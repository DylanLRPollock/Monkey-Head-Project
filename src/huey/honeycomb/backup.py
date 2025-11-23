"""Compatibility shim forwarding to :mod:`hueyos.honeycomb.backup`."""

from hueyos.honeycomb.backup import BackupError, BackupResult, perform_rsync_snapshot, restore_snapshot

__all__ = [
    "BackupError",
    "BackupResult",
    "perform_rsync_snapshot",
    "restore_snapshot",
]
