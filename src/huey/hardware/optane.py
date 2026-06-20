"""Intel Optane style tier management for local caching and swap."""

from __future__ import annotations


class OptaneManager:
    """Track logical Optane-backed tiers."""

    def __init__(self, *, capacity_gb: int = 128) -> None:
        self.capacity_gb = capacity_gb
        self._tiers: dict[str, int] = {}

    def allocate_tier(self, name: str, size_gb: int) -> dict[str, object]:
        self._tiers[name] = size_gb
        return {"name": name, "size_gb": size_gb, "remaining_gb": self.remaining_gb}

    @property
    def remaining_gb(self) -> int:
        return self.capacity_gb - sum(self._tiers.values())

    def snapshot(self) -> dict[str, object]:
        return {"capacity_gb": self.capacity_gb, "tiers": dict(self._tiers)}


__all__ = ["OptaneManager"]
