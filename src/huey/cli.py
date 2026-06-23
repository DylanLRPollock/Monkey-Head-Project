# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: CLI compatibility wrapper (src)

"""Expose the HueyOS CLI interfaces under :mod:`huey.cli`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from warnings import deprecated

from .memory.PY import cli as _cli

__all__ = [
    "main",
    "parse_arguments",
    "run_cli",
    "huey_main",
    "run_command_center",
    "run_gui",
]

type Argv = Iterable[str] | None


def parse_arguments(argv: Argv = None) -> argparse.Namespace:
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


@deprecated(
    "huey.cli.huey_main() is a legacy compatibility entry point; use "
    "huey.cli.main() instead.",
    stacklevel=2,
)
def huey_main(config_file: str = "config.yaml") -> None:
    """Compatibility shim for legacy CLI entry points."""

    raise NotImplementedError(
        "The legacy CLI entry point is not available in this environment."
    )


def run_command_center(argv: list[str] | None = None) -> int:
    """Delegate to the read-only Command Center backend launcher."""

    from huey.apps.command_center.cli import main as command_center_main

    return command_center_main(argv)


def run_gui(argv: list[str] | None = None) -> int:
    """Launch the unified HueyOS desktop shell."""

    del argv
    from huey.run import launch_manager_ui

    launch_manager_ui()
    return 0


@deprecated(
    "huey.cli.run_cli() is a legacy compatibility wrapper; use huey.cli.main() "
    "instead.",
    stacklevel=2,
)
def run_cli(argv: Argv = None) -> None:
    """Invoke the legacy CLI with parsed arguments."""

    args = parse_arguments(argv)
    huey_main(config_file=args.config)


def main(argv: Argv = None) -> int:
    """Route the Command Center subcommand before falling back to the main CLI."""

    args = list(argv) if argv is not None else sys.argv[1:]
    if args and args[0] in {"command-center", "command_center"}:
        return run_command_center(args[1:])
    if args and args[0] == "gui":
        return run_gui(args[1:])
    return _cli.main(args)
