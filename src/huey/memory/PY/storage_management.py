# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Storage Management module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utilities to manage the ``memory`` storage directory."""

from __future__ import annotations

import logging
import os
import shutil
import time
from pathlib import Path
from typing import Iterable, List, Optional

__all__ = ["StorageManager"]

logger = logging.getLogger(__name__)

# Default subfolders maintained inside the memory directory
DEFAULT_FOLDERS: List[str] = [
    "DOCS",
    "JPEG",
    "JSON",
    "LOGS",
    "PDF",
    "PNG",
    "SESSIONS",
    "UPLOADS",
    "ZIP",
    "TXT",
]

# Map common file extensions to destination folders
EXT_MAP = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "pdf": "PDF",
    "json": "JSON",
    "zip": "ZIP",
    "txt": "TXT",
    "log": "LOGS",
}


class StorageManager:
    """Helper to organize and maintain the project memory directory."""

    def __init__(self, base_dir: Optional[str | Path] = None) -> None:
        env = os.environ.get("MEMORY_DIR")
        self.base_dir = Path(base_dir or env or "memory")
        self.ensure_structure()

    # -----------------------------------------------------
    def ensure_structure(self) -> None:
        """Create missing default subfolders."""
        for folder in DEFAULT_FOLDERS:
            (self.base_dir / folder).mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------
    def _unique_move(self, src: Path, dst_dir: Path) -> Path:
        dst_dir.mkdir(parents=True, exist_ok=True)
        dest = dst_dir / src.name
        if dest.exists():
            stem, suffix = src.stem, src.suffix
            count = 1
            while dest.exists():
                dest = dst_dir / f"{stem}_{count}{suffix}"
                count += 1
        shutil.move(str(src), dest)
        return dest

    # -----------------------------------------------------
    def sort_root_files(self, *, dry_run: bool = False) -> None:
        """Move files in the base directory into subfolders by extension."""
        for item in self.base_dir.iterdir():
            if not item.is_file():
                continue
            ext = item.suffix.lower().lstrip(".")
            folder = EXT_MAP.get(ext, ext.upper() if ext else "MISC")
            if dry_run:
                target_dir = self.base_dir / folder
                logger.info("Dry-run move: %s -> %s", item, target_dir / item.name)
                continue
            self._unique_move(item, self.base_dir / folder)

    # -----------------------------------------------------
    def list_files(self, folder: Optional[str] = None) -> List[str]:
        """Return sorted file paths within ``folder`` or the entire directory."""
        path = self.base_dir / folder if folder else self.base_dir
        if not path.is_dir():
            return []
        return sorted(str(p) for p in path.rglob("*") if p.is_file())

    # -----------------------------------------------------
    def cleanup_empty_dirs(self) -> None:
        """Remove empty subdirectories in the base directory."""
        for d in self.base_dir.iterdir():
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()

    # -----------------------------------------------------
    def get_total_size(self, folder: Optional[str] = None) -> int:
        """Return the total size in bytes of all files under ``folder``."""
        path = self.base_dir / folder if folder else self.base_dir
        if not path.exists():
            return 0
        total = 0
        for p in path.rglob("*"):
            if p.is_file():
                try:
                    total += p.stat().st_size
                except (FileNotFoundError, PermissionError) as exc:
                    logger.warning(
                        "Failed to stat file for size calculation: %s (%s)", p, exc
                    )
        return total

    # -----------------------------------------------------
    def remove_older_than(
        self, days: int, folder: Optional[str] = None, *, dry_run: bool = False
    ) -> int:
        """Remove files older than ``days`` days and return the count."""
        path = self.base_dir / folder if folder else self.base_dir
        if days <= 0 or not path.exists():
            return 0
        threshold = time.time() - days * 86400
        removed = 0
        for p in path.rglob("*"):
            try:
                is_file = p.is_file()
            except OSError as exc:
                logger.warning(
                    "Failed to inspect path while pruning old files: %s (%s)", p, exc
                )
                continue

            if not is_file:
                continue

            try:
                modified_time = p.stat().st_mtime
            except (FileNotFoundError, PermissionError) as exc:
                logger.warning(
                    "Failed to stat file while pruning old files: %s (%s)", p, exc
                )
                continue

            if modified_time < threshold:
                if dry_run:
                    logger.info("Dry-run prune: %s", p)
                    removed += 1
                    continue
                try:
                    p.unlink()
                    removed += 1
                except (FileNotFoundError, PermissionError) as exc:
                    logger.warning("Failed to delete old file: %s (%s)", p, exc)
        self.cleanup_empty_dirs()
        return removed


def main(argv: Optional[Iterable[str]] = None) -> None:
    """Basic CLI for manual maintenance."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage memory storage")
    parser.add_argument(
        "--path",
        help="Base memory directory (defaults to MEMORY_DIR or 'memory')",
    )
    parser.add_argument(
        "--sort",
        action="store_true",
        help="Sort files located directly in the base directory",
    )
    parser.add_argument(
        "--list",
        metavar="FOLDER",
        help="List all files under the given subfolder",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove empty directories",
    )
    parser.add_argument(
        "--size",
        nargs="?",
        const="",
        metavar="FOLDER",
        help="Show total size of FOLDER or the entire storage",
    )
    parser.add_argument(
        "--prune",
        type=int,
        metavar="DAYS",
        help="Delete files older than DAYS days",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview sort/prune actions without changing files.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the confirmation prompt for prune operations.",
    )

    args = parser.parse_args(argv)
    mgr = StorageManager(args.path)

    if args.sort:
        mgr.sort_root_files(dry_run=args.dry_run)
    if args.list is not None:
        for f in mgr.list_files(args.list):
            print(f)
    if args.cleanup:
        mgr.cleanup_empty_dirs()
    if args.size is not None:
        size = mgr.get_total_size(args.size or None)
        print(size)
    if args.prune is not None:
        if not args.dry_run and not args.yes:
            confirmation = input(
                f"Delete files older than {args.prune} day(s) under '{mgr.base_dir}'? [y/N]: "
            ).strip().lower()
            if confirmation not in {"y", "yes"}:
                print("Cancelled.")
                return
        removed = mgr.remove_older_than(args.prune, dry_run=args.dry_run)
        print(removed)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
