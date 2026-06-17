#!/usr/bin/env python3
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Uninstaller module (huey/memory/PY)

"""Cross-platform uninstaller for the Monkey Head Project."""

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
WINDOWS_UNINSTALL = os.path.join(SCRIPT_DIR, "setup", "Windows11", "03-CLEANUP.bat")


def run_uninstaller() -> int:
    system = platform.system()
    try:
        if system == "Linux":
            subprocess.run(["bash", LINUX_UNINSTALL], check=True)
        elif system == "Darwin":
            subprocess.run(["bash", MAC_UNINSTALL], check=True)
        elif system == "Windows":
            subprocess.run(["cmd", "/c", WINDOWS_UNINSTALL], check=True)
        else:
            print(f"Unsupported operating system: {system}")
            return 1
    except subprocess.CalledProcessError as exc:
        print(f"Uninstaller failed with return code {exc.returncode}")
        return exc.returncode
    return 0


if __name__ == "__main__":
    sys.exit(run_uninstaller())
