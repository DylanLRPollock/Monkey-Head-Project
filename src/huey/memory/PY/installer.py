# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Installer module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import argparse
import os
import subprocess
import sys
from pathlib import Path

from huey.os.core.platform_support import (
    build_platform_script_command,
    find_project_root,
    resolve_platform_script_paths,
)
from huey.os.core.system_checks import ensure_admin
from huey.os.license_cli import show_license_cli
from huey.os.license_gui import show_license_gui

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = find_project_root(Path(__file__).resolve())

# Hardware selection options for manual installation
HARDWARE_OPTIONS = [
    "SuperMicro X9 qri-f+",
    "MacBook Pro 2019",
    "iMac 5K 2017",
    "Raspberry Pi 3 B+",
    "Raspberry Pi 4",
    "HP Compaq 8200 Elite",
    "Lenovo Legion Go",
    "Framework Laptop 13",
    "Dell XPS 15",
]

# Software package options for manual selection
SOFTWARE_OPTIONS = [
    "git",
    "nodejs",
    "python3",
    "python3-venv",
    "docker.io",
    "ffmpeg",
    "tmux",
]


def select_hardware() -> str:
    """Prompt user to select hardware configuration."""
    print("Select installation mode:")
    print("1) auto - general hardware installation")
    print("2) manual - select hardware from list")
    mode = input("Enter choice [1/2]: ").strip()
    if mode == "2":
        print("Available hardware options:")
        for idx, option in enumerate(HARDWARE_OPTIONS, start=1):
            print(f"{idx}) {option}")
        selection = input("Enter hardware number: ").strip()
        try:
            hardware = HARDWARE_OPTIONS[int(selection) - 1]
        except (ValueError, IndexError):
            print("Invalid choice. Using general hardware configuration.")
            hardware = "general"
    else:
        hardware = "general"

    config_dir = os.path.join(SCRIPT_DIR, "config")
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, "hardware.txt"), "w", encoding="utf-8") as fh:
        fh.write(hardware + "\n")

    return hardware


def select_software() -> str:
    """Prompt user to select software packages."""
    print("Select software installation:")
    print("1) auto - install all default packages")
    print("2) manual - choose packages to install")
    mode = input("Enter choice [1/2]: ").strip()
    if mode == "2":
        print("Available packages:")
        for idx, pkg in enumerate(SOFTWARE_OPTIONS, start=1):
            print(f"{idx}) {pkg}")
        selection = input("Enter package numbers separated by spaces: ").strip()
        packages: list[str] = []
        for num in selection.split():
            try:
                packages.append(SOFTWARE_OPTIONS[int(num) - 1])
            except (ValueError, IndexError):
                print(f"Invalid selection: {num}")
        software = " ".join(packages) if packages else "auto"
    else:
        software = "auto"

    config_dir = os.path.join(SCRIPT_DIR, "config")
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, "software.txt"), "w", encoding="utf-8") as fh:
        fh.write(software + "\n")

    return software


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for non-interactive installs."""
    parser = argparse.ArgumentParser(description="Install Monkey Head Project")
    parser.add_argument("--hardware", help="Hardware preset name")
    parser.add_argument(
        "--software",
        nargs="+",
        help="Packages to install or 'auto' for defaults",
    )
    return parser.parse_args(argv)


def ensure_admin_privileges() -> None:
    """Verify the script is running with administrator rights."""
    if os.name == "nt":
        try:
            import ctypes

            if not ctypes.windll.shell32.IsUserAnAdmin():
                raise PermissionError
        except Exception:
            print("Administrator privileges required.")
            raise PermissionError("Please run as Administrator")
    else:
        ensure_admin()


def display_license() -> None:
    """Show the license agreement using GUI or CLI."""
    try:
        show_license_gui()
    except Exception:
        show_license_cli()

def update_submodules() -> None:
    """Ensure git submodules are initialized."""
    sync_script = (
        PROJECT_ROOT / "src" / "huey" / "memory" / "PY" / "sync_pygpt_structure.py"
    )
    try:
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"], check=True
        )
        subprocess.run([sys.executable, str(sync_script)], check=True, cwd=PROJECT_ROOT)
    except subprocess.CalledProcessError as exc:
        print(f"Failed to update submodules: {exc.returncode}")
        raise


def run_installer(
    hardware: str | None = None, software: list[str] | None = None
) -> int:
    if hardware is None:
        hardware = select_hardware()
    if software is None:
        software_choice = select_software()
    else:
        software_choice = "auto" if software == ["auto"] else " ".join(software)
    env = os.environ.copy()
    env["MHP_HARDWARE"] = hardware
    env["MHP_SOFTWARE"] = software_choice
    paths = resolve_platform_script_paths(PROJECT_ROOT)
    script_path = paths.install
    if script_path is None:
        print(f"Unsupported operating system: {paths.host.system}")
        return 1
    if not script_path.exists():
        print(f"Installer script not found: {script_path}")
        return 1

    try:
        ensure_admin_privileges()
        update_submodules()
        display_license()
        subprocess.run(
            build_platform_script_command(script_path),
            check=True,
            env=env,
            cwd=PROJECT_ROOT,
        )
    except subprocess.CalledProcessError as exc:
        print(f"Installer failed with return code {exc.returncode}")
        return exc.returncode
    print(
        "\nThank you for supporting the Monkey Head Project!\n"
        "We hope you enjoy using it."
    )
    return 0


if __name__ == "__main__":
    arguments = parse_args()
    sys.exit(run_installer(arguments.hardware, arguments.software))
