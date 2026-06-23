"""Backup helpers for packaging data and runtime snapshots."""

from __future__ import annotations

import shutil
from pathlib import Path


def create_backup_archive(source: str | Path, destination_stem: str | Path) -> str:
    source_path = Path(source)
    destination = Path(destination_stem)
    archive = shutil.make_archive(str(destination), "zip", root_dir=str(source_path))
    return archive


__all__ = ["create_backup_archive"]
