#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Launcher module (huey/memory/PY)

"""Unified launcher for the Monkey Head Project."""

from __future__ import annotations

import argparse
import sys

import run
import installer
import uninstaller
import fresh_install
import repair
from monkey_head.core.system_checks import system_check


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Manage installation and launch the Monkey Head Project"
    )
    sub = parser.add_subparsers(dest="command")
    sub.required = False
    sub.add_parser("run", help="Launch the application")
    sub.add_parser("install", help="Run installer")
    sub.add_parser("uninstall", help="Run uninstaller")
    fresh_parser = sub.add_parser("fresh-install", help="Uninstall then reinstall")
    fresh_parser.add_argument(
        "--source",
        choices=["local", "github"],
        default="local",
        help="Install from local files or clone from GitHub",
    )
    fresh_parser.add_argument(
        "--repo",
        default=repair.REPO_URL,
        help="Repository URL when using --source github",
    )
    sub.add_parser("system-check", help="Run environment verification")

    args, remainder = parser.parse_known_args(argv)
    cmd = args.command or "run"

    if cmd == "install":
        sys.exit(installer.run_installer())
    if cmd == "uninstall":
        sys.exit(uninstaller.run_uninstaller())
    if cmd == "fresh-install":
        sys.exit(fresh_install.run_fresh_install(args.source, args.repo))
    if cmd == "system-check":
        system_check()
        return

    # default: run application
    sys.argv = [sys.argv[0]] + remainder
    run.main()


if __name__ == "__main__":
    main()
