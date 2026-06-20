# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: CLI compatibility wrapper (src)

"""Expose the HueyOS CLI interfaces under :mod:`huey.cli`."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Optional

from .memory.PY import cli as _cli

__all__ = ["main", "parse_arguments", "run_cli", "huey_main", "run_command_center"]


def parse_arguments(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments for the legacy Huey entry point."""

    parser = argparse.ArgumentParser(description="Huey CLI wrapper")
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def huey_main(config_file: str = "config.yaml") -> None:
    """Compatibility shim for legacy CLI entry points."""

    raise NotImplementedError(
        "The legacy CLI entry point is not available in this environment."
    )


def run_command_center(argv: list[str] | None = None) -> int:
    """Delegate to the read-only Command Center backend launcher."""

    from huey.apps.command_center.cli import main as command_center_main

    return command_center_main(argv)


def run_cli(argv: Optional[Iterable[str]] = None) -> None:
    """Invoke the legacy CLI with parsed arguments."""

    args = parse_arguments(argv)
    huey_main(config_file=args.config)


def main(argv: Optional[Iterable[str]] = None) -> int:
    """Route the Command Center subcommand before falling back to the main CLI."""

    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] in {"command-center", "command_center", "gui"}:
        return run_command_center(args[1:])
    return _cli.main(args)
