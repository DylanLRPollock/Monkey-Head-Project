#!/usr/bin/env python3
"""Compatibility wrapper for :mod:`scripts.media.decompress_audio_to_flac`."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.media.decompress_audio_to_flac import *  # noqa: F401,F403
from scripts.media.decompress_audio_to_flac import main

if __name__ == "__main__":
    main()
