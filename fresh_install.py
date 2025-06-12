#!/usr/bin/env python3
"""Run a clean reinstall of the Monkey Head Project."""
from __future__ import annotations

import sys

import installer
import uninstaller


def run_fresh_install() -> int:
    """Remove existing files and perform a new installation."""
    print("Starting fresh installation...")
    uninstall_rc = uninstaller.run_uninstaller()
    if uninstall_rc != 0:
        print(f"Uninstall failed with code {uninstall_rc}")
        return uninstall_rc
    return installer.run_installer()


if __name__ == "__main__":
    sys.exit(run_fresh_install())
