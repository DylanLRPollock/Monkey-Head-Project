"""Deterministic success and failure coverage for public media operations."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from huey.media.media_manager import (
    AudioTransformOptions,
    FFmpegMediaManager,
)


def _ok(command: list[str], stdout: str = "") -> SimpleNamespace:
    return SimpleNamespace(returncode=0, stdout=stdout, stderr="")


def test_media_manager_run_uses_argv_and_maps_success(monkeypatch):
    captured = {}
    manager = FFmpegMediaManager(timeout_seconds=17)

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return _ok(command, "ffmpeg version fixture\n")

    monkeypatch.setattr("huey.media.media_manager.subprocess.run", fake_run)
    result = manager.run(["ffmpeg", "-version"])

    assert result.ok
    assert result.stdout == "ffmpeg version fixture\n"
    assert captured["command"] == ["ffmpeg", "-version"]
    assert captured["kwargs"]["shell"] is False
    assert captured["kwargs"]["timeout"] == 17
    assert captured["kwargs"]["capture_output"] is True


def test_media_manager_version_handles_success_failure_and_missing_binary(
    monkeypatch,
):
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg", ffprobe_path="ffprobe")
    monkeypatch.setattr(
        manager,
        "run",
        lambda command: SimpleNamespace(
            ok=command[0] == "ffmpeg",
            stdout="ffmpeg version 7.0\nextra" if command[0] == "ffmpeg" else "",
            stderr="unavailable",
        ),
    )

    assert manager.version() == {
        "ffmpeg": "ffmpeg version 7.0",
        "ffprobe": None,
    }
    assert FFmpegMediaManager().version() == {"ffmpeg": None, "ffprobe": None}


def test_probe_failure_and_non_mapping_metadata(tmp_path, monkeypatch):
    source = tmp_path / "clip.wav"
    source.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffprobe_path="ffprobe")

    monkeypatch.setattr(
        manager,
        "run",
        lambda _command: SimpleNamespace(ok=False, stdout="", stderr="probe failed"),
    )
    with pytest.raises(RuntimeError, match="probe failed"):
        manager.probe(source)

    monkeypatch.setattr(
        manager,
        "run",
        lambda _command: SimpleNamespace(
            ok=True, stdout='{"format": [], "streams": {}}', stderr=""
        ),
    )
    result = manager.probe(source)
    assert result.format_name is None
    assert result.streams == []
    assert result.raw == {"format": [], "streams": {}}


def test_build_audio_command_covers_format_seek_and_duration(tmp_path):
    source = tmp_path / "input.wav"
    source.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")
    command = manager.build_audio_transform_command(
        source,
        tmp_path / "output.ogg",
        AudioTransformOptions(
            start_seconds=1.25,
            duration_seconds=4,
            channels=2,
            sample_rate=44100,
            normalize=True,
            output_format="ogg",
        ),
        overwrite=True,
    )

    assert command[1] == "-y"
    assert command[command.index("-ss") + 1] == "1.25"
    assert command[command.index("-t") + 1] == "4"
    assert command[command.index("-ac") + 1] == "2"
    assert command[command.index("-ar") + 1] == "44100"
    assert command[command.index("-af") + 1] == "dynaudnorm"
    assert command[command.index("-f") + 1] == "ogg"


@pytest.mark.parametrize(
    ("method", "args", "expected"),
    [
        ("convert_audio", (16000, 1), ("-ar", "16000")),
        ("extract_audio", (22050, 2), ("-ac", "2")),
        ("prepare_for_transcription", (), ("-af", "loudnorm")),
        ("generate_waveform_image", (), ("showwavespic", "-filter_complex")),
        ("generate_spectrogram_image", (), ("showspectrumpic", "-filter_complex")),
        ("extract_thumbnail", (), ("-frames:v", "1")),
    ],
)
def test_media_transform_helpers_build_expected_commands(
    method, args, expected, tmp_path, monkeypatch
):
    source = tmp_path / "source.wav"
    source.write_bytes(b"fixture")
    output = tmp_path / "out.bin"
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")
    seen = []

    def fake_run(command):
        seen.append(command)
        return SimpleNamespace(command=command, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(manager, "run", fake_run)
    operation = getattr(manager, method)
    if method in {"convert_audio", "extract_audio"}:
        operation(source, output, *args)
    else:
        operation(source, output)

    command = seen[0]
    assert expected[0] in command
    assert expected[1] in command[command.index(expected[0]) + 1]


def test_extract_frames_detect_silence_and_split_chunks(tmp_path, monkeypatch):
    source = tmp_path / "video.mp4"
    source.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")
    calls = []
    monkeypatch.setattr(
        manager,
        "run",
        lambda command: calls.append(command)
        or SimpleNamespace(command=command, returncode=0, stdout="", stderr=""),
    )

    manager.extract_frames(source, tmp_path / "frames", fps=2.5)
    manager.detect_silence(source, noise_db=-35, duration_seconds=0.4)
    manager.split_audio_chunks(source, tmp_path / "chunks", chunk_seconds=30)

    assert "fps=2.5" in calls[0]
    assert "silencedetect=noise=-35dB:d=0.4" in calls[1]
    assert calls[1][-1] == "-"
    assert calls[2][calls[2].index("-segment_time") + 1] == "30"
    assert (tmp_path / "frames").is_dir()
    assert (tmp_path / "chunks").is_dir()


def test_output_and_binary_validation_stays_before_execution(tmp_path):
    source = tmp_path / "source.wav"
    source.write_bytes(b"fixture")
    manager = FFmpegMediaManager()
    with pytest.raises(RuntimeError, match="FFmpeg is not available"):
        manager.build_audio_transform_command(
            source, tmp_path / "out.wav", AudioTransformOptions()
        )
    with pytest.raises(FileNotFoundError):
        manager.build_audio_transform_command(
            tmp_path / "missing.wav", tmp_path / "out.wav", AudioTransformOptions()
        )

    existing = tmp_path / "existing.wav"
    existing.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        FFmpegMediaManager(ffmpeg_path="ffmpeg").build_audio_transform_command(
            source, existing, AudioTransformOptions()
        )
