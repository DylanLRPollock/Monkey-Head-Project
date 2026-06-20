"""Startup validation helpers for FFmpeg-dependent features."""

from __future__ import annotations

import shutil
import subprocess


def check_ffmpeg() -> bool:
    """Return ``True`` when ``ffmpeg`` is visible on ``PATH``."""

    return shutil.which("ffmpeg") is not None


def check_ffprobe() -> bool:
    """Return ``True`` when ``ffprobe`` is visible on ``PATH``."""

    return shutil.which("ffprobe") is not None


def get_ffmpeg_version() -> str | None:
    """Return the installed FFmpeg version string if available."""

    if not check_ffmpeg():
        return None
    result = subprocess.run(
        ["ffmpeg", "-version"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout:
        return None
    return result.stdout.splitlines()[0].strip()


def validate_media_environment() -> dict[str, object]:
    """Return a snapshot of FFmpeg/ffprobe readiness."""

    ffmpeg_ready = check_ffmpeg()
    ffprobe_ready = check_ffprobe()
    return {
        "ffmpeg": ffmpeg_ready,
        "ffprobe": ffprobe_ready,
        "ffmpeg_version": get_ffmpeg_version(),
        "ready": ffmpeg_ready and ffprobe_ready,
    }


__all__ = [
    "check_ffmpeg",
    "check_ffprobe",
    "get_ffmpeg_version",
    "validate_media_environment",
]
