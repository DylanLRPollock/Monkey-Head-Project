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


def main() -> int:
    cmd = [sys.executable, "../run.py", "--cli"]
    return subprocess.call(cmd)


if __name__ == "__main__":  # pragma: no cover - example script
    raise SystemExit(main())

