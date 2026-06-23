"""Tools and utilities for the scaffold runtime."""

from __future__ import annotations

from .backup import create_backup_archive
from .encryption import FernetVault
from .file_watcher import FileWatcher
from .hashing import sha256_text
from .metrics import MetricsRegistry
from .profiler import ProfileTimer
from .scheduler import JobScheduler, ScheduledJob
from .testing import assert_mapping_subset, build_fixture_payload

__all__ = [
    "FernetVault",
    "FileWatcher",
    "JobScheduler",
    "MetricsRegistry",
    "ProfileTimer",
    "ScheduledJob",
    "assert_mapping_subset",
    "build_fixture_payload",
    "create_backup_archive",
    "sha256_text",
]
