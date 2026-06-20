"""Compatibility shim forwarding to :mod:`huey.os.honeycomb.backup`."""

from __future__ import annotations

from huey.os.honeycomb.backup import (
    BackupError,
    BackupResult,
    perform_rsync_snapshot,
    restore_snapshot,
)

__all__ = ["BackupError", "BackupResult", "perform_rsync_snapshot", "restore_snapshot"]
