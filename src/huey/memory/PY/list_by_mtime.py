# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: List By Mtime module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Backward-compatible wrapper for :mod:`hueyos.utils.sorting`."""

from __future__ import annotations

from .sorting import list_files_by_mtime

__all__ = ["list_files_by_mtime"]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="List files in a directory from oldest to newest"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan",
    )
    args = parser.parse_args()

    for file_path in list_files_by_mtime(args.directory):
        print(file_path)
