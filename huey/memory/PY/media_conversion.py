# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Media Conversion module (huey/memory/PY)

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
import os

__all__ = [
    "convert_audio",
    "convert_video",
    "convert_file",
    "extract_audio",
    "convert_media",
]


def _run_ffmpeg(args: list[str]) -> None:
    """Run an ffmpeg command and raise if it fails."""
    cmd = ["ffmpeg", "-y"] + args
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", "ignore"))


def convert_audio(src: str, dst: str, bitrate: str = "192k") -> None:
    """Convert an audio file to a new format using ffmpeg."""
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    _run_ffmpeg(["-i", src, "-b:a", bitrate, dst])


def convert_video(src: str, dst: str, codec: str = "libx264") -> None:
    """Convert a video file to a new format using ffmpeg."""
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    _run_ffmpeg(["-i", src, "-vcodec", codec, dst])


def convert_file(src: str, dst: str) -> None:
    """Generic file conversion by copying to a new path."""
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    shutil.copyfile(src, dst)


def extract_audio(src: str, dst: str) -> None:
    """Extract the audio track from a video file."""
    if not os.path.exists(src):
        raise FileNotFoundError(src)
    ext = Path(dst).suffix.lower()
    if ext == ".mp3":
        _run_ffmpeg(["-i", src, "-vn", "-acodec", "libmp3lame", dst])
    else:
        _run_ffmpeg(["-i", src, "-vn", "-acodec", "copy", dst])


AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}


def convert_media(
    src: str,
    dst: str,
    *,
    bitrate: str = "192k",
    codec: str = "libx264",
) -> None:
    """Convert an audio or video file, falling back to copy.

    Parameters
    ----------
    src : str
        Path to the input file.
    dst : str
        Path to the output file.
    bitrate : str, optional
        Audio bitrate used for audio conversion.
    codec : str, optional
        Video codec used for video conversion.
    """

    if not os.path.exists(src):
        raise FileNotFoundError(src)

    src_ext = Path(src).suffix.lower()
    dst_ext = Path(dst).suffix.lower()

    if src_ext in VIDEO_EXTENSIONS and dst_ext in AUDIO_EXTENSIONS:
        extract_audio(src, dst)
    elif src_ext in AUDIO_EXTENSIONS:
        convert_audio(src, dst, bitrate=bitrate)
    elif src_ext in VIDEO_EXTENSIONS:
        if dst_ext == ".gif":
            from .convert_video_to_gif import convert_video_to_gif  # local import
            convert_video_to_gif(src, dst)
        else:
            convert_video(src, dst, codec=codec)
    elif src_ext in IMAGE_EXTENSIONS and dst_ext in IMAGE_EXTENSIONS:
        shutil.copyfile(src, dst)
    else:
        convert_file(src, dst)
