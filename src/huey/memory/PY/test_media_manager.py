from __future__ import annotations

from pathlib import Path

import pytest

from huey.media.media_manager import CommandResult, FFmpegMediaManager


def test_missing_source_fails_before_ffmpeg(tmp_path: Path) -> None:
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg", ffprobe_path="ffprobe")
    with pytest.raises(FileNotFoundError):
        manager.convert_audio(tmp_path / "missing.mp3", tmp_path / "out.wav")


def test_existing_output_requires_overwrite(tmp_path: Path) -> None:
    source = tmp_path / "in.mp3"
    output = tmp_path / "out.wav"
    source.write_bytes(b"fake")
    output.write_bytes(b"existing")
    manager = FFmpegMediaManager(ffmpeg_path="ffmpeg", ffprobe_path="ffprobe")
    with pytest.raises(FileExistsError):
        manager.convert_audio(source, output)


def test_command_result_is_json_safe(tmp_path: Path) -> None:
    result = CommandResult(0, "", "", ["ffmpeg"], tmp_path / "out.wav")
    assert result.to_json_dict()["output_path"].endswith("out.wav")
