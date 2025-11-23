#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Startup module (huey/memory/PY)

"""Convenient startup entry point for the Monkey Head Project."""

from __future__ import annotations

import argparse
import os
import sys

import run
from hueyos.core.system_checks import (
    check_os_support,
    check_python_version,
    system_check,
)


def startup(skip_checks: bool = False, dry_run: bool = False) -> None:
    """Run optional checks and launch the main application."""
    if not skip_checks:
        check_os_support()
        check_python_version()
        try:
            system_check()
        except Exception as exc:
            print(f"System check failed: {exc}", file=sys.stderr)
            if dry_run:
                return
            # continue to run even if checks fail
    if dry_run:
        return
    run.main()


def main() -> None:
    """Parse startup options and invoke :func:`startup`."""
    parser = argparse.ArgumentParser(
        description="Perform environment checks and launch Monkey Head",
        add_help=False,
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip environment verification",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run checks but do not start the application",
    )
    parser.add_argument(
        "--workdir",
        type=str,
        help="Working directory passed through to run.py",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this message and exit",
    )

    args, remainder = parser.parse_known_args()

    if args.workdir:
        os.environ["PYGPT_WORKDIR"] = os.path.abspath(args.workdir)

    # pass remaining args to run.py
    sys.argv = [sys.argv[0]] + remainder
    startup(skip_checks=args.skip_checks, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
