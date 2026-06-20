# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: layout canonicalization tests

from __future__ import annotations

import importlib
from pathlib import Path


def test_huey_os_is_canonical_package():
    module = importlib.import_module("huey.os")

    module_file = Path(module.__file__).as_posix()
    assert "/huey/os/" in module_file or module_file.endswith("/huey/os/__init__.py")


def test_hueyos_compatibility_shim_includes_huey_os_path():
    legacy = importlib.import_module("hueyos")

    paths = [Path(path).as_posix() for path in legacy.__path__]
    assert any(path.endswith("/huey/os") for path in paths)


def test_hueyos_api_compatibility_resolves_to_huey_os_api():
    legacy_api = importlib.import_module("hueyos.api")
    canonical_api = importlib.import_module("huey.os.api")

    assert Path(legacy_api.__file__).resolve() == Path(canonical_api.__file__).resolve()
