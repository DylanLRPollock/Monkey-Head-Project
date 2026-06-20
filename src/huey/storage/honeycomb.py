"""Honeycomb storage core combining cache, clustering, and replication."""

from __future__ import annotations

import json
from typing import Any

from huey.exceptions import StorageError

from .cache import MemoryCache
from .compression import compress_text, decompress_text
from .fault_tolerance import ReplicationPolicy
from .hex_cluster import HexClusterIndex
from .index import StorageIndex


class HoneycombStore:
    """Store structured records in a deterministic in-memory layout."""

    def __init__(self) -> None:
        self.cache = MemoryCache()
        self.index = StorageIndex()
        self.cluster_index = HexClusterIndex()
        self.replication = ReplicationPolicy()
        self._records: dict[str, str] = {}

    def put(
        self,
        key: str,
        value: dict[str, Any],
        *,
        labels: list[str] | None = None,
    ) -> dict[str, object]:
        payload = json.dumps(value, sort_keys=True, default=str)
        compressed = compress_text(payload)
        cluster = self.cluster_index.cluster_for(key)
        self._records[key] = compressed
        self.cache.set(key, value)
        self.index.add(key, labels=labels, cluster=cluster)
        return {
            "key": key,
            "cluster": cluster,
            "replication": self.replication.plan(cluster),
        }

    def get(self, key: str) -> dict[str, Any]:
        cached = self.cache.get(key)
        if isinstance(cached, dict):
            return cached
        compressed = self._records.get(key)
        if compressed is None:
            raise StorageError(f"Unknown storage key: {key}")
        payload = json.loads(decompress_text(compressed))
        self.cache.set(key, payload)
        return payload

    def delete(self, key: str) -> None:
        if key not in self._records:
            raise StorageError(f"Unknown storage key: {key}")
        self._records.pop(key, None)
        self.index.remove(key)
        self.cache.set(key, None, ttl_seconds=0)

    def snapshot(self) -> dict[str, object]:
        return {
            "keys": sorted(self._records),
            "index": self.index.snapshot(),
            "cache": self.cache.snapshot(),
        }


__all__ = ["HoneycombStore"]
