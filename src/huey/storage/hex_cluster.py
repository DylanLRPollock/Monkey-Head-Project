"""Hexagonal clustering helpers for the honeycomb storage layout."""

from __future__ import annotations

from hashlib import sha1


class HexClusterIndex:
    """Derive stable cluster IDs from logical keys."""

    def __init__(self, *, width: int = 3) -> None:
        self.width = width

    def cluster_for(self, key: str) -> str:
        return sha1(key.encode("utf-8")).hexdigest()[: self.width]


__all__ = ["HexClusterIndex"]
