#!/usr/bin/env python3
"""Repair the Monkey Head Project by reinstalling from a fresh clone."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import installer
import uninstaller

REPO_URL = "https://github.com/DylanLRPollock/Monkey-Head-Project.git"


def run_repair(repo_url: str = REPO_URL) -> int:
    """Clone the repository and run a fresh installation."""
    print("Starting repair procedure...")

    uninstall_rc = uninstaller.run_uninstaller()
    if uninstall_rc != 0:
        print(f"Uninstall failed with code {uninstall_rc}")
        return uninstall_rc

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Cloning repository from {repo_url}...")
        clone = subprocess.run(
            [
                "git",
                "clone",
                repo_url,
                tmpdir,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if clone.returncode != 0:
            sys.stderr.write(clone.stderr.decode())
            return clone.returncode

        print("Running installer from fresh clone...")
        rc = subprocess.run(
            [
                sys.executable,
                "installer.py",
            ],
            cwd=tmpdir,
        ).returncode
        if rc != 0:
            print(f"Installer failed with code {rc}")
        return rc


if __name__ == "__main__":
    sys.exit(run_repair())
