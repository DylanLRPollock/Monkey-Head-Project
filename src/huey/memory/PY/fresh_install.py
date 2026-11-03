#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Fresh Install module (huey/memory/PY)

"""Run a clean reinstall of the Monkey Head Project."""

from __future__ import annotations

import argparse
import sys

import installer
import repair
import uninstaller

from huey.os.core.privileged_operations import authorize_privileged_operation


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line options."""
    parser = argparse.ArgumentParser(
        description="Clean reinstall the Monkey Head Project",
    )
    parser.add_argument(
        "--source",
        choices=["local", "github"],
        help="Install from local files or clone from GitHub",
    )
    parser.add_argument(
        "--repo",
        default=repair.REPO_URL,
        help="Repository URL when using --source github",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Explicitly authorize reinstall"
    )
    return parser.parse_args(argv)


def _prompt_source() -> str:
    """Interactively prompt for reinstall source."""
    choice = (
        input("Reinstall from local files or GitHub clone? [l/g]: ").strip().lower()
    )
    return "github" if choice.startswith("g") else "local"


def run_fresh_install(
    source: str | None = None,
    repo_url: str = repair.REPO_URL,
    *,
    confirmed: bool = False,
    actor_role: str | None = None,
) -> int:
    """Remove existing files and reinstall only after explicit confirmation."""
    try:
        authorize_privileged_operation(
            "project.uninstall", confirmed=confirmed, actor_role=actor_role
        )
    except PermissionError:
        return 2
    if source is None:
        source = _prompt_source()
    if source == "github":
        # repair.run_repair handles uninstallation internally
        return repair.run_repair(
            repo_url, confirmed=confirmed, actor_role=actor_role
        )

    print("Starting fresh installation...")
    uninstall_rc = uninstaller.run_uninstaller(
        confirmed=confirmed, actor_role=actor_role
    )
    if uninstall_rc != 0:
        print(f"Uninstall failed with code {uninstall_rc}")
        return uninstall_rc
    return installer.run_installer()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return run_fresh_install(
        args.source,
        args.repo,
        confirmed=args.yes,
        actor_role="admin" if args.yes else None,
    )


if __name__ == "__main__":
    sys.exit(main())
