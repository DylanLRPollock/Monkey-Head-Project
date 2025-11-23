"""File and natural sorting helpers."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, List


def list_files_by_mtime(directory: str, reverse: bool = False) -> List[str]:
    base = Path(directory)
    files = [p for p in base.iterdir() if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=reverse)
    return [str(p) for p in files]


_splitter = re.compile(r"(\d+)")


def natural_sort(items: Iterable[str]) -> List[str]:
    def key(value: str):
        return [int(part) if part.isdigit() else part for part in _splitter.split(value)]

    return sorted(items, key=key)


__all__ = ["list_files_by_mtime", "natural_sort"]
