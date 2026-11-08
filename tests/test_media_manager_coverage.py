"""Offline regression coverage for FFmpeg manager error and compatibility paths."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from huey.media.media_manager import FFmpegManager, FFmpegMediaManager


def _completed(command: list[str], stdout: str = "ok"):
    return subprocess.CompletedProcess(command, 0, stdout, "")


def test_media_manager_run_maps_timeout_missing_binary_and_os_error(monkeypatch):
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")

    def timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("ffmpeg", 1, output=b"partial")

    monkeypatch.setattr("huey.media.media_manager.subprocess.run", timeout)
    timed_out = manager.run(["ffmpeg", "-version"], timeout_seconds=1)
    assert timed_out.returncode == 124
    assert timed_out.stdout == "partial"
    assert "timed out after 1 seconds" in timed_out.stderr

    monkeypatch.setattr(
        "huey.media.media_manager.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("missing")),
    )
    assert manager.run(["missing"]).returncode == 127

    monkeypatch.setattr(
        "huey.media.media_manager.subprocess.run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("denied")),
    )
    assert manager.run(["ffmpeg"]).stderr == "denied"


def test_probe_parses_valid_metadata_and_rejects_invalid_json(tmp_path, monkeypatch):
    source = tmp_path / "audio.wav"
    source.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffprobe_path="ffprobe")
    monkeypatch.setattr(
        manager,
        "run",
        lambda command: SimpleNamespace(
            ok=True,
            stdout='{"format":{"format_name":"wav","duration":"2.5",'
            '"bit_rate":"bad","size":"12"},"streams":[{"codec":"pcm"}]}',
            stderr="",
        ),
    )

    result = manager.probe(source)
    assert result.format_name == "wav"
    assert result.duration_seconds == 2.5
    assert result.bit_rate is None
    assert result.size_bytes == 12
    assert result.streams == [{"codec": "pcm"}]

    monkeypatch.setattr(
        manager,
        "run",
        lambda _command: SimpleNamespace(ok=True, stdout="not json", stderr=""),
    )
    with pytest.raises(RuntimeError, match="invalid JSON"):
        manager.probe(source)


def test_legacy_manager_validates_probe_and_safe_conversion_commands(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.wav"
    source.write_bytes(b"fixture")
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        output = '{"format":{"format_name":"wav","duration":"1.5",'
        output += '"bit_rate":"64000"},"streams":[]}'
        return _completed(command, output if "ffprobe" in command[0] else "done")

    manager = FFmpegManager(runner=runner)
    monkeypatch.setattr(
        "huey.media.media_manager.shutil.which", lambda _name: "/bin/tool"
    )
    manager.validate_binaries()
    probe = manager.probe(source)
    assert probe.duration_seconds == 1.5
    assert probe.bit_rate == 64000

    output = tmp_path / "converted.mp3"
    converted = manager.convert_audio(
        source, output, sample_rate=16000, channels=1, bitrate="128k"
    )
    assert converted.output_path == output.resolve()
    assert calls[-1][0][calls[-1][0].index("-ar") :][:2] == ["-ar", "16000"]
    assert "shell" not in calls[-1][1]


@pytest.mark.parametrize(
    "operation",
    [
        "normalize_audio",
        "prepare_transcription_wav",
        "extract_audio",
        "thumbnail",
        "waveform",
        "spectrogram",
        "split_audio_chunks",
    ],
)
def test_legacy_manager_transforms_use_argument_lists(operation, tmp_path):
    source = tmp_path / "video.mp4"
    source.write_bytes(b"fixture")
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        return _completed(command)

    manager = FFmpegManager(runner=runner)
    output = tmp_path / f"{operation}.out"
    if operation == "split_audio_chunks":
        output = tmp_path / "parts" / "clip-%03d.wav"
        manager.split_audio_chunks(source, output, seconds=10)
    else:
        getattr(manager, operation)(source, output)

    command, kwargs = calls[-1]
    assert command[0] == "ffmpeg"
    assert isinstance(command, list)
    assert kwargs["check"] is False
    assert kwargs["text"] is True


def test_legacy_manager_rejects_invalid_inputs_outputs_and_commands(tmp_path):
    source = tmp_path / "source.wav"
    source.write_bytes(b"fixture")
    manager = FFmpegManager(runner=lambda command, **_kwargs: _completed(command))

    with pytest.raises(ValueError, match="must not be empty"):
        manager.run([])
    with pytest.raises(FileNotFoundError, match="Media file not found"):
        manager.probe(tmp_path / "missing.wav")
    with pytest.raises(ValueError, match="frame_number"):
        manager.extract_frame(source, tmp_path / "frame.png", frame_number=-1)
    with pytest.raises(ValueError, match="seconds"):
        manager.split_audio_chunks(source, tmp_path / "chunk-%d.wav", seconds=0)

    existing = tmp_path / "existing.wav"
    existing.write_bytes(b"existing")
    with pytest.raises(FileExistsError):
        manager.convert_audio(source, existing)


def test_legacy_manager_reports_failed_subprocess(tmp_path):
    source = tmp_path / "source.wav"
    source.write_bytes(b"fixture")
    manager = FFmpegManager(
        runner=lambda command, **_kwargs: subprocess.CompletedProcess(
            command, 1, "", "conversion failed"
        )
    )

    with pytest.raises(RuntimeError, match="conversion failed"):
        manager.normalize_audio(source, tmp_path / "output.wav")
