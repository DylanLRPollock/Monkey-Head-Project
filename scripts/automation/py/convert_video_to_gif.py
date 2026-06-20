#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

from _dispatch import run_memory_python

if __name__ == "__main__":
    run_memory_python("convert_video_to_gif.py", start_path=_THIS_DIR)
