# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey (src)

"""Compatibility package exposing the legacy Huey modules under ``src``."""

from __future__ import annotations

import importlib
from typing import Any

_CORE_MODULES = (
    "api",
    "cli",
    "config",
    "exceptions",
    "function_registry",
    "pdf_utils",
    "pyhuey_integration",
    "pygpt_integration",
    "run",
    "utils",
    "memory",
)

__all__ = []
__all__ = list(_CORE_MODULES)

_LEGACY_PREFIX = f"{__name__}.memory.PY"


def __getattr__(name: str) -> Any:
    """Dynamically expose legacy modules from :mod:`huey.memory.PY`."""

    try:
        module = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError:
        try:
            module = importlib.import_module(f"{_LEGACY_PREFIX}.{name}")
        except ModuleNotFoundError as exc:  # pragma: no cover - error path
            raise AttributeError(
                f"module '{__name__}' has no attribute {name!r}"
            ) from exc
    globals()[name] = module
    return module


def __dir__() -> list[str]:  # pragma: no cover - convenience helper
    return sorted(set(__all__) | set(globals()))
