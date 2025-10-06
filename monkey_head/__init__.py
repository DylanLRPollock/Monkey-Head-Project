"""Monkey Head compatibility package."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from . import core  # noqa: F401
from . import function_registry, pdf_utils, system_checks, utils  # noqa: F401

__all__ = [
    "core",
    "function_registry",
    "pdf_utils",
    "system_checks",
    "utils",
]

_LEGACY_PREFIX = "huey.memory.PY"


def __getattr__(name: str) -> Any:
    """Dynamically load legacy modules shipped with the project."""

    try:
        module = import_module(f"{_LEGACY_PREFIX}.{name}")
    except ModuleNotFoundError as exc:  # pragma: no cover - error path
        raise AttributeError(f"module 'monkey_head' has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> list[str]:  # pragma: no cover - convenience helper
    return sorted(set(__all__) | set(globals()) | _legacy_exports())


def _legacy_exports() -> set[str]:
    """Return a set of legacy module names for interactive discovery."""

    try:
        legacy_pkg = import_module(_LEGACY_PREFIX)
    except ModuleNotFoundError:  # pragma: no cover - legacy path missing
        return set()
    return set(getattr(legacy_pkg, "__all__", ()))
