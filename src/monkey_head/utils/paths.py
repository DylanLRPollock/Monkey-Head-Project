# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Paths module (src/monkey_head/utils)

"""Compatibility wrapper around :mod:`huey.utils.paths`."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_impl = import_module("huey.utils.paths")

__all__ = [
    "ensure_subdirectory",
    "get_logs_dir",
    "get_memory_path",
    "memory_candidates",
]

ensure_subdirectory = getattr(_impl, "ensure_subdirectory")
get_logs_dir = getattr(_impl, "get_logs_dir")
get_memory_path = getattr(_impl, "get_memory_path")
memory_candidates = getattr(_impl, "memory_candidates")


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__
