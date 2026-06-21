"""Parse FFmpeg silencedetect output into structured silence regions."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable

START_RE = re.compile(r"silence_start:\s*(?P<start>[0-9.]+)")
END_RE = re.compile(
    r"silence_end:\s*(?P<end>[0-9.]+)\s*\|\s*silence_duration:\s*(?P<duration>[0-9.]+)"
)


@dataclass(frozen=True)
class SilenceRegion:
    """A detected silent section in seconds."""

    start_seconds: float
    end_seconds: float | None = None
    duration_seconds: float | None = None

    def to_dict(self) -> dict[str, float | None]:
        """Return a JSON-safe dictionary."""
        return asdict(self)


def parse_silencedetect_lines(lines: Iterable[str]) -> list[SilenceRegion]:
    """Parse lines emitted by FFmpeg's ``silencedetect`` audio filter."""
    regions: list[SilenceRegion] = []
    open_start: float | None = None

    for line in lines:
        start_match = START_RE.search(line)
        if start_match:
            open_start = float(start_match.group("start"))
            continue

        end_match = END_RE.search(line)
        if end_match:
            end = float(end_match.group("end"))
            duration = float(end_match.group("duration"))
            start = open_start if open_start is not None else max(0.0, end - duration)
            regions.append(SilenceRegion(start, end, duration))
            open_start = None

    if open_start is not None:
        regions.append(SilenceRegion(open_start))
    return regions


def parse_silencedetect_text(text: str) -> list[dict[str, float | None]]:
    """Parse FFmpeg stderr text into JSON-safe silence region dictionaries."""
    return [region.to_dict() for region in parse_silencedetect_lines(text.splitlines())]

