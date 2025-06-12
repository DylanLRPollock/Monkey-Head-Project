# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
import os
import platform
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Hardware selection options for manual installation
HARDWARE_OPTIONS = [
    "SuperMicro X9 qri-f+",
    "MacBook Pro 2019",
    "iMac 5K 2017",
    "Raspberry Pi 3 B+",
    "Raspberry Pi 4",
    "HP Compaq 8200 Elite",
    "Lenovo Legion Go",
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

LINUX_INSTALL = os.path.join(SCRIPT_DIR, "setup", "Debian13", "install.sh")
MAC_INSTALL = os.path.join(SCRIPT_DIR, "setup", "macOS", "install.sh")
WINDOWS_INSTALL = os.path.join(SCRIPT_DIR, "setup", "Windows11", "01-FULL.bat")


def update_submodules() -> None:
    """Ensure git submodules are initialized."""
    try:
        subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"], check=True
        )
    except subprocess.CalledProcessError as exc:
        print(f"Failed to update submodules: {exc.returncode}")
        raise


def run_installer():
    system = platform.system()
    hardware = select_hardware()
    env = os.environ.copy()
    env["MHP_HARDWARE"] = hardware
    try:
        update_submodules()
        if system == "Linux":
            subprocess.run(["bash", LINUX_INSTALL], check=True, env=env)
        elif system == "Darwin":
            subprocess.run(["bash", MAC_INSTALL], check=True, env=env)
        elif system == "Windows":
            subprocess.run(["cmd", "/c", WINDOWS_INSTALL], check=True, env=env)
        else:
            print(f"Unsupported operating system: {system}")
            return 1
    except subprocess.CalledProcessError as exc:
        print(f"Installer failed with return code {exc.returncode}")
        return exc.returncode
    print(
        "\nThank you for supporting the Monkey Head Project!\n"
        "We hope you enjoy using it."
    )
    return 0


if __name__ == "__main__":
    sys.exit(run_installer())
