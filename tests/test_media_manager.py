from pathlib import Path

import pytest

from huey.media import (
    AudioTransformOptions,
    FFmpegCommandResult,
    FFmpegMediaManager,
    check_ffmpeg_available,
    media_manager,
)


def test_import_huey_media_succeeds() -> None:
    import huey.media as imported_media

    assert imported_media.FFmpegMediaManager is FFmpegMediaManager


def test_constructor_does_not_fail_if_ffmpeg_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(media_manager.shutil, "which", lambda _name: None)

    manager = FFmpegMediaManager()

    assert manager.ffmpeg_path is None
    assert manager.ffprobe_path is None


def test_build_audio_transform_command_expected_args(tmp_path: Path) -> None:
    input_path = tmp_path / "input.mp3"
    output_path = tmp_path / "output.wav"
    input_path.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")

    command = manager.build_audio_transform_command(
        input_path=input_path,
        output_path=output_path,
        options=AudioTransformOptions(
            sample_rate=16000,
            channels=1,
            normalize=True,
            loudnorm=True,
            remove_silence=True,
        ),
    )

    assert "-ac" in command
    assert command[command.index("-ac") + 1] == "1"
    assert "-ar" in command
    assert command[command.index("-ar") + 1] == "16000"
    assert "-af" in command
    audio_filter = command[command.index("-af") + 1]
    assert "loudnorm=I=-16:TP=-1.5:LRA=11" in audio_filter
    assert "silenceremove=" in audio_filter
    assert "dynaudnorm" not in audio_filter
    assert "-n" in command
    assert str(output_path) == command[-1]


def test_transform_audio_refuses_to_overwrite_existing_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.mp3"
    output_path = tmp_path / "output.wav"
    input_path.write_bytes(b"fixture")
    output_path.write_bytes(b"existing")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")

    def fail_run(_args: list[str]) -> FFmpegCommandResult:
        raise AssertionError("run should not be called")

    monkeypatch.setattr(manager, "run", fail_run)

    with pytest.raises(FileExistsError):
        manager.transform_audio(input_path, output_path)


def test_probe_raises_file_not_found_for_missing_input(tmp_path: Path) -> None:
    manager = FFmpegMediaManager(ffprobe_path="ffprobe")

    with pytest.raises(FileNotFoundError):
        manager.probe(tmp_path / "missing.mp3")


def test_prepare_for_transcription_uses_expected_transform(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.mp3"
    output_path = tmp_path / "prepared.wav"
    input_path.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")
    captured: dict[str, list[str]] = {}

    def fake_run(args: list[str]) -> FFmpegCommandResult:
        captured["command"] = args
        return FFmpegCommandResult(command=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(manager, "run", fake_run)

    result = manager.prepare_for_transcription(input_path, output_path)

    assert result.ok
    command = captured["command"]
    assert command[command.index("-ac") + 1] == "1"
    assert command[command.index("-ar") + 1] == "16000"
    audio_filter = command[command.index("-af") + 1]
    assert "loudnorm" in audio_filter
    assert "silenceremove" in audio_filter


def test_generate_waveform_image_builds_showwavespic_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.wav"
    output_path = tmp_path / "waveform.png"
    input_path.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")
    captured: dict[str, list[str]] = {}

    def fake_run(args: list[str]) -> FFmpegCommandResult:
        captured["command"] = args
        return FFmpegCommandResult(command=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(manager, "run", fake_run)

    manager.generate_waveform_image(input_path, output_path)

    assert any("showwavespic=s=1280x320" in part for part in captured["command"])


def test_generate_spectrogram_image_builds_showspectrumpic_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.wav"
    output_path = tmp_path / "spectrogram.png"
    input_path.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")
    captured: dict[str, list[str]] = {}

    def fake_run(args: list[str]) -> FFmpegCommandResult:
        captured["command"] = args
        return FFmpegCommandResult(command=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(manager, "run", fake_run)

    manager.generate_spectrogram_image(input_path, output_path)

    assert any("showspectrumpic=s=1280x720" in part for part in captured["command"])


def test_extract_thumbnail_uses_single_frame_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.mp4"
    output_path = tmp_path / "thumbnail.png"
    input_path.write_bytes(b"fixture")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")
    captured: dict[str, list[str]] = {}

    def fake_run(args: list[str]) -> FFmpegCommandResult:
        captured["command"] = args
        return FFmpegCommandResult(command=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(manager, "run", fake_run)

    manager.extract_thumbnail(input_path, output_path)

    command = captured["command"]
    assert "-frames:v" in command
    assert command[command.index("-frames:v") + 1] == "1"


def test_check_ffmpeg_available_returns_bool() -> None:
    assert isinstance(check_ffmpeg_available(), bool)


def test_extract_frame_builds_select_command_and_returns_failure_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    input_path = tmp_path / "input.mp4"
    output_path = tmp_path / "frame.png"
    failed_output = tmp_path / "failed.png"
    input_path.write_bytes(b"fixture")
    responses = [
        FFmpegCommandResult(
            command=[],
            returncode=0,
            stdout="",
            stderr="",
        ),
        FFmpegCommandResult(
            command=[],
            returncode=1,
            stdout="",
            stderr="simulated encoder failure",
        ),
    ]
    captured: list[list[str]] = []
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")

    def fake_run(command: list[str]) -> FFmpegCommandResult:
        captured.append(command)
        return FFmpegCommandResult(
            command=command,
            returncode=responses[len(captured) - 1].returncode,
            stdout="",
            stderr=responses[len(captured) - 1].stderr,
        )

    monkeypatch.setattr(manager, "run", fake_run)
    result = manager.extract_frame(
        input_path, output_path, frame_number=7, overwrite=True
    )
    failed = manager.extract_frame(input_path, failed_output, frame_number=2)

    assert result.ok
    assert result.output_path == output_path
    assert result.command[2] == "-y"
    assert result.command[result.command.index("-vf") + 1] == "select=eq(n\\,7)"
    assert result.command[result.command.index("-frames:v") + 1] == "1"
    assert failed.ok is False
    assert failed.stderr == "simulated encoder failure"
    assert len(captured) == 2


def test_extract_frame_validates_number_input_and_output_before_running(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg")

    def fail_run(_command: list[str]) -> FFmpegCommandResult:
        pytest.fail("FFmpeg must not run for invalid frame paths")

    monkeypatch.setattr(manager, "run", fail_run)
    with pytest.raises(ValueError, match="frame_number must be zero or greater"):
        manager.extract_frame(
            tmp_path / "missing.mp4",
            tmp_path / "frame.png",
            frame_number=-1,
        )
    with pytest.raises(FileNotFoundError):
        manager.extract_frame(
            tmp_path / "missing.mp4",
            tmp_path / "frame.png",
            frame_number=0,
        )

    source = tmp_path / "source.mp4"
    source.write_bytes(b"fixture")
    output = tmp_path / "frame.png"
    output.write_bytes(b"keep")
    with pytest.raises(FileExistsError):
        manager.extract_frame(source, output, frame_number=0)
    assert output.read_bytes() == b"keep"
