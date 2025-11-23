"""Create and restore rsync-based honeycomb snapshots for HueyOS."""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from hueyos.utils.paths import get_memory_path


class BackupError(RuntimeError):
    """Raised when the backup tooling is not available or fails."""


@dataclass(frozen=True)
class BackupResult:
    """Details about a completed backup snapshot."""

    snapshot: Path
    command: List[str]
    stdout: str
    stderr: str


def _resolve_source(source: Optional[Path] = None) -> Path:
    if source is None:
        return get_memory_path(create=True)
    return Path(source).resolve()


def _ensure_destination(destination: Path) -> Path:
    destination = Path(destination).expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    return destination


def _resolve_rsync() -> str:
    binary = shutil.which("rsync")
    if not binary:
        raise BackupError(
            "rsync is required for honeycomb snapshots but was not found in PATH"
        )
    return binary


def perform_rsync_snapshot(
    *,
    destination: Path,
    source: Optional[Path] = None,
    extra_args: Optional[Iterable[str]] = None,
    dry_run: bool = False,
    timestamp: Optional[str] = None,
) -> BackupResult:
    """Create a timestamped rsync snapshot of the honeycomb memory tree."""

    rsync_binary = _resolve_rsync()
    source_path = _resolve_source(source)
    destination_root = _ensure_destination(destination)
    snapshot_id = timestamp or time.strftime("%Y%m%d-%H%M%S")
    snapshot_path = destination_root / snapshot_id
    snapshot_path.mkdir(parents=True, exist_ok=True)
    command: List[str] = [rsync_binary, "-a", "--delete"]
    if dry_run:
        command.append("--dry-run")
    if extra_args:
        command.extend(list(extra_args))
    command.extend([f"{source_path}/", str(snapshot_path)])
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return BackupResult(
        snapshot=snapshot_path,
        command=command,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def restore_snapshot(
    snapshot: Path, target: Path, *, extra_args: Optional[Iterable[str]] = None
) -> BackupResult:
    """Restore a snapshot into ``target`` using ``rsync``."""

    rsync_binary = _resolve_rsync()
    snapshot_path = Path(snapshot).resolve()
    target_path = Path(target).resolve()
    target_path.mkdir(parents=True, exist_ok=True)
    command: List[str] = [rsync_binary, "-a", "--delete"]
    if extra_args:
        command.extend(list(extra_args))
    command.extend([f"{snapshot_path}/", str(target_path)])
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return BackupResult(
        snapshot=target_path,
        command=command,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


__all__ = ["BackupError", "BackupResult", "perform_rsync_snapshot", "restore_snapshot"]
