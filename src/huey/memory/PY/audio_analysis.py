"""Audio inspection helpers built on ffprobe and FFmpeg analysis filters."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from huey.media.media_manager import FFmpegManager
from huey.media.silence_parser import parse_silencedetect_text

MEAN_VOLUME_RE = re.compile(r"mean_volume:\s*(?P<value>-?[0-9.]+)\s*dB")
MAX_VOLUME_RE = re.compile(r"max_volume:\s*(?P<value>-?[0-9.]+)\s*dB")


@dataclass(frozen=True)
class AudioAnalysis:
    """JSON-safe audio analysis summary."""

    path: str
    duration_seconds: float | None
    bit_rate: int | None
    channels: int | None
    sample_rate_hz: int | None
    mean_volume_db: float | None = None
    max_volume_db: float | None = None
    silence_regions: list[dict[str, float | None]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return a JSON-safe dictionary."""
        return asdict(self)


def analyze_audio(
    source: str | Path, *, manager: FFmpegManager | None = None
) -> AudioAnalysis:
    """Analyze duration, stream basics, volume, and silence regions."""
    media_manager = manager or FFmpegManager()
    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(f"Audio source not found: {source_path}")

    probe = media_manager.probe(source_path)
    audio_stream = next(
        (stream for stream in probe.streams if stream.get("codec_type") == "audio"), {}
    )

    volume_result = media_manager.run(
        [
            media_manager.ffmpeg_bin,
            "-hide_banner",
            "-i",
            str(source_path),
            "-af",
            "volumedetect",
            "-f",
            "null",
            "-",
        ]
    )
    silence_result = media_manager.run(
        [
            media_manager.ffmpeg_bin,
            "-hide_banner",
            "-i",
            str(source_path),
            "-af",
            "silencedetect=noise=-35dB:d=0.5",
            "-f",
            "null",
            "-",
        ]
    )

    return AudioAnalysis(
        path=str(source_path),
        duration_seconds=probe.duration_seconds,
        bit_rate=probe.bit_rate,
        channels=_optional_int(audio_stream.get("channels")),
        sample_rate_hz=_optional_int(audio_stream.get("sample_rate")),
        mean_volume_db=_match_float(MEAN_VOLUME_RE, volume_result.stderr),
        max_volume_db=_match_float(MAX_VOLUME_RE, volume_result.stderr),
        silence_regions=parse_silencedetect_text(silence_result.stderr),
    )


def _match_float(pattern: re.Pattern[str], text: str) -> float | None:
    match = pattern.search(text)
    return float(match.group("value")) if match else None


def _optional_int(value: object) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None
