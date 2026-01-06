# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey

"""HueyOS runtime package consolidated under the ``src`` layout."""

from __future__ import annotations

import importlib
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


def _optional_import(module_name: str) -> Any | None:
    """Import ``module_name`` within :mod:`huey`, logging failures as debug."""

    try:
        return importlib.import_module(f"{__name__}.{module_name}")
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency path
        _LOGGER.debug("Optional module %s not available: %s", module_name, exc)
        return None


agents = _optional_import("agents")
core = _optional_import("core")
function_registry = importlib.import_module(f"{__name__}.function_registry")
pdf_utils = importlib.import_module(f"{__name__}.pdf_utils")
system_checks = importlib.import_module(f"{__name__}.system_checks")
utils = importlib.import_module(f"{__name__}.utils")
memory = importlib.import_module(f"{__name__}.memory")

__all__ = [
    "function_registry",
    "pdf_utils",
    "system_checks",
    "utils",
    "memory",
]

if agents is not None:
    __all__.append("agents")
if core is not None:
    __all__.append("core")

_LEGACY_PREFIX = f"{__name__}.memory.PY"


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
