from __future__ import annotations

import json
from pathlib import Path

import pytest

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


def test_build_seed_data_reports_existing_proof_paths(
    monkeypatch, tmp_path: Path
) -> None:
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr(
        seed,
        "check_ffmpeg",
        lambda: FFmpegValidationReport(True, "ffmpeg", "ffprobe"),
    )

    data = seed.build_seed_data(tmp_path)

    assert data["paths"] == {
        "src/huey/media": False,
        "src/huey/v1": False,
        "tests": True,
    }
    assert data["ffmpeg"]["available"] is True


def test_write_seed_data_rejects_existing_path_unless_overwrite_enabled(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        seed,
        "check_ffmpeg",
        lambda: FFmpegValidationReport(False, None, None, errors=["missing"]),
    )
    output = tmp_path / "nested" / "seed.json"
    output.parent.mkdir()
    output.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError, match="overwrite is false"):
        seed.write_seed_data(tmp_path, output)

    result = seed.write_seed_data(tmp_path, output, overwrite=True)
    assert json.loads(output.read_text(encoding="utf-8")) == result


def test_seed_cli_prints_json_and_written_path(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.setattr(
        seed,
        "check_ffmpeg",
        lambda: FFmpegValidationReport(False, None, None, errors=["missing"]),
    )

    assert seed.main(["--project-root", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["schema"] == "huey.command_center.seed"

    output = tmp_path / "out" / "seed.json"
    assert seed.main(["--project-root", str(tmp_path), "--output", str(output)]) == 0
    assert capsys.readouterr().out.strip() == f"wrote: {output}"

    assert (
        seed.main(
            [
                "--project-root",
                str(tmp_path),
                "--output",
                str(output),
                "--overwrite",
                "--json",
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["schema"] == "huey.command_center.seed"
