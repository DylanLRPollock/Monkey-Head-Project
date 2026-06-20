"""Deterministic fixture queue helpers for the V1 proof loop."""

from __future__ import annotations

from pathlib import Path
from shutil import move

_IGNORED_SUFFIXES = {".partial", ".tmp"}


def list_pending_fixtures(queue_dir: str | Path) -> list[Path]:
    """Return pending fixture files in deterministic filename order."""
    queue_path = Path(queue_dir)
    if not queue_path.exists():
        return []

    pending = [
        item
        for item in queue_path.iterdir()
        if item.is_file() and item.suffix not in _IGNORED_SUFFIXES
    ]
    return sorted(pending, key=lambda path: path.name)


def claim_fixture(path: str | Path, runs_dir: str | Path) -> Path:
    """Atomically claim a fixture by moving it into the active runs directory."""
    source = Path(path)
    destination_dir = Path(runs_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    moved_to = move(str(source), str(destination))
    return Path(moved_to)


def mark_processed(path: str | Path, processed_dir: str | Path) -> Path:
    """Move a processed fixture to the processed archive directory."""
    source = Path(path)
    destination_dir = Path(processed_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / source.name
    moved_to = move(str(source), str(destination))
    return Path(moved_to)


def mark_failed(
    path: str | Path, failed_dir: str | Path, reason: str
) -> tuple[Path, Path]:
    """Move a failed fixture to failed archive and write a sidecar reason file."""
    source = Path(path)
    destination_dir = Path(failed_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    failed_fixture = destination_dir / source.name
    moved_to = Path(move(str(source), str(failed_fixture)))

    reason_path = destination_dir / f"{moved_to.name}.reason.txt"
    reason_path.write_text(reason, encoding="utf-8")
    return moved_to, reason_path
