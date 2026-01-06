# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey (src)

"""Compatibility package exposing the legacy Huey modules under ``src``."""

from __future__ import annotations

import importlib
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

_CORE_MODULES = (
    "api",
    "cli",
    "config",
    "exceptions",
    "function_registry",
    "pdf_utils",
    "pygpt_integration",
    "run",
    "utils",
    "memory",
)

__all__ = []


def _optional_import(module_name: str) -> Any | None:
    """Import ``module_name`` from :mod:`huey` and log failures."""

    try:
        return importlib.import_module(f"{__name__}.{module_name}")
    except ModuleNotFoundError as exc:  # pragma: no cover - optional path
        _LOGGER.debug("Optional module %s not available: %s", module_name, exc)
        return None


for _module_name in _CORE_MODULES:
    _module = _optional_import(_module_name)
    if _module is not None:
        globals()[_module_name] = _module
        __all__.append(_module_name)

_LEGACY_PREFIX = f"{__name__}.memory.PY"


def __getattr__(name: str) -> Any:
    """Dynamically expose legacy modules from :mod:`huey.memory.PY`."""

    try:
        module = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError:
        try:
            module = importlib.import_module(f"{_LEGACY_PREFIX}.{name}")
        except ModuleNotFoundError as exc:  # pragma: no cover - error path
            raise AttributeError(f"module '{__name__}' has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> list[str]:  # pragma: no cover - convenience helper
    return sorted(set(__all__) | set(globals()))
