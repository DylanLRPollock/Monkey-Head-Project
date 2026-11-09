"""Coverage for the media manager's module-level public operations."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.media import media_manager


class FakeManager:
    def __init__(self):
        self.commands = []
        self.transforms = []
        self.ok = True
        self.stderr = "simulated media failure"
        self.stdout = ""
        self.prepared = None
        self.silence_result = None

    def require_ffmpeg(self):
        return Path("/usr/bin/ffmpeg")

    @staticmethod
    def _overwrite_arg(overwrite):
        return "-y" if overwrite else "-n"

    def run(self, command, *, timeout_seconds=None):
        self.commands.append((command, timeout_seconds))
        return SimpleNamespace(
            ok=self.ok,
            command=command,
            returncode=0 if self.ok else 1,
            stdout=self.stdout,
            stderr=self.stderr,
        )

    def transform_audio(self, source, target, *, options, overwrite):
        self.transforms.append((source, target, options, overwrite))
        return SimpleNamespace(
            ok=self.ok,
            stdout=self.stdout,
            stderr=self.stderr,
        )

    def detect_silence(self, source, *, noise_db, duration_seconds):
        self.silence_result = (source, noise_db, duration_seconds)
        return SimpleNamespace(
            ok=self.ok,
            stdout=self.stdout,
            stderr=self.stderr,
        )

    def prepare_for_transcription(self, **kwargs):
        self.prepared = kwargs
        return SimpleNamespace(ok=self.ok, **kwargs)


@pytest.fixture
def manager(monkeypatch):
    fake = FakeManager()
    monkeypatch.setattr(media_manager, "get_default_manager", lambda: fake)
    return fake


@pytest.fixture
def source_file(tmp_path):
    source = tmp_path / "source.wav"
    source.write_bytes(b"fixture")
    return source


def test_convert_audio_builds_argv_and_rejects_failed_ffmpeg(
    manager, source_file, tmp_path, monkeypatch
):
    target = tmp_path / "nested" / "converted.mp3"

    result = media_manager.convert_audio(
        source_file, target, bitrate="192k", overwrite=False
    )

    command, timeout = manager.commands[-1]
    assert result == target.resolve()
    assert command[:4] == [
        "/usr/bin/ffmpeg",
        "-n",
        "-i",
        str(source_file.resolve()),
    ]
    assert command[-3:] == ["-b:a", "192k", str(target.resolve())]
    assert timeout is None

    manager.ok = False
    with pytest.raises(RuntimeError, match="simulated media failure"):
        media_manager.convert_audio(source_file, tmp_path / "failed.mp3")


def test_audio_transform_wrappers_forward_options_and_surface_failures(
    manager, source_file, tmp_path
):
    resampled = media_manager.resample_audio(
        source_file, tmp_path / "resampled.wav", channels=1, sample_rate=16000
    )
    normalized = media_manager.normalize_audio(source_file, tmp_path / "normalized.wav")

    assert resampled == (tmp_path / "resampled.wav").resolve()
    assert normalized == (tmp_path / "normalized.wav").resolve()
    assert manager.transforms[0][2].channels == 1
    assert manager.transforms[0][2].sample_rate == 16000
    assert manager.transforms[1][2].normalize is True
    assert all(item[3] is True for item in manager.transforms)

    manager.ok = False
    with pytest.raises(RuntimeError, match="simulated media failure"):
        media_manager.resample_audio(source_file, tmp_path / "bad.wav")


def test_media_wrapper_commands_cover_filters_codecs_and_frame_patterns(
    manager, source_file, tmp_path
):
    removed = media_manager.remove_silence(
        source_file, tmp_path / "trimmed.wav", threshold="-35dB"
    )
    extracted = media_manager.extract_audio(
        source_file,
        tmp_path / "audio.aac",
        codec="aac",
        sample_rate=22050,
        channels=2,
    )
    transcoded = media_manager.transcode_video(
        source_file,
        tmp_path / "video.mp4",
        video_codec="libx265",
        audio_codec="aac",
    )
    frames = media_manager.extract_frames(
        source_file, tmp_path / "frames" / "frame-%03d.png", fps=2.5
    )

    assert removed == (tmp_path / "trimmed.wav").resolve()
    assert extracted == (tmp_path / "audio.aac").resolve()
    assert transcoded == (tmp_path / "video.mp4").resolve()
    assert frames == (tmp_path / "frames" / "frame-%03d.png").resolve()
    silence_filter = manager.commands[0][0][
        manager.commands[0][0].index("-af") + 1
    ]
    assert "silenceremove=" in silence_filter
    assert manager.commands[1][0][-7:] == [
        "-acodec",
        "aac",
        "-ac",
        "2",
        "-ar",
        "22050",
        str((tmp_path / "audio.aac").resolve()),
    ]
    assert manager.commands[2][0][-5:] == [
        "-c:v",
        "libx265",
        "-c:a",
        "aac",
        str((tmp_path / "video.mp4").resolve()),
    ]
    assert manager.commands[3][0][-2:] == [
        "fps=2.5",
        str((tmp_path / "frames" / "frame-%03d.png").resolve()),
    ]
    assert (tmp_path / "frames").is_dir()


def test_module_wrappers_validate_sources_outputs_and_ffmpeg_before_execution(
    manager, source_file, tmp_path
):
    with pytest.raises(FileNotFoundError):
        media_manager.convert_audio(tmp_path / "missing.wav", tmp_path / "out.wav")
    assert manager.commands == []

    existing = tmp_path / "existing.wav"
    existing.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        media_manager.convert_audio(
            source_file, existing, overwrite=False
        )
    assert existing.read_bytes() == b"keep"
    assert manager.commands == []

    def missing_ffmpeg():
        raise RuntimeError("FFmpeg is not available")

    monkeypatch.setattr(manager, "require_ffmpeg", missing_ffmpeg)
    with pytest.raises(RuntimeError, match="FFmpeg is not available"):
        media_manager.convert_audio(source_file, tmp_path / "unavailable.wav")
    assert manager.commands == []


def test_detect_silence_parses_matched_and_unmatched_segments(manager, source_file):
    manager.stderr = (
        "silence_start: 0.5\\n"
        "silence_end: 1.5 | silence_duration: 1.0\\n"
        "silence_end: 3.0 | silence_duration: 0.25"
    )

    segments = media_manager.detect_silence(
        source_file, noise_db=-35, duration_seconds=0.4
    )

    assert segments == [
        {"start": 0.5, "end": 1.5, "duration": 1.0},
        {"start": 2.75, "end": 3.0, "duration": 0.25},
    ]
    assert manager.silence_result == (source_file, -35, 0.4)

    manager.ok = False
    with pytest.raises(RuntimeError, match="simulated media failure"):
        media_manager.detect_silence(source_file)


@pytest.mark.parametrize(
    ("function", "expected"),
    [
        (media_manager._optional_float, 1.25),
        (media_manager._optional_int, 3),
    ],
)
def test_optional_numeric_coercers_accept_valid_values(function, expected):
    value = 1.25 if function is media_manager._optional_float else "3"
    assert function(value) == expected
    assert function(None) is None
    assert function("not-a-number") is None


def test_prepare_audio_for_transcription_delegates_to_default_manager(
    manager, source_file, tmp_path
):
    target = tmp_path / "prepared.wav"

    result = media_manager.prepare_audio_for_transcription(
        source_file, target, overwrite=True
    )

    assert result.ok
    assert manager.prepared == {
        "input_path": source_file,
        "output_path": target,
        "overwrite": True,
    }
