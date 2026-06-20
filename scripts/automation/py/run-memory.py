#!/usr/bin/env python3
"""Run any remembered Python script from ``src/huey/memory/PY`` by filename."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from _dispatch import available_memory_python_scripts, run_memory_python


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a remembered Python script from src/huey/memory/PY."
    )
    parser.add_argument("script", help="Filename inside src/huey/memory/PY.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    available = set(available_memory_python_scripts(_THIS_DIR))
    if args.script not in available:
        parser.error(
            f"Unknown remembered Python script '{args.script}'. "
            f"Available count: {len(available)}."
        )

    run_memory_python(args.script, start_path=_THIS_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
