#!/usr/bin/env python3
"""Operator command for huey.media.cli_audio_prepare."""
from __future__ import annotations
import sys
from pathlib import Path
src = Path(__file__).resolve().parents[1] / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))
from huey.media.cli_audio_prepare import main
if __name__ == "__main__":
    raise SystemExit(main())
