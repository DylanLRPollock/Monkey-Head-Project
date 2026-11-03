"""Operator-facing V1 integrity CLI tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from huey.v1.fixture_registry import register_fixture


def test_v1_fixture_cli_passes_and_detects_tampering(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "v1_fixture_check.py"
    source = tmp_path / "fixture.txt"
    source.write_text("original", encoding="utf-8")
    registry = tmp_path / "registry.json"
    register_fixture(source, registry_path=registry)
    args = [sys.executable, str(script), "--registry", str(registry), "--json"]
    good = subprocess.run(args, capture_output=True, text=True, check=True)
    assert json.loads(good.stdout)["passed"] == 1
    source.write_text("modified", encoding="utf-8")
    bad = subprocess.run(args, capture_output=True, text=True, check=False)
    assert bad.returncode == 1
    assert json.loads(bad.stdout)["failed"] == 1


def test_v1_fixture_cli_unknown_id_fails_explicitly(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "v1_fixture_check.py"
    registry = tmp_path / "registry.json"
    registry.write_text("{}", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(script), "--registry", str(registry), "--id", "missing"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Unknown fixture ID" in result.stderr
