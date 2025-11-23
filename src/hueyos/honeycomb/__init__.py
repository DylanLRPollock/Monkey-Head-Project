"""Compatibility layer mapping honeycomb helpers to the Huey implementation."""

from __future__ import annotations

from hueyos.honeycomb.backup import BackupError, BackupResult, perform_rsync_snapshot, restore_snapshot
from hueyos.honeycomb.index import HoneycombContentMapping, HoneycombIndex
from hueyos.honeycomb.monitor import HoneycombMonitor, HoneycombUsageTotals
from hueyos.honeycomb.retention import RetentionPolicy, parse_duration
from hueyos.honeycomb.storage import HoneycombRecord, HoneycombStorage

__all__ = [
    "BackupError",
    "BackupResult",
    "HoneycombContentMapping",
    "HoneycombIndex",
    "HoneycombMonitor",
    "HoneycombUsageTotals",
    "HoneycombRecord",
    "HoneycombStorage",
    "RetentionPolicy",
    "perform_rsync_snapshot",
    "parse_duration",
    "restore_snapshot",
]
