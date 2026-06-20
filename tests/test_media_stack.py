"""Tests for the FFmpeg media wrapper layer."""

from __future__ import annotations

from unittest.mock import patch

import huey.media.media_manager as media_manager
from huey.media.ffmpeg_validator import validate_media_environment
from huey.media.media_manager import FFmpegCommandResult, FFmpegMediaManager


def test_validate_media_environment_reports_missing_tools():
    with patch("huey.media.ffmpeg_validator.shutil.which", return_value=None):
        payload = validate_media_environment()

    assert payload["ready"] is False
    assert payload["ffmpeg"] is False
    assert payload["ffprobe"] is False


def test_probe_media_parses_ffprobe_json(tmp_path, monkeypatch):
    media_file = tmp_path / "fixture.wav"
    media_file.write_bytes(b"data")
    manager = FFmpegMediaManager(ffprobe_path="ffprobe")

    def fake_run(args: list[str]) -> FFmpegCommandResult:
        return FFmpegCommandResult(
            command=args,
            returncode=0,
            stdout=(
                '{"format": {'
                '"duration": "1.23", '
                '"bit_rate": "64000", '
                '"size": "4", '
                '"format_name": "wav"}, '
                '"streams": []}'
            ),
            stderr="",
        )

    monkeypatch.setattr(manager, "run", fake_run)
    monkeypatch.setattr(media_manager, "get_default_manager", lambda: manager)

    payload = media_manager.probe_media(media_file)

    assert payload.duration_seconds == 1.23
    assert payload.bit_rate == 64000
    assert payload.size_bytes == 4
    assert payload.format_name == "wav"
