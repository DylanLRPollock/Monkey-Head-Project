"""Honeycomb storage, monitoring, and retention primitives."""

from __future__ import annotations

from .backup import perform_rsync_snapshot, restore_snapshot
from .index import HoneycombIndex
from .retention import RetentionPolicy, parse_duration
from .storage import HoneycombRecord, HoneycombStorage


def __getattr__(name: str):
    if name == "HoneycombMonitor":
        from .monitor import HoneycombMonitor

        globals()[name] = HoneycombMonitor
        return HoneycombMonitor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "HoneycombIndex",
    "HoneycombMonitor",
    "HoneycombRecord",
    "HoneycombStorage",
    "RetentionPolicy",
    "parse_duration",
    "perform_rsync_snapshot",
    "restore_snapshot",
]
