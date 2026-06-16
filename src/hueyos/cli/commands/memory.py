"""Memory command registration scaffold for incremental CLI extraction."""

from __future__ import annotations

import argparse
from typing import Callable


def _legacy_handler(name: str) -> Callable[[argparse.Namespace], int]:
    def _handler(args: argparse.Namespace) -> int:
        from huey.memory.PY import cli as legacy_cli

        return getattr(legacy_cli, name)(args)

    return _handler


def register_memory_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register memory-oriented command groups via legacy handlers."""

    sort_cmd = subparsers.add_parser(
        "memory-sort", help="Organise the shared memory directory by file type."
    )
    sort_cmd.add_argument(
        "--source",
        help="Source directory containing unsorted files (defaults to memory/RAW).",
    )
    sort_cmd.add_argument(
        "--destination",
        help="Destination root directory (defaults to the configured memory path).",
    )
    sort_cmd.add_argument(
        "--dry-run",
        action="store_true",
        help="Report planned moves without modifying the filesystem.",
    )
    sort_cmd.add_argument(
        "--json",
        action="store_true",
        help="Emit the summary as JSON.",
    )
    sort_cmd.set_defaults(handler=_legacy_handler("_cmd_memory_sort"))
