"""Compatibility wrapper for :mod:`huey.system_checks`."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_impl = import_module("monkey_head.system_checks")

__all__ = list(getattr(_impl, "__all__", ()))
if not __all__:
    __all__ = [
        "check_os_support",
        "check_python_version",
        "ensure_admin",
        "logger",
        "system_check",
    ]

for name in __all__:
    globals()[name] = getattr(_impl, name)


# Expose supporting modules that callers monkeypatch in tests and CLI utilities.
platform = getattr(_impl, "platform")
shutil = getattr(_impl, "shutil")
sys = getattr(_impl, "sys")
distro = getattr(_impl, "distro", None)

__all__.extend(["platform", "shutil", "sys", "distro"])


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__
