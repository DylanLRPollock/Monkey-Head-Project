"""Honeycomb-style storage primitives for the speculative runtime."""

from __future__ import annotations

from .cache import MemoryCache
from .compression import compress_text, decompress_text
from .fault_tolerance import ReplicationPolicy
from .hex_cluster import HexClusterIndex
from .honeycomb import HoneycombStore
from .index import StorageIndex

__all__ = [
    "HexClusterIndex",
    "HoneycombStore",
    "MemoryCache",
    "ReplicationPolicy",
    "StorageIndex",
    "compress_text",
    "decompress_text",
]
