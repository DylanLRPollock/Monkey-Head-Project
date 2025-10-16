# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Function Registry module (huey)

"""Simple function registry used by high level utilities."""

from __future__ import annotations

from typing import Callable, Dict, List

_FUNCTIONS: Dict[str, Callable] = {}

__all__ = ["register_function", "list_functions", "get_functions"]


def register_function(func: Callable) -> Callable:
    """Register ``func`` in the global registry."""

    _FUNCTIONS[func.__name__] = func
    return func


def list_functions() -> List[str]:
    """Return a sorted list of registered function names."""

    return sorted(_FUNCTIONS)


def get_functions() -> Dict[str, Callable]:
    """Return a copy of the registered functions."""

    return dict(_FUNCTIONS)
