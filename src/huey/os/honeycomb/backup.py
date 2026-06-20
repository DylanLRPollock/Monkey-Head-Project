"""Backup and restore helpers for Honeycomb storage."""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class BackupError(RuntimeError):
    """Raised when a Honeycomb backup or restore operation fails."""


@dataclass(frozen=True)
class BackupResult:
    """Result metadata for a Honeycomb backup or restore operation."""

    source: Path
    destination: Path
    files_copied: int
    bytes_copied: int
    started_at: float
    finished_at: float
    operation: str = "backup"

    @property
    def elapsed_seconds(self) -> float:
        return self.finished_at - self.started_at

    def as_dict(self) -> dict[str, object]:
        return {
            "source": str(self.source),
            "destination": str(self.destination),
            "files_copied": self.files_copied,
            "bytes_copied": self.bytes_copied,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed_seconds": self.elapsed_seconds,
            "operation": self.operation,
        }


def _copy_tree(
    source: Path, destination: Path, *, overwrite: bool = False
) -> tuple[int, int]:
    if not source.exists():
        raise BackupError(f"source does not exist: {source}")

    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() and not overwrite:
            raise BackupError(f"destination already exists: {destination}")
        shutil.copy2(source, destination)
        return 1, destination.stat().st_size

    if destination.exists() and not overwrite:
        raise BackupError(f"destination already exists: {destination}")

    files_copied = 0
    bytes_copied = 0
    destination.mkdir(parents=True, exist_ok=True)

    for item in source.rglob("*"):
        relative = item.relative_to(source)
        target = destination / relative

        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)
        files_copied += 1
        bytes_copied += target.stat().st_size

    return files_copied, bytes_copied


def perform_rsync_snapshot(
    source: str | Path,
    destination: str | Path,
    *,
    overwrite: bool = False,
    label: Optional[str] = None,
) -> BackupResult:
    """Create a Honeycomb snapshot.

    The historical function name references rsync, but this implementation uses
    Python's standard library so it works on Windows development machines too.
    """

    started = time.time()
    source_path = Path(source).expanduser().resolve()
    destination_path = Path(destination).expanduser()

    if label:
        destination_path = destination_path / label

    destination_path = destination_path.resolve()

    try:
        files, size = _copy_tree(source_path, destination_path, overwrite=overwrite)
    except Exception as exc:
        if isinstance(exc, BackupError):
            raise
        raise BackupError(str(exc)) from exc

    finished = time.time()
    return BackupResult(
        source=source_path,
        destination=destination_path,
        files_copied=files,
        bytes_copied=size,
        started_at=started,
        finished_at=finished,
        operation="backup",
    )


def restore_snapshot(
    snapshot: str | Path,
    destination: str | Path,
    *,
    overwrite: bool = False,
) -> BackupResult:
    """Restore a Honeycomb snapshot to ``destination``."""

    started = time.time()
    snapshot_path = Path(snapshot).expanduser().resolve()
    destination_path = Path(destination).expanduser().resolve()

    try:
        files, size = _copy_tree(snapshot_path, destination_path, overwrite=overwrite)
    except Exception as exc:
        if isinstance(exc, BackupError):
            raise
        raise BackupError(str(exc)) from exc

    finished = time.time()
    return BackupResult(
        source=snapshot_path,
        destination=destination_path,
        files_copied=files,
        bytes_copied=size,
        started_at=started,
        finished_at=finished,
        operation="restore",
    )


__all__ = ["BackupError", "BackupResult", "perform_rsync_snapshot", "restore_snapshot"]
