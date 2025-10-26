"""Compatibility wrapper for :mod:`huey.memory.PY.logger`."""

from __future__ import annotations

from importlib import import_module

_impl = import_module("huey.memory.PY.logger")

__all__ = getattr(_impl, "__all__", []) or ["get_logger"]

for name in dir(_impl):
    if name.startswith("_") and name not in __all__:
        continue
    globals()[name] = getattr(_impl, name)
