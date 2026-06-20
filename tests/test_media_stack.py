"""Tests for the FFmpeg media wrapper layer."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from huey.media.ffmpeg_validator import validate_media_environment
from huey.media.media_manager import probe_media


def test_validate_media_environment_reports_missing_tools():
    with patch("huey.media.ffmpeg_validator.shutil.which", return_value=None):
        payload = validate_media_environment()

    assert payload["ready"] is False
    assert payload["ffmpeg"] is False
    assert payload["ffprobe"] is False


def test_probe_media_parses_ffprobe_json(tmp_path):
    media_file = tmp_path / "fixture.wav"
    media_file.write_bytes(b"data")

    with patch(
        "huey.media.media_manager._run_ffprobe",
        return_value=SimpleNamespace(
            stdout='{"format": {"duration": "1.23"}, "streams": []}'
        ),
    ):
        payload = probe_media(media_file)

    assert payload["format"]["duration"] == "1.23"
