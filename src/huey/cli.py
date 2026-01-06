# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: CLI compatibility wrapper (src)

"""Expose the HueyOS CLI interfaces under :mod:`huey.cli`."""

from __future__ import annotations

import argparse
from typing import Iterable, Optional

from .memory.PY import cli as _cli

main = _cli.main

__all__ = ["main", "parse_arguments", "run_cli", "huey_main"]


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


def run_cli(argv: Optional[Iterable[str]] = None) -> None:
    """Invoke the legacy CLI with parsed arguments."""

    args = parse_arguments(argv)
    huey_main(config_file=args.config)
