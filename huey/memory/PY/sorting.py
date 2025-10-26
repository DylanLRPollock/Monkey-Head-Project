# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Sorting module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""General sorting utilities."""

from __future__ import annotations

import os
import re
from typing import Iterable, List

__all__ = ["list_files_by_mtime", "natural_sort"]


def list_files_by_mtime(directory: str, reverse: bool = False) -> List[str]:
    """Return file paths sorted by modification time.

    Parameters
    ----------
    directory:
        Path of the directory to scan.
    reverse:
        When ``True`` sort newest first instead of oldest first.
    """
    entries = [os.path.join(directory, f) for f in os.listdir(directory)]
    entries = [e for e in entries if os.path.isfile(e)]
    entries.sort(key=lambda p: os.path.getmtime(p), reverse=reverse)
    return entries


def natural_sort(items: Iterable[str]) -> List[str]:
    """Return ``items`` sorted in natural order."""

    def convert(text: str) -> int | str:
        return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key: str) -> list[int | str]:
        return [convert(component) for component in re.split(r"([0-9]+)", key)]

    return sorted(list(items), key=alphanum_key)
