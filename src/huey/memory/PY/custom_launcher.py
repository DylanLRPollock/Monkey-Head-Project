# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Custom Launcher module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Example launcher that starts the project in CLI mode."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from huey.os.core.platform_support import find_project_root


def main() -> int:
    root = find_project_root(Path(__file__).resolve())
    runner = root / "run.py"
    if runner.is_symlink() or not runner.is_file():
        raise FileNotFoundError(f"Project runner not found: {runner}")
    return subprocess.call(
        [sys.executable, str(runner.resolve()), "--cli"], cwd=root, shell=False
    )


if __name__ == "__main__":  # pragma: no cover - example script
    raise SystemExit(main())
