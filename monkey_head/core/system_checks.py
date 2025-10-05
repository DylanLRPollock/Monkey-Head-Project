"""Compatibility layer for :mod:`monkey_head.system_checks`."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_module = import_module("monkey_head.system_checks")

__all__ = getattr(_module, "__all__", [name for name in dir(_module) if not name.startswith("_")])
if "check_python_version" not in __all__:
    __all__.append("check_python_version")

for _name in __all__:
    if _name != "check_python_version":
        globals()[_name] = getattr(_module, _name)

logger = getattr(_module, "logger")


def __getattr__(name: str) -> Any:  # pragma: no cover - proxy
    return getattr(_module, name)


def __setattr__(name: str, value: Any) -> None:  # pragma: no cover - proxy
    setattr(_module, name, value)
    globals()[name] = value


def check_python_version() -> None:
    """Warn when running on experimental Python versions.

    This wrapper mirrors :func:`monkey_head.system_checks.check_python_version`
    but uses the ``logger`` attribute from this proxy module. Tests that patch
    ``monkey_head.core.system_checks.logger`` therefore observe the expected
    behaviour without needing to modify the legacy implementation directly.
    """

    info = getattr(_module, "sys").version_info
    if isinstance(info, tuple):
        major, minor = info[0], info[1]
    else:
        major = getattr(info, "major", 0)
        minor = getattr(info, "minor", 0)

    if major == 3 and minor == 13:
        logger.warning(
            "Python 3.13 detected. This version is experimental and not fully supported."
        )
