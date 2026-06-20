#!/usr/bin/env python3
"""Validate archived dependency snapshots used for provenance and recovery."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    snapshots_dir = Path("archives") / "dependency-snapshots"
    if not snapshots_dir.is_dir():
        print(f"Archived dependency snapshot directory is missing: {snapshots_dir}")
        return 1

    snapshot_files = sorted(snapshots_dir.glob("*.pip-snapshot"))
    pip_check_files = sorted(snapshots_dir.glob("*pip-check*.txt"))

    if not snapshot_files or not pip_check_files:
        print("Archived dependency snapshots are incomplete.")
        print(f"  pip snapshots: {len(snapshot_files)}")
        print(f"  pip check reports: {len(pip_check_files)}")
        return 1

    print(
        "Archived dependency snapshots check passed "
        f"({len(snapshot_files)} snapshots, {len(pip_check_files)} pip-check reports)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
