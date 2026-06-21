from __future__ import annotations

from huey.media import ffmpeg_validator


def test_check_ffmpeg_reports_missing_binaries(monkeypatch) -> None:
    monkeypatch.setattr(ffmpeg_validator.shutil, "which", lambda name: None)
    report = ffmpeg_validator.check_ffmpeg()
    assert report.available is False
    assert "ffmpeg not found on PATH" in report.errors
    assert report.to_json_dict()["available"] is False


def test_validator_main_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(ffmpeg_validator.shutil, "which", lambda name: None)
    exit_code = ffmpeg_validator.main(["--json"])
    assert exit_code == 0
    assert '"available": false' in capsys.readouterr().out

