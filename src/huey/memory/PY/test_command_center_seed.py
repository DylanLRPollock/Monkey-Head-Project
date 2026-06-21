from __future__ import annotations

from pathlib import Path

from huey.apps.command_center import seed
from huey.media.ffmpeg_validator import FFmpegValidationReport


def test_build_seed_data(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        seed,
        "check_ffmpeg",
        lambda: FFmpegValidationReport(False, None, None, errors=["missing"]),
    )
    data = seed.build_seed_data(tmp_path)
    assert data["schema"] == "huey.command_center.seed"
    assert "live microphone capture" in data["deferred_by_default"]

