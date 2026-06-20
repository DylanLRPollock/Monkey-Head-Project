"""Retention helpers for Honeycomb storage."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Optional

_DURATION_RE = re.compile(r"^\s*(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>[smhdwMy]?)\s*$")


def parse_duration(value: str | int | float | None) -> Optional[float]:
    """Parse a retention duration into seconds.

    Supported suffixes:
    s = seconds, m = minutes, h = hours, d = days, w = weeks,
    M = 30-day months, y = 365-day years.

    ``None`` or an empty string means no retention limit.
    """

    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    match = _DURATION_RE.match(text)
    if not match:
        raise ValueError(f"invalid duration: {value!r}")

    number = float(match.group("value"))
    unit = match.group("unit") or "s"

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 60 * 60,
        "d": 60 * 60 * 24,
        "w": 60 * 60 * 24 * 7,
        "M": 60 * 60 * 24 * 30,
        "y": 60 * 60 * 24 * 365,
    }

    return number * multipliers[unit]


@dataclass(frozen=True)
class RetentionPolicy:
    """Simple age-based retention policy."""

    max_age: str | int | float | None = None

    @property
    def max_age_seconds(self) -> Optional[float]:
        return parse_duration(self.max_age)

    def should_retain(self, timestamp: float, *, now: float | None = None) -> bool:
        limit = self.max_age_seconds
        if limit is None:
            return True
        current = time.time() if now is None else now
        return (current - float(timestamp)) <= limit

    def should_prune(self, timestamp: float, *, now: float | None = None) -> bool:
        return not self.should_retain(timestamp, now=now)


__all__ = ["RetentionPolicy", "parse_duration"]
