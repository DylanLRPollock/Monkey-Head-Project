"""Canonical HueyOS namespace exposed as :mod:`huey.os`.

During the layout migration, some maintained modules still live directly under
``huey`` while legacy modules remain in ``huey.memory.PY``. Expose all three
search roots here so ``huey.os`` can act as the canonical import surface while
the rest of the tree catches up.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

_base = importlib.import_module("huey")
_PACKAGE_DIR = Path(__file__).resolve().parent
_HUEY_DIR = _PACKAGE_DIR.parent
_LEGACY_DIR = _HUEY_DIR / "memory" / "PY"

__path__ = [
    str(path) for path in (_PACKAGE_DIR, _HUEY_DIR, _LEGACY_DIR) if path.is_dir()
]

__all__ = sorted(
    set(getattr(_base, "__all__", ()))
    | {
        "api",
        "cli",
        "core",
        "hardware",
        "honeycomb",
        "runtime",
        "scripts",
        "services",
        "utils",
    }
)


def __getattr__(name: str) -> Any:
    try:
        return getattr(_base, name)
    except AttributeError:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(dir(_base)) | set(globals()))
