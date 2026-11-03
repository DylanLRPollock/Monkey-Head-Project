#!/usr/bin/env python3
"""Dry-run memory indexing unless explicit --write and --index-path are provided."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __name__ == "__main__":
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

from huey.memory.indexing import discover_paths, rebuild_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--index-path", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true")
    action.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.write and args.index_path is None:
        parser.error("--write requires --index-path")
    try:
        root = args.root.expanduser().resolve()
        paths = discover_paths(root, index_path=args.index_path)
        count = (
            len(rebuild_index(root, index_path=args.index_path))
            if args.write
            else len(paths)
        )
    except (OSError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"Memory index error: {exc}\n")
    payload = {
        "mode": "write" if args.write else "dry-run",
        "root": str(root),
        "count": count,
        "index_path": str(args.index_path.resolve()) if args.index_path else None,
        "inputs": [str(path) for path in paths],
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(f"{payload['mode']}: {count} indexable files in {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
