#!/usr/bin/env python3
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utility to organize files from ``raw`` into ``memory``."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
MEMORY_DIR = BASE_DIR / "memory"

# map common extensions to existing subfolders
EXT_MAP = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "pdf": "PDF",
    "json": "JSON",
    "zip": "ZIP",
    "txt": "TXT",
}


def _unique_move(src: Path, dst_dir: Path) -> Path:
    """Move ``src`` into ``dst_dir`` ensuring the filename is unique."""
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


def sort_raw_files(base_dir: Path | None = None) -> None:
    """Move files from ``raw`` to ``memory`` categorized by extension."""
    if base_dir is None:
        base_dir = BASE_DIR
    raw = base_dir / "raw"
    mem = base_dir / "memory"
    raw.mkdir(exist_ok=True)
    mem.mkdir(exist_ok=True)

    for item in raw.iterdir():
        if not item.is_file():
            continue
        ext = item.suffix.lower().lstrip(".")
        folder_name = EXT_MAP.get(ext, ext.upper() if ext else "MISC")
        _unique_move(item, mem / folder_name)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sort files from 'raw' into 'memory' by extension"
    )
    parser.add_argument(
        "base",
        nargs="?",
        default=BASE_DIR,
        type=Path,
        help="Directory containing 'raw' and 'memory' folders",
    )
    args = parser.parse_args()
    sort_raw_files(args.base)


if __name__ == "__main__":
    main()
