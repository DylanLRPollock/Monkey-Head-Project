"""Audio inspection helpers built on top of the FFmpeg media subsystem."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from huey.media.ffmpeg_validator import check_ffmpeg
from huey.media.media_manager import detect_silence, probe_media


def _audio_stream(source: str | Path) -> dict[str, object]:
    payload = probe_media(source).raw
    for stream in payload.get("streams", []):
        if stream.get("codec_type") == "audio":
            return dict(stream)
    return {}


def duration(source: str | Path) -> float:
    """Return audio duration in seconds."""

    payload = probe_media(source).raw
    return float(payload.get("format", {}).get("duration", 0.0))


def bitrate(source: str | Path) -> int:
    """Return audio bitrate in bits per second."""

    stream = _audio_stream(source)
    raw_value = stream.get("bit_rate") or probe_media(source).raw.get("format", {}).get(
        "bit_rate", 0
    )
    return int(float(raw_value or 0))


def sample_rate(source: str | Path) -> int:
    """Return audio sample rate."""

    return int(float(_audio_stream(source).get("sample_rate", 0)))


def channels(source: str | Path) -> int:
    """Return the number of audio channels."""

    return int(_audio_stream(source).get("channels", 0))


def _volumedetect(source: str | Path) -> dict[str, float]:
    if not check_ffmpeg():
        raise RuntimeError("ffmpeg is not available on PATH")
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(Path(source).expanduser().resolve()),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    mean_match = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", result.stderr or "")
    peak_match = re.search(r"max_volume:\s*(-?[0-9.]+) dB", result.stderr or "")
    return {
        "mean_volume": float(mean_match.group(1)) if mean_match else 0.0,
        "max_volume": float(peak_match.group(1)) if peak_match else 0.0,
    }


def peak_level(source: str | Path) -> float:
    """Return the detected peak level in dB."""

    return _volumedetect(source)["max_volume"]


def rms_level(source: str | Path) -> float:
    """Return the mean/RMS volume in dB."""

    return _volumedetect(source)["mean_volume"]


def silence_map(source: str | Path) -> list[dict[str, float]]:
    """Return silence segments detected in the audio."""

    return detect_silence(source)


__all__ = [
    "bitrate",
    "channels",
    "duration",
    "peak_level",
    "rms_level",
    "sample_rate",
    "silence_map",
]
