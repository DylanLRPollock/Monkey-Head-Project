"""Canonical Honeycomb package for HueyOS.

This package provides the maintained ``huey.os.honeycomb`` import path while
legacy ``huey.honeycomb`` modules remain compatibility shims.
"""

from .backup import BackupError, BackupResult, perform_rsync_snapshot, restore_snapshot
from .index import HoneycombContentMapping, HoneycombIndex
from .monitor import HoneycombMonitor, HoneycombUsageTotals
from .retention import RetentionPolicy, parse_duration
from .storage import SCHEMA_VERSION, HoneycombRecord, HoneycombStorage

__all__ = [
    "BackupError",
    "BackupResult",
    "HoneycombContentMapping",
    "HoneycombIndex",
    "HoneycombMonitor",
    "HoneycombRecord",
    "HoneycombStorage",
    "HoneycombUsageTotals",
    "RetentionPolicy",
    "SCHEMA_VERSION",
    "parse_duration",
    "perform_rsync_snapshot",
    "restore_snapshot",
]
