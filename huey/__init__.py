# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey

"""Monkey Head compatibility package."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

_LOGGER = logging.getLogger(__name__)


def _optional_import(module_name: str) -> Any | None:
    """Import ``module_name`` capturing errors from optional dependencies."""

    try:
        return import_module(f"monkey_head.{module_name}")
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency path
        _LOGGER.debug("Optional module %s not available: %s", module_name, exc)
        return None


agents = _optional_import("agents")
core = _optional_import("core")
function_registry = import_module("monkey_head.function_registry")
pdf_utils = import_module("monkey_head.pdf_utils")
system_checks = import_module("monkey_head.system_checks")
utils = import_module("monkey_head.utils")

__all__ = [
    "function_registry",
    "pdf_utils",
    "system_checks",
    "utils",
]

if agents is not None:
    __all__.append("agents")
if core is not None:
    __all__.append("core")

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
