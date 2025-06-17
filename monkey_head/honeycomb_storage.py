"""Honeycomb style storage system with simple clustering and replication."""

from __future__ import annotations

import os
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List


class HoneycombStorage:
    """Simple fault tolerant storage using hexagonal clusters."""

    def __init__(
        self, base_dir: str | Path = "memory/HONEYCOMB", replicas: int = 2
    ) -> None:
        self.base_dir = Path(base_dir)
        self.replicas = max(1, replicas)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------
    def _cluster_dirs(self, key: str) -> List[Path]:
        """Return cluster directories for a key."""
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        dirs = []
        for i in range(self.replicas):
            cluster = digest[i * 2 : i * 2 + 2]
            path = self.base_dir / f"h{cluster}"
            path.mkdir(parents=True, exist_ok=True)
            dirs.append(path)
        return dirs

    # -------------------------------------------------
    def store(self, key: str, data: Dict[str, Any]) -> None:
        """Store JSON serialisable data under key with replication."""
        for d in self._cluster_dirs(key):
            with open(d / f"{key}.json", "w", encoding="utf-8") as f:
                json.dump(data, f)

    # -------------------------------------------------
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data for key from the first available replica."""
        for d in self._cluster_dirs(key):
            path = d / f"{key}.json"
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    continue
        return None

    # -------------------------------------------------
    def remove(self, key: str) -> None:
        """Remove all replicas for the given key."""
        for d in self._cluster_dirs(key):
            path = d / f"{key}.json"
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass

    # -------------------------------------------------
    def list_keys(self) -> List[str]:
        """Return all stored keys."""
        keys = set()
        for d in self.base_dir.iterdir():
            if not d.is_dir():
                continue
            for f in d.glob("*.json"):
                keys.add(f.stem)
        return sorted(keys)
