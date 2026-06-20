"""Script compatibility package for :mod:`huey.os`."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

_PACKAGE_DIR = Path(__file__).resolve().parent
_HUEY_DIR = _PACKAGE_DIR.parents[1]
_HUEY_SCRIPTS_DIR = _HUEY_DIR / "scripts"
_LEGACY_DIR = _HUEY_DIR / "memory" / "PY"

__path__ = [
    str(path)
    for path in (_PACKAGE_DIR, _HUEY_SCRIPTS_DIR, _LEGACY_DIR)
    if path.is_dir()
]

_base = importlib.import_module("huey.scripts")
__all__ = list(getattr(_base, "__all__", ()))


def __getattr__(name: str) -> Any:
    try:
        return getattr(_base, name)
    except AttributeError:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()))
