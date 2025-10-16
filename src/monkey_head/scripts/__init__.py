# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for src/monkey_head/scripts

"""Compatibility helpers for legacy management scripts."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import List

_base = import_module("huey.scripts")

__all__ = list(getattr(_base, "__all__", ()))
for name in __all__:
    globals()[name] = getattr(_base, name)

__path__: List[str] = [str(Path(__file__).resolve().parent)]
for candidate in getattr(_base, "__path__", []):
    if candidate not in __path__:
        __path__.append(candidate)
