# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Example Data Loader module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Example utility that loads rows from a CSV file."""

from __future__ import annotations

import argparse
import csv


def load_rows(csv_path: str) -> list[dict[str, str]]:
    """Return list of rows from ``csv_path``."""

    rows: list[dict[str, str]] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows.extend(reader)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Load CSV rows")
    parser.add_argument("file", type=str, help="CSV file path")
    args = parser.parse_args()
    rows = load_rows(args.file)
    print(f"Loaded {len(rows)} rows from {args.file}")


if __name__ == "__main__":  # pragma: no cover - example script
    main()
