# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for src/hueyos/utils

"""Expose utility helpers while bridging legacy Monkey Head modules."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import List

_base = import_module("huey.utils")

# Re-export the public API from the maintained implementation.
auto_sort_memory = getattr(_base, "auto_sort_memory")
ensure_subdirectory = getattr(_base, "ensure_subdirectory")
get_logs_dir = getattr(_base, "get_logs_dir")
get_memory_path = getattr(_base, "get_memory_path")

__all__ = list(getattr(_base, "__all__", ()))

# Extend the package search path so that imports such as
# ``hueyos.utils.sorting`` resolve to the compatibility modules that live
# inside ``src/huey/memory/PY``.
__path__: List[str] = [str(Path(__file__).resolve().parent)]
for candidate in getattr(_base, "__path__", []):
    if candidate not in __path__:
        __path__.append(candidate)
_legacy = Path(__file__).resolve().parents[2] / "huey" / "memory" / "PY"
if _legacy.exists():
    legacy_path = str(_legacy)
    if legacy_path not in __path__:
        __path__.append(legacy_path)
