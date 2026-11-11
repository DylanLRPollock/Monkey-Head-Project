"""Test deterministic Command Center seed export and CLI behavior."""

from __future__ import annotations

import importlib
import json
import sys


def test_build_and_write_seed_payload(tmp_path, monkeypatch):
    module = importlib.import_module("huey.memory.PY.export_command_center_seed")
    payload = module.build_seed_payload()
    assert set(payload) == {
        "config",
        "theme",
        "theme_css",
        "safety",
        "repositories",
        "phases",
        "validation_commands",
        "operator_panel",
        "v1_runs",
    }
    assert payload["repositories"]
    assert payload["phases"]

    output = tmp_path / "nested" / "seed.json"
    assert module.write_seed(output) == output
    assert json.loads(output.read_text(encoding="utf-8")) == module.build_seed_payload()

    cli_output = tmp_path / "cli.json"
    monkeypatch.setattr(sys, "argv", ["export_seed", "--output", str(cli_output)])
    assert module.main() == 0
    assert (
        json.loads(cli_output.read_text(encoding="utf-8"))
        == module.build_seed_payload()
    )


def test_export_module_bootstraps_source_path_when_needed(monkeypatch):
    module = importlib.import_module("huey.memory.PY.export_command_center_seed")
    monkeypatch.setattr(
        sys,
        "path",
        [entry for entry in sys.path if entry != str(module.SRC)],
    )
    importlib.reload(module)
    assert sys.path[0] == str(module.SRC)
    monkeypatch.setattr(sys, "path", [str(module.SRC), *sys.path])
    importlib.reload(module)
