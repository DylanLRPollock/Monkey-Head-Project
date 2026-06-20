#!/usr/bin/env python3
"""Launch the HueyOS Command Center backend."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from huey.apps.command_center.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
