"""Utility compatibility package for :mod:`huey.os`.

Modern helpers live under :mod:`huey.utils`; several legacy helpers still live
in ``huey.memory.PY``.  This package exposes both locations under
``huey.os.utils`` so package-style imports keep working during the migration.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

_PACKAGE_DIR = Path(__file__).resolve().parent
_HUEY_DIR = _PACKAGE_DIR.parents[1]
_HUEY_UTILS_DIR = _HUEY_DIR / "utils"
_LEGACY_DIR = _HUEY_DIR / "memory" / "PY"

__path__ = [
    str(path) for path in (_PACKAGE_DIR, _HUEY_UTILS_DIR, _LEGACY_DIR) if path.is_dir()
]

_base = importlib.import_module("huey.utils")

for _name in getattr(_base, "__all__", ()):
    globals()[_name] = getattr(_base, _name)

__all__ = sorted(
    set(getattr(_base, "__all__", ())) | {"auto_sort", "gpu", "paths", "persistence"}
)


def __getattr__(name: str) -> Any:
    try:
        return getattr(_base, name)
    except AttributeError:
        module = importlib.import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()))
