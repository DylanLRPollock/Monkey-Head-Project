"""Validate local FFmpeg readiness for the HueyOS V1 proof path."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class FFmpegValidationReport:
    """JSON-safe FFmpeg environment validation report."""

    ffmpeg_available: bool
    ffprobe_available: bool
    ffmpeg_version: str | None = None
    ffprobe_version: str | None = None
    required_filters: dict[str, bool] = field(default_factory=dict)
    v1_ready: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return the report as a JSON-safe dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Return pretty JSON for CLI output."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def validate_ffmpeg_environment(
    *,
    ffmpeg_bin: str = "ffmpeg",
    ffprobe_bin: str = "ffprobe",
    required_filters: Sequence[str] = (
        "loudnorm",
        "silencedetect",
        "showwavespic",
        "showspectrumpic",
    ),
) -> FFmpegValidationReport:
    """Check binaries and filters needed for Phase 1 media work."""
    ffmpeg_available = shutil.which(ffmpeg_bin) is not None
    ffprobe_available = shutil.which(ffprobe_bin) is not None
    notes: list[str] = []
    filters: dict[str, bool] = {name: False for name in required_filters}

    ffmpeg_version = _version_line(ffmpeg_bin) if ffmpeg_available else None
    ffprobe_version = _version_line(ffprobe_bin) if ffprobe_available else None

    if not ffmpeg_available:
        notes.append(f"Missing FFmpeg binary: {ffmpeg_bin}")
    if not ffprobe_available:
        notes.append(f"Missing ffprobe binary: {ffprobe_bin}")

    if ffmpeg_available:
        filter_output = _command_stdout([ffmpeg_bin, "-hide_banner", "-filters"])
        for name in required_filters:
            filters[name] = name in filter_output
            if not filters[name]:
                notes.append(f"Missing FFmpeg filter: {name}")

    v1_ready = ffmpeg_available and ffprobe_available and all(filters.values())
    if v1_ready:
        notes.append("FFmpeg environment is ready for V1 audio preparation.")

    return FFmpegValidationReport(
        ffmpeg_available=ffmpeg_available,
        ffprobe_available=ffprobe_available,
        ffmpeg_version=ffmpeg_version,
        ffprobe_version=ffprobe_version,
        required_filters=filters,
        v1_ready=v1_ready,
        notes=notes,
    )


def _version_line(binary: str) -> str | None:
    output = _command_stdout([binary, "-version"])
    return output.splitlines()[0] if output else None


def _command_stdout(command: Sequence[str]) -> str:
    completed = subprocess.run(
        list(command),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout or ""
