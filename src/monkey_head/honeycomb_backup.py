"""Compatibility shim forwarding to :mod:`monkey_head.honeycomb.backup`."""

from __future__ import annotations

from monkey_head.honeycomb.backup import BackupError, BackupResult, perform_rsync_snapshot, restore_snapshot

__all__ = ["BackupError", "BackupResult", "perform_rsync_snapshot", "restore_snapshot"]
