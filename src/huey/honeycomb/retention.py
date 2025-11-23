# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Honeycomb Retention module (huey)

"""Retention policy helpers for honeycomb storage."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional

from huey.honeycomb.index import HoneycombIndex
from huey.honeycomb.storage import HoneycombStorage

_DURATION_PATTERN = re.compile(r"^(?P<value>\d+)(?P<unit>[smhdwy])$")
_UNIT_SECONDS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
    "y": 31557600,
}


def parse_duration(value: str) -> float:
    """Convert a symbolic duration (``30d``) into seconds."""

    match = _DURATION_PATTERN.match(value.strip())
    if not match:
        raise ValueError(f"Unsupported retention duration: {value!r}")
    unit = match.group("unit")
    seconds = _UNIT_SECONDS[unit]
    amount = int(match.group("value"))
    return float(amount * seconds)


@dataclass
class RetentionPolicy:
    """Retention settings keyed by content type and comb."""

    content_types: Dict[str, float] = field(default_factory=dict)
    combs: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_config(cls, config: Mapping[str, Mapping[str, str]]) -> "RetentionPolicy":
        content_types: Dict[str, float] = {}
        combs: Dict[str, float] = {}
        for name, value in config.get("content_types", {}).items():
            content_types[name] = parse_duration(value)
        for name, value in config.get("combs", {}).items():
            combs[name] = parse_duration(value)
        return cls(content_types=content_types, combs=combs)

    def to_config(self) -> Dict[str, Dict[str, str]]:
        def _format(entries: Mapping[str, float]) -> Dict[str, str]:
            formatted: Dict[str, str] = {}
            for key, seconds in entries.items():
                formatted[key] = f"{int(seconds)}s"
            return formatted

        return {
            "content_types": _format(self.content_types),
            "combs": _format(self.combs),
        }

    def apply(
        self,
        storage: HoneycombStorage,
        *,
        index: Optional[HoneycombIndex] = None,
        now: Optional[float] = None,
    ) -> Dict[str, int]:
        """Apply the retention rules returning the number of pruned cells per key."""

        now_ts = now if now is not None else time.time()
        removed: Dict[str, int] = {}
        if index is not None:
            for content_type, retention_seconds in self.content_types.items():
                prefixes = list(index.prefixes_for_content_type(content_type))
                cutoff = now_ts - retention_seconds
                for prefix in prefixes:
                    count = storage.prune(prefix, older_than=cutoff)
                    if count:
                        removed[content_type] = removed.get(content_type, 0) + count
        for comb, retention_seconds in self.combs.items():
            cutoff = now_ts - retention_seconds
            prefix = f"{comb}/"
            count = storage.prune(prefix, older_than=cutoff)
            if count:
                removed[comb] = removed.get(comb, 0) + count
        return removed


__all__ = ["RetentionPolicy", "parse_duration"]
