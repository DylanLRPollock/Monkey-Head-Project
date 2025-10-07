"""Monkey Head compatibility package."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

LOGGER = logging.getLogger(__name__)

_OPTIONAL_MODULES = (
    "agents",
    "core",
    "function_registry",
    "honeycomb_storage",
    "llm",
    "pdf_utils",
    "system_checks",
    "utils",
)

_LOADED_MODULES: dict[str, Any] = {}
_MISSING_OPTIONALS: set[str] = set()

for _module in _OPTIONAL_MODULES:
    try:
        _LOADED_MODULES[_module] = import_module(f"{__name__}.{_module}")
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on extras
        LOGGER.debug("Optional Monkey Head module %s unavailable: %s", _module, exc)
        _MISSING_OPTIONALS.add(_module)
    else:
        globals()[_module] = _LOADED_MODULES[_module]

__all__ = [name for name in _OPTIONAL_MODULES if name not in _MISSING_OPTIONALS]

_LEGACY_PREFIX = "huey.memory.PY"


def __getattr__(name: str) -> Any:
    """Dynamically load legacy or lazily imported modules."""

    if name in _LOADED_MODULES:
        return _LOADED_MODULES[name]

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

