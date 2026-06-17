"""Compatibility namespace exposing :mod:`huey` as :mod:`hueyos`.

The migration keeps the maintained implementation under :mod:`huey` while many
call sites and tests still import :mod:`hueyos`.  Expose the same package search
roots so regular imports such as ``hueyos.core.task_scheduler`` and legacy
modules such as ``hueyos.chat_learning`` resolve without bespoke bridge files.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

_base = importlib.import_module("huey")
_PACKAGE_DIR = Path(__file__).resolve().parent
_SRC_DIR = _PACKAGE_DIR.parent
_HUEY_DIR = _SRC_DIR / "huey"
_LEGACY_DIR = _HUEY_DIR / "memory" / "PY"

__path__ = [
    str(path) for path in (_PACKAGE_DIR, _HUEY_DIR, _LEGACY_DIR) if path.is_dir()
]


def __getattr__(name: str) -> Any:
    try:
        return getattr(_base, name)
    except AttributeError:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module


def __dir__() -> list[str]:
    return sorted(set(dir(_base)))
