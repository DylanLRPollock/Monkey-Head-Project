# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Package initializer for huey/core

"""Core utilities for the Monkey Head compatibility layer."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["messaging", "system_checks", "task_scheduler"]


def __getattr__(name: str) -> Any:  # pragma: no cover - thin import proxy
    if name in __all__:
        module = import_module(f"monkey_head.core.{name}")
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:  # pragma: no cover - convenience helper
    return sorted(set(__all__) | set(globals()))
