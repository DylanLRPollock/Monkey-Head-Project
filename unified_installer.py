#!/usr/bin/env python3
"""Unified installer for HueyOS setup scripts."""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SETUP_ROOT = REPO_ROOT / "setup"


def _read_os_release() -> dict[str, str]:
    os_release = {}
    os_release_path = Path("/etc/os-release")
    if not os_release_path.exists():
        return os_release
    for line in os_release_path.read_text(encoding="utf-8").splitlines():
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os_release[key.strip()] = value.strip().strip('"')
    return os_release


def detect_target() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    if system == "linux":
        os_release = _read_os_release()
        os_id = os_release.get("ID", "").lower()
        id_like = os_release.get("ID_LIKE", "").lower()
        if os_id == "debian" or "debian" in id_like:
            return "debian"
        return "linux"
    return "unknown"


def select_script(target: str) -> Path:
    if target == "windows":
        return SETUP_ROOT / "Windows" / "install-win.ps1"
    if target == "macos":
        return SETUP_ROOT / "macOS" / "install-mac.sh"
    if target == "debian":
        return SETUP_ROOT / "Debian" / "install-deb.sh"
    raise RuntimeError(f"Unsupported OS target: {target}")


def build_command(target: str, script_path: Path, passthrough: list[str]) -> list[str]:
    if target == "windows":
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if script_path.suffix.lower() == ".ps1" and powershell:
            return [
                powershell,
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                *passthrough,
            ]
        bat_script = SETUP_ROOT / "Windows" / "install-win.bat"
        return ["cmd", "/c", str(bat_script), *passthrough]
    return ["bash", str(script_path), *passthrough]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the platform-specific HueyOS installer from setup/."
    )
    parser.add_argument(
        "--target",
        choices=["debian", "macos", "windows"],
        help="Override detected OS target.",
    )
    parser.add_argument(
        "passthrough",
        nargs=argparse.REMAINDER,
        help="Arguments passed directly to the platform installer.",
    )
    args = parser.parse_args()

    target = args.target or detect_target()
    if target in {"linux", "unknown"}:
        print(
            "Unsupported OS. Supported targets are Debian, macOS, and Windows. "
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

    command = build_command(target, script_path, passthrough)
    print(f"Detected target: {target}")
    print(f"Running installer: {' '.join(command)}")

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
