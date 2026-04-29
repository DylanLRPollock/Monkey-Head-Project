"""Tests for the :mod:`hueyos` compatibility namespace."""

from __future__ import annotations

import importlib
from pathlib import Path

import hueyos


def test_hueyos_package_path_exposes_current_and_legacy_roots():
    paths = [Path(path) for path in hueyos.__path__]

    assert any(path.name == "hueyos" for path in paths)
    assert any(path.name == "huey" for path in paths)
    assert any(path.name == "PY" and path.parent.name == "memory" for path in paths)


def test_hueyos_imports_modern_and_legacy_submodules():
    cases = {
        "hueyos.core.task_scheduler": "TaskScheduler",
        "hueyos.license_cli": "show_license_cli",
        "hueyos.logging_setup": "configure_logging",
        "hueyos.services.environment_setup": "clone_repository",
        "hueyos.scripts.preload_data": "preload_all",
        "hueyos.utils.gpu": "detect_accelerators",
        "hueyos.utils.persistence": "TelemetryStore",
        "hueyos.utils.sorting": "natural_sort",
    }

    for module_name, attribute in cases.items():
        module = importlib.import_module(module_name)
        assert hasattr(module, attribute), module_name


def test_hueyos_local_modules_override_legacy_bridges():
    install_gui = importlib.import_module("hueyos.install_gui")
    license_gui = importlib.import_module("hueyos.license_gui")

    assert install_gui.validate_license_acceptance.__module__ == "hueyos.install_gui"
    assert license_gui.accept_license.__module__ == "hueyos.license_gui"
