"""In-memory cache used by the honeycomb storage core."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(slots=True)
class CacheEntry:
    value: object
    expires_at: float | None = None


class MemoryCache:
    """Small TTL-capable cache for repeated storage reads."""

    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    def set(self, key: str, value: object, *, ttl_seconds: int | None = None) -> None:
        expires_at = None if ttl_seconds is None else time.time() + ttl_seconds
        self._entries[key] = CacheEntry(value=value, expires_at=expires_at)

    def get(self, key: str) -> object | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at is not None and entry.expires_at < time.time():
            self._entries.pop(key, None)
            return None
        return entry.value

    def snapshot(self) -> dict[str, object]:
        return {
            key: {"value": entry.value, "expires_at": entry.expires_at}
            for key, entry in self._entries.items()
        }


__all__ = ["MemoryCache"]
