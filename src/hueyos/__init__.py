"""Compatibility namespace exposing :mod:`huey.os` as :mod:`hueyos`.

Canonical HueyOS implementation now lives under ``huey.os``. This shim keeps
legacy ``hueyos`` imports working during the migration window.

New code should import from ``huey.os`` directly.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

_impl = importlib.import_module("huey.os")
_PACKAGE_DIR = Path(__file__).resolve().parent

_path_entries = [_PACKAGE_DIR]
_path_entries.extend(Path(entry) for entry in getattr(_impl, "__path__", ()))
__path__ = [str(path) for path in _path_entries if path.is_dir()]

__all__ = list(getattr(_impl, "__all__", ()))


def __getattr__(name: str) -> Any:
    try:
        return getattr(_impl, name)
    except AttributeError:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(dir(_impl)) | set(globals()))
