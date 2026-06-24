#!/usr/bin/env python3
"""Unified installer for HueyOS setup scripts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from huey.os.core.platform_support import (
    detect_host_platform,
    find_project_root,
    normalize_installer_target,
    resolve_platform_script_paths,
)

REPO_ROOT = find_project_root(Path(__file__).resolve())


def _normalize_target(target: str) -> str:
    return normalize_installer_target(target)


def detect_target() -> str:
    return detect_host_platform().installer_target


def _resolve_paths(target: str):
    paths = resolve_platform_script_paths(REPO_ROOT, target=_normalize_target(target))
    if paths.install is None:
        raise RuntimeError(f"Unsupported OS target: {target}")
    return paths


def select_script(target: str) -> Path:
    return _resolve_paths(target).install or Path()


def build_command(target: str, passthrough: list[str]) -> list[str]:
    paths = _resolve_paths(target)
    return paths.command_for("install", passthrough) or [str(paths.install)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the platform-specific HueyOS installer from the repository."
    )
    parser.add_argument(
        "--target",
        choices=["linux", "debian", "macos", "windows"],
        help="Override detected OS target.",
    )
    parser.add_argument(
        "passthrough",
        nargs=argparse.REMAINDER,
        help="Arguments passed directly to the platform installer.",
    )
    args = parser.parse_args()

    target = args.target or detect_target()
    normalized_target = _normalize_target(target)
    if normalized_target == "unknown":
        print(
            "Unsupported OS. Supported targets are Linux, macOS, and Windows. "
            "Use --target to override if appropriate.",
            file=sys.stderr,
        )
        return 1

    script_path = select_script(target)
    if not script_path.exists():
        print(f"Installer script not found: {script_path}", file=sys.stderr)
        return 1

    passthrough = args.passthrough
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    command = build_command(target, passthrough)
    print(f"Detected target: {normalized_target}")
    print(f"Running installer: {' '.join(command)}")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
