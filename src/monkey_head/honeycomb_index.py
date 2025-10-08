"""Compatibility wrapper for :mod:`huey.honeycomb_index`."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_impl = import_module("huey.honeycomb_index")

__all__ = list(getattr(_impl, "__all__", ()))
if not __all__:
    __all__ = [
        "HoneycombIndex",
        "HoneycombIndexRecord",
    ]

for name in __all__:
    globals()[name] = getattr(_impl, name)


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__
