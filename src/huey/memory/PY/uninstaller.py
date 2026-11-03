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
from huey.os.core.privileged_operations import authorize_privileged_operation

PROJECT_ROOT = find_project_root(Path(__file__).resolve())


def run_uninstaller(
    *, dry_run: bool = False, confirmed: bool = False, actor_role: str | None = None
) -> int:
    """Uninstall only on an explicitly authorized, verified local request."""
    try:
        should_execute = authorize_privileged_operation(
            "project.uninstall",
            dry_run=dry_run,
            confirmed=confirmed,
            actor_role=actor_role,
        )
    except PermissionError as exc:
        print(str(exc))
        return 2
    if not should_execute:
        # No path probing, filesystem mutations or subprocess creation in preview.
        print("[dry-run] Uninstall authorization preview; no host changes.")
        return 0

    paths = resolve_platform_script_paths(PROJECT_ROOT)
    if paths.uninstall is None:
        print(f"Unsupported operating system: {paths.host.system}")
        return 1
    if paths.uninstall.is_symlink() or not paths.uninstall.is_file():
        print(f"Uninstaller script not found: {paths.uninstall}")
        return 1

    project_root = PROJECT_ROOT.resolve()
    script = paths.uninstall.resolve()
    if not script.is_relative_to(project_root):
        print("Uninstaller script must be inside the project directory.")
        return 2

    command = paths.command_for("uninstall")
    if not command or not all(isinstance(arg, str) and arg for arg in command):
        print("Invalid uninstaller command.")
        return 2

    try:
        subprocess.run(
            command, check=True, cwd=project_root, shell=False, timeout=1200
        )
    except subprocess.TimeoutExpired:
        print("Uninstaller timed out.")
        return 124
    except subprocess.CalledProcessError as exc:
        print(f"Uninstaller failed with return code {exc.returncode}")
        return exc.returncode
    except OSError as exc:
        print(f"Unable to launch uninstaller: {exc}")
        return 1
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
        if not sys.stdin.isatty():
            print("Noninteractive use requires --yes.")
            sys.exit(2)
        try:
            reply = input("Run the Monkey Head uninstaller? [y/N]: ")
        except EOFError:
            sys.exit(2)
        confirmed = reply.strip().lower() in {"y", "yes"}

    sys.exit(
        run_uninstaller(
            dry_run=arguments.dry_run,
            confirmed=confirmed,
            actor_role="admin" if confirmed else None,
        )
    )
