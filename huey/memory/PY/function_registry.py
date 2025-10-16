# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Function Registry module (huey/memory/PY)

from __future__ import annotations

from typing import Callable, Dict, List

_FUNCTIONS: Dict[str, Callable] = {}


def register_function(func: Callable) -> Callable:
    """Register ``func`` in the global function registry."""
    _FUNCTIONS[func.__name__] = func
    return func


def list_functions() -> List[str]:
    """Return a sorted list of registered function names."""
    return sorted(_FUNCTIONS)


def get_functions() -> Dict[str, Callable]:
    """Return a copy of the function registry."""
    return dict(_FUNCTIONS)


__all__ = ["register_function", "list_functions", "get_functions"]
