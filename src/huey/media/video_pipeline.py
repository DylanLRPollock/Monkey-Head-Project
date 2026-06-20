"""Video helpers that build on the central FFmpeg media manager."""

from __future__ import annotations

from pathlib import Path

from huey.media.media_manager import (
    _coerce_path,
    _ensure_source,
    _run_ffmpeg,
)
from huey.media.media_manager import extract_frames as _extract_frames
from huey.media.media_manager import (
    probe_media,
)


def extract_frames(
    source: str | Path,
    output_pattern: str | Path,
    *,
    fps: float = 1.0,
) -> Path:
    """Extract video frames to a numbered image sequence."""

    return _extract_frames(source, output_pattern, fps=fps)


def extract_keyframes(
    source: str | Path,
    output_pattern: str | Path,
) -> Path:
    """Extract I-frames from a video."""

    src = _ensure_source(source)
    dst = _coerce_path(output_pattern)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(
        [
            "-i",
            str(src),
            "-vf",
            "select='eq(pict_type,I)'",
            "-vsync",
            "vfr",
            str(dst),
        ]
    )
    return dst


def extract_thumbnail(
    source: str | Path,
    target: str | Path,
    *,
    timestamp: float = 1.0,
) -> Path:
    """Extract a single thumbnail frame."""

    src = _ensure_source(source)
    dst = _coerce_path(target)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(["-ss", str(timestamp), "-i", str(src), "-frames:v", "1", str(dst)])
    return dst


def split_video(
    source: str | Path,
    output_dir: str | Path,
    *,
    chunk_seconds: float = 30.0,
    prefix: str = "segment",
) -> list[Path]:
    """Split a video into fixed-duration segments."""

    src = _ensure_source(source)
    directory = _coerce_path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    pattern = directory / f"{prefix}-%03d.mp4"
    _run_ffmpeg(
        [
            "-i",
            str(src),
            "-c",
            "copy",
            "-map",
            "0",
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            str(pattern),
        ]
    )
    return sorted(directory.glob(f"{prefix}-*.mp4"))


def video_metadata(source: str | Path) -> dict[str, object]:
    """Return full ffprobe metadata for a video file."""

    return probe_media(source).raw


def video_duration(source: str | Path) -> float:
    """Return video duration in seconds."""

    payload = video_metadata(source)
    return float(payload.get("format", {}).get("duration", 0.0))


def video_fps(source: str | Path) -> float:
    """Return the primary video stream frames-per-second value."""

    payload = video_metadata(source)
    for stream in payload.get("streams", []):
        if stream.get("codec_type") != "video":
            continue
        raw_value = str(stream.get("r_frame_rate") or "0/1")
        numerator, _, denominator = raw_value.partition("/")
        if denominator and float(denominator) != 0:
            return float(numerator) / float(denominator)
        return float(numerator)
    return 0.0


__all__ = [
    "extract_frames",
    "extract_keyframes",
    "extract_thumbnail",
    "split_video",
    "video_duration",
    "video_fps",
    "video_metadata",
]
