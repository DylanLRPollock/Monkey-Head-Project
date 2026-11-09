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
from huey.os.core.privileged_operations import authorize_privileged_operation

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


def _authorization_result(args: argparse.Namespace) -> int | None:
    try:
        authorized = authorize_privileged_operation(
            "project.install",
            confirmed=args.yes,
            actor_role="operator" if args.yes else None,
            dry_run=args.dry_run,
        )
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not authorized:
        print("[dry-run] Install authorization preview; no host access.")
        return 0
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the platform-specific HueyOS installer from the repository."
    )
    parser.add_argument(
        "--target",
        choices=["linux", "debian", "macos", "windows"],
        help="Override detected OS target.",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Confirm the installation operation."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without accessing the host."
    )
    parser.add_argument(
        "passthrough",
        nargs=argparse.REMAINDER,
        help="Arguments passed directly to the platform installer.",
    )
    args = parser.parse_args(argv)

    authorization_result = _authorization_result(args)
    if authorization_result is not None:
        return authorization_result

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
    if script_path.is_symlink() or not script_path.is_file():
        print(f"Installer script not found: {script_path}", file=sys.stderr)
        return 1
    root = REPO_ROOT.resolve()
    script = script_path.resolve()
    if not script.is_relative_to(root):
        print("Installer script must be inside the project directory.", file=sys.stderr)
        return 2

    passthrough = args.passthrough
    if passthrough and passthrough[0] == "--":
        passthrough = passthrough[1:]

    command = build_command(target, passthrough)
    print(f"Detected target: {normalized_target}")
    print(f"Running installer: {' '.join(command)}")

    try:
        subprocess.run(command, check=True, shell=False, timeout=1200, cwd=root)
    except subprocess.TimeoutExpired:
        print("Installer timed out.", file=sys.stderr)
        return 124
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
