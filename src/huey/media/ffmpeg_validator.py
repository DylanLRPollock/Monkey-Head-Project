"""Startup validation helpers for FFmpeg-dependent features."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class FFmpegValidationReport:
    """Structured FFmpeg readiness report used by legacy and canonical callers."""

    available: bool
    ffmpeg_version: str | None = None
    ffprobe_version: str | None = None
    errors: list[str] = field(default_factory=list)
    ffprobe_available: bool | None = None
    required_filters: dict[str, bool] = field(default_factory=dict)
    v1_ready: bool | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def ffmpeg_available(self) -> bool:
        """Return whether FFmpeg is available."""

        return self.available

    def __bool__(self) -> bool:
        return self.available

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe dictionary."""

        payload = asdict(self)
        payload["ready"] = self.ready
        return payload

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe dictionary."""

        return self.to_dict()

    def to_json(self) -> str:
        """Return pretty JSON for CLI output."""

        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @property
    def ready(self) -> bool:
        """Return the broad readiness state for the current report."""

        if self.v1_ready is not None:
            return self.v1_ready
        if self.ffprobe_available is None:
            return self.available
        return self.available and self.ffprobe_available


def _which(binary: str) -> str | None:
    return shutil.which(binary)


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


def check_ffmpeg(*, ffmpeg_bin: str = "ffmpeg") -> FFmpegValidationReport:
    """Return a structured FFmpeg availability report."""

    available = _which(ffmpeg_bin) is not None
    errors: list[str] = []
    if not available:
        errors.append(f"{ffmpeg_bin} not found on PATH")
    return FFmpegValidationReport(
        available=available,
        ffmpeg_version=_version_line(ffmpeg_bin) if available else None,
        errors=errors,
    )


def check_ffprobe(*, ffprobe_bin: str = "ffprobe") -> bool:
    """Return ``True`` when ``ffprobe`` is visible on ``PATH``."""

    return _which(ffprobe_bin) is not None


def get_ffmpeg_version(*, ffmpeg_bin: str = "ffmpeg") -> str | None:
    """Return the installed FFmpeg version string if available."""

    report = check_ffmpeg(ffmpeg_bin=ffmpeg_bin)
    return report.ffmpeg_version


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
    """Return a detailed readiness report for the media stack."""

    ffmpeg_report = check_ffmpeg(ffmpeg_bin=ffmpeg_bin)
    ffprobe_available = check_ffprobe(ffprobe_bin=ffprobe_bin)
    ffprobe_version = _version_line(ffprobe_bin) if ffprobe_available else None
    errors = list(ffmpeg_report.errors)
    notes = list(ffmpeg_report.errors)
    filters: dict[str, bool] = {name: False for name in required_filters}

    if not ffprobe_available:
        message = f"{ffprobe_bin} not found on PATH"
        errors.append(message)
        notes.append(message)

    if ffmpeg_report.available:
        filter_output = _command_stdout([ffmpeg_bin, "-hide_banner", "-filters"])
        for name in required_filters:
            filters[name] = name in filter_output
            if not filters[name]:
                message = f"Missing FFmpeg filter: {name}"
                errors.append(message)
                notes.append(message)

    v1_ready = ffmpeg_report.available and ffprobe_available and all(filters.values())
    if v1_ready:
        notes.append("FFmpeg environment is ready for V1 audio preparation.")

    return FFmpegValidationReport(
        available=ffmpeg_report.available,
        ffmpeg_version=ffmpeg_report.ffmpeg_version,
        ffprobe_version=ffprobe_version,
        errors=errors,
        ffprobe_available=ffprobe_available,
        required_filters=filters,
        v1_ready=v1_ready,
        notes=notes,
    )


def validate_media_environment() -> dict[str, object]:
    """Return a compact snapshot of FFmpeg/ffprobe readiness."""

    report = validate_ffmpeg_environment()
    return {
        "ffmpeg": report.available,
        "ffprobe": bool(report.ffprobe_available),
        "ffmpeg_version": report.ffmpeg_version,
        "ffprobe_version": report.ffprobe_version,
        "ready": report.ready,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description="Check FFmpeg availability.")
    parser.add_argument(
        "--json", action="store_true", help="Print machine-readable JSON."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when FFmpeg is unavailable.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the FFmpeg availability check."""

    args = build_parser().parse_args(argv)
    report = check_ffmpeg()
    if args.json:
        print(report.to_json())
    else:
        status = "available" if report.available else "unavailable"
        print(f"FFmpeg is {status}.")
        for error in report.errors:
            print(f"- {error}")
    if args.strict and not report.available:
        return 1
    return 0


__all__ = [
    "FFmpegValidationReport",
    "check_ffmpeg",
    "check_ffprobe",
    "get_ffmpeg_version",
    "main",
    "validate_ffmpeg_environment",
    "validate_media_environment",
]
