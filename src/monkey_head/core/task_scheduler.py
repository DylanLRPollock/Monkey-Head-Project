"""Compatibility wrapper for :mod:`huey.core.task_scheduler`."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_impl = import_module("huey.core.task_scheduler")

__all__ = list(getattr(_impl, "__all__", ()))
if not __all__:
    __all__ = [
        "Agent",
        "HealthProvider",
        "ResourceProfile",
        "ResourceSnapshot",
        "TaskLogEntry",
        "TaskPriority",
        "TaskRecord",
        "TaskScheduler",
        "TaskStatus",
    ]

for name in __all__:
    globals()[name] = getattr(_impl, name)


def __getattr__(name: str) -> Any:
    return getattr(_impl, name)


__doc__ = _impl.__doc__
