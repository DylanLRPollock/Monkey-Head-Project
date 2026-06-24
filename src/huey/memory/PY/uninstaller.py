#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Uninstaller module (huey/memory/PY)

"""Cross-platform uninstaller for the Monkey Head Project."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from huey.os.core.platform_support import find_project_root, resolve_platform_script_paths

PROJECT_ROOT = find_project_root(Path(__file__).resolve())


def run_uninstaller(*, dry_run: bool = False, confirmed: bool = True) -> int:
    paths = resolve_platform_script_paths(PROJECT_ROOT)
    if paths.uninstall is None:
        host = paths.host
        print(f"Unsupported operating system: {host.system}")
        return 1
    if not paths.uninstall.exists():
        print(f"Uninstaller script not found: {paths.uninstall}")
        return 1

    command = paths.command_for("uninstall") or [str(paths.uninstall)]

    if dry_run:
        print(f"[dry-run] {' '.join(command)}")
        return 0

    if not confirmed:
        print("Confirmation required. Re-run with confirmed=True or --yes.")
        return 2

    try:
        subprocess.run(command, check=True, cwd=PROJECT_ROOT)
    except subprocess.CalledProcessError as exc:
        print(f"Uninstaller failed with return code {exc.returncode}")
        return exc.returncode
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Monkey Head uninstaller.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the uninstall command without executing it.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation prompt.",
    )
    arguments = parser.parse_args()

    confirmed = arguments.yes or arguments.dry_run
    if not confirmed:
        reply = input("Run the Monkey Head uninstaller? [y/N]: ").strip().lower()
        confirmed = reply in {"y", "yes"}

    sys.exit(run_uninstaller(dry_run=arguments.dry_run, confirmed=confirmed))
