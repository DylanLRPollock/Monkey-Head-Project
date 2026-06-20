"""System-focused command registrations for the HueyOS CLI."""

from __future__ import annotations

import argparse
import json


def _cmd_system_check(args: argparse.Namespace) -> int:
    from huey.os.system_checks import system_check

    results = system_check()
    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        if args.verbose:
            print("System check results:")
        for key, value in sorted(results.items()):
            status = "OK" if value else "WARN"
            if args.verbose:
                print(f"  {key}: {status}")
            else:
                print(f"{key}: {status}")
    return 0


def register_system_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register system inspection commands."""

    sys_cmd = subparsers.add_parser(
        "system-check", help="Run environment diagnostics and compatibility checks."
    )
    sys_cmd.add_argument(
        "--json",
        action="store_true",
        help="Emit the collected results as JSON.",
    )
    sys_cmd.add_argument(
        "--verbose",
        action="store_true",
        help="Always print each individual check result.",
    )
    sys_cmd.set_defaults(handler=_cmd_system_check)
