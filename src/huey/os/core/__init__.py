"""Core namespace for the canonical :mod:`huey.os` package."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

_PACKAGE_DIR = Path(__file__).resolve().parent
_HUEY_CORE_DIR = _PACKAGE_DIR.parents[1] / "core"

__path__ = [str(path) for path in (_PACKAGE_DIR, _HUEY_CORE_DIR) if path.is_dir()]

_base = import_module("huey.core")
__all__ = sorted(set(getattr(_base, "__all__", ())) | {"resilience", "task_scheduler"})


def __getattr__(name: str) -> Any:
    try:
        return getattr(_base, name)
    except AttributeError:
        module = import_module(f"{__name__}.{name}")
        globals()[name] = module
        return module


def __dir__() -> list[str]:
    return sorted(set(__all__) | set(globals()))
