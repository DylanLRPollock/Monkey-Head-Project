# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey.memory (src)

"""Legacy memory package wrapper for HueyOS."""

from __future__ import annotations

import importlib
from typing import Any

_CORE_MODULES = (
    "core",
    "utils",
    "PY",
)

__all__ = list(_CORE_MODULES)

_LEGACY_PREFIX = f"{__name__}.PY"


def __getattr__(name: str) -> Any:
    """Dynamically expose legacy modules from :mod:`huey.memory.PY`."""

    try:
        module = importlib.import_module(f"{_LEGACY_PREFIX}.{name}")
    except ModuleNotFoundError as exc:  # pragma: no cover - error path
        raise AttributeError(f"module '{__name__}' has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> list[str]:  # pragma: no cover - convenience helper
    return sorted(set(__all__) | set(globals()))
