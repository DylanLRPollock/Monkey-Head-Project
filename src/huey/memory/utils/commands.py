"""Compatibility wrapper for :mod:`huey.memory.PY.commands`."""

from __future__ import annotations

from importlib import import_module

_impl = import_module("huey.memory.PY.commands")

__all__ = getattr(_impl, "__all__", [])

# Re-export public attributes for callers expecting the legacy module layout.
for name in dir(_impl):
    if name.startswith("_") and name not in __all__:
        continue
    globals()[name] = getattr(_impl, name)
