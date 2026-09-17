#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.repo.check_stale_platform_strings`."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.repo.check_stale_platform_strings import *  # noqa: F401,F403
from scripts.repo.check_stale_platform_strings import main

if __name__ == "__main__":
    raise SystemExit(main())
