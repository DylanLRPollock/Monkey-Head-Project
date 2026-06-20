"""Compatibility smoke tests for legacy ``huey`` import paths."""

from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path


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


def test_import_huey_connector_canonical_package():
    module = importlib.import_module("huey.connectors.pyhuey")

    module_file = Path(module.__file__).as_posix()
    assert module_file.endswith("/huey/connectors/pyhuey/__init__.py")
    assert getattr(module, "__version__", None)


def test_import_huey_connector_legacy_package_shim_points_to_canonical_tree():
    legacy = importlib.import_module("huey.pygpt_net")
    canonical = importlib.import_module("huey.connectors.pyhuey")

    legacy_paths = [Path(path).resolve() for path in legacy.__path__]

    assert Path(canonical.__file__).resolve().parent in legacy_paths


def test_legacy_connector_submodule_spec_resolves_to_canonical_tree():
    spec = importlib.util.find_spec("huey.pygpt_net.controller.config.placeholder")

    assert spec is not None
    assert spec.origin is not None
    assert (
        Path(spec.origin)
        .as_posix()
        .endswith("/huey/connectors/pyhuey/controller/config/placeholder.py")
    )
