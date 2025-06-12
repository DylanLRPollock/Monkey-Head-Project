# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Media conversion utilities using FFmpeg."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

__all__ = [
    "convert_audio",
    "convert_video",
    "convert_file",
]


def _run_ffmpeg(args: list[str]) -> None:
    """Run an ffmpeg command and raise if it fails."""
    cmd = ["ffmpeg", "-y"] + args
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", "ignore"))


def convert_audio(src: str, dst: str, bitrate: str = "192k") -> None:
    """Convert an audio file to a new format using ffmpeg."""
    _run_ffmpeg(["-i", src, "-b:a", bitrate, dst])


def convert_video(src: str, dst: str, codec: str = "libx264") -> None:
    """Convert a video file to a new format using ffmpeg."""
    _run_ffmpeg(["-i", src, "-vcodec", codec, dst])


def convert_file(src: str, dst: str) -> None:
    """Generic file conversion by copying to a new path."""
    shutil.copyfile(src, dst)
