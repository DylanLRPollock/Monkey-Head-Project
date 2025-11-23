# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Auto Sort module (src/hueyos/utils)

"""Compatibility wrapper around :mod:`huey.utils.auto_sort`."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_impl = import_module("huey.utils.auto_sort")

__all__ = ["auto_sort_memory", "get_extension_map"]

auto_sort_memory = getattr(_impl, "auto_sort_memory")
get_extension_map = getattr(_impl, "get_extension_map")


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__
