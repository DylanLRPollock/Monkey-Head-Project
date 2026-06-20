"""Compatibility smoke tests for legacy ``huey`` import paths."""

from __future__ import annotations

import importlib
import importlib.metadata
import json


def test_import_huey_api_module():
    module = importlib.import_module("huey.api")
    assert module.app is not None
    assert callable(module.main)


def test_import_huey_run_module():
    module = importlib.import_module("huey.run")
    assert callable(module.main)
    assert callable(module.run_module)


def test_import_huey_cli_module():
    module = importlib.import_module("huey.cli")
    assert callable(module.main)


def test_console_script_entrypoints_resolve():
    entry_points = importlib.metadata.entry_points(group="console_scripts")
    mapping = {entry.name: entry for entry in entry_points}

    assert "huey" in mapping
    assert "huey-api" in mapping

    assert callable(mapping["huey"].load())
    assert callable(mapping["huey-api"].load())


def test_huey_console_script_executes_system_check(monkeypatch, capsys):
    def fake_system_check():
        return {"os_supported": True, "python_supported": True}

    monkeypatch.setattr("huey.os.system_checks.system_check", fake_system_check)
    entry_points = importlib.metadata.entry_points(group="console_scripts")
    mapping = {entry.name: entry for entry in entry_points}

    runner = mapping["huey"].load()
    exit_code = runner(["system-check", "--json"])
    assert exit_code == 0
    assert json.loads(capsys.readouterr().out) == {
        "os_supported": True,
        "python_supported": True,
    }


def test_import_api_through_legacy_and_new_paths():
    legacy = importlib.import_module("huey.api")
    maintained = importlib.import_module("huey.os.api.app")

    assert legacy.app is maintained.app
    assert callable(legacy.main)
    assert callable(maintained.main)
