"""Repair utility that reinstalls the project from a repository."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import uninstaller


def run_repair(repo_url: str) -> int:
    result = uninstaller.run_uninstaller()
    if result != 0:
        return result

    with tempfile.TemporaryDirectory() as tmpdir:
        checkout = Path(tmpdir)
        clone = subprocess.run(
            ["git", "clone", repo_url, str(checkout)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if clone.returncode != 0:
            return clone.returncode

        install = subprocess.run([sys.executable, "installer.py"], cwd=str(checkout))
        return install.returncode


__all__ = ["run_repair"]
