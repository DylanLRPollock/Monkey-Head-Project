#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Uninstaller module (huey/memory/PY)

"""Cross-platform uninstaller for the Monkey Head Project."""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = Path(__file__).resolve().parents[4]

LINUX_UNINSTALL = str(
    PROJECT_ROOT / "platform" / "installers" / "debian" / "Debian" / "uninstall-deb.sh"
)
MAC_UNINSTALL = os.path.join(SCRIPT_DIR, "setup", "macOS", "uninstall.sh")
WINDOWS_UNINSTALL = str(PROJECT_ROOT / "src" / "huey" / "memory" / "BAT" / "uninstall.bat")


def _uninstall_command(system: str) -> list[str] | None:
    if system == "Linux":
        return ["bash", LINUX_UNINSTALL]
    if system == "Darwin":
        return ["bash", MAC_UNINSTALL]
    if system == "Windows":
        return ["cmd", "/c", WINDOWS_UNINSTALL]
    return None


def run_uninstaller(*, dry_run: bool = False, confirmed: bool = True) -> int:
    system = platform.system()
    command = _uninstall_command(system)
    if command is None:
        print(f"Unsupported operating system: {system}")
        return 1

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

    sys.exit(
        run_uninstaller(dry_run=arguments.dry_run, confirmed=confirmed)
    )
