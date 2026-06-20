# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Auto Sort module (huey/scripts)

"""CLI for the :func:`huey.os.utils.auto_sort.auto_sort_memory` helper."""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from huey.os.utils.auto_sort import auto_sort_memory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Organise files stored in the Monkey Head memory directory.",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Source directory containing unsorted files (defaults to memory/RAW).",
    )
    parser.add_argument(
        "--destination",
        type=str,
        default=None,
        help="Destination root directory (defaults to the configured memory path).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the planned moves without modifying the filesystem.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the summary as JSON for easy scripting.",
    )
    return parser


def main(argv: list[str] | None = None) -> Dict[str, Any]:
    """Execute the auto-sort command and return the summary object."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    summary = auto_sort_memory(
        source_dir=args.source,
        destination_root=args.destination,
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        moved = summary.get("moved", [])
        skipped = summary.get("skipped", [])
        print(f"Source: {summary['source']}")
        print(f"Destination: {summary['destination']}")
        print(f"Moved {len(moved)} file(s)")
        if moved:
            for item in moved:
                print(f"  - {item}")
        if skipped:
            print(f"Skipped {len(skipped)} file(s) due to naming conflicts:")
            for item in skipped:
                print(f"  - {item}")
    return summary


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
