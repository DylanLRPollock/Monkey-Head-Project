# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Honeycomb Storage module (src/hueyos)

"""File-backed honeycomb storage for structured agent memory."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class HoneycombRecord:
    """Represents a single payload stored inside the honeycomb."""

    key: str
    data: Any
    created_at: float
    updated_at: float


class HoneycombStorage:
    """Simple JSON file backed storage arranged using comb/cell keys.

    Each record is stored on disk as ``<base_dir>/<comb>/<cell>.json``. The JSON
    payload contains the record metadata (key, created/updated timestamps) along
    with the user supplied data. While the layout favours readability over raw
    performance it is perfectly adequate for the relatively small memory volumes
    handled by HueyOS agents and keeps the implementation dependency free.

    Parameters
    ----------
    base_dir:
        Directory where comb folders and cell files are created. When ``None``
        the path ``memory/LOGS/honeycomb`` underneath the project is used.
    record_extension:
        Optional suffix appended to generated cell filenames. Defaults to
        ``".json"``.
    """

    def __init__(
        self,
        base_dir: Optional[Path | str] = None,
        *,
        record_extension: str = ".json",
    ) -> None:
        if base_dir is None:
            base_dir = self._default_base_dir()
        else:
            base_dir = Path(base_dir)
            base_dir.mkdir(parents=True, exist_ok=True)
        self._base_dir = Path(base_dir)
        self._extension = record_extension
        self._lock = threading.RLock()
        self._closed = False

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Mark the storage as closed to prevent further writes."""

        with self._lock:
            self._closed = True

    def __enter__(self) -> "HoneycombStorage":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - passthrough
        self.close()

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("HoneycombStorage has been closed")

    @staticmethod
    def _default_base_dir() -> Path:
        root = Path(__file__).resolve().parents[2]
        env_value = os.environ.get("MEMORY_PATH")
        if env_value:
            base = Path(os.path.expanduser(env_value)).resolve()
        else:
            preferred = (root / "memory").resolve()
            if preferred.exists():
                base = preferred
            else:
                packaged = (root / "src" / "huey" / "memory").resolve()
                base = packaged if packaged.exists() else preferred
        target = base / "LOGS" / "honeycomb"
        target.mkdir(parents=True, exist_ok=True)
        return target

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _split_key(key: str) -> tuple[str, str]:
        if not isinstance(key, str):
            raise TypeError("Honeycomb keys must be strings")
        if not key or key.strip() == "":
            raise ValueError("Honeycomb keys must not be empty")
        if "/" in key:
            comb, cell = key.split("/", 1)
        else:
            comb, cell = "default", key
        if not comb:
            raise ValueError("Comb portion of key must not be empty")
        return comb, cell

    def _record_path(self, key: str) -> Path:
        comb, cell = self._split_key(key)
        cell_parts = [part for part in cell.split("/") if part]
        if not cell_parts:
            raise ValueError("Cell portion of key must not be empty")
        filename = cell_parts[-1]
        if not filename.endswith(self._extension):
            filename = f"{filename}{self._extension}"
        cell_parts[-1] = filename
        return self._base_dir.joinpath(comb, *cell_parts)

    def _key_from_path(self, path: Path) -> str:
        relative = path.relative_to(self._base_dir)
        parts = list(relative.parts)
        if len(parts) < 2:
            raise ValueError(f"Invalid record path: {path!s}")
        comb = parts[0]
        cell_parts = list(parts[1:])
        if cell_parts:
            last = cell_parts[-1]
            if last.endswith(self._extension):
                last = last[: -len(self._extension)]
            cell_parts[-1] = last
        cell = "/".join(cell_parts)
        return f"{comb}/{cell}" if cell else comb

    def _iter_record_paths(self) -> Iterator[Path]:
        if not self._base_dir.exists():
            return
        for path in self._base_dir.rglob(f"*{self._extension}"):
            if path.is_file():
                yield path

    def _iter_records(self) -> Iterator[HoneycombRecord]:
        for path in self._iter_record_paths():
            record = self._read_record(path)
            if record is not None:
                yield record

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------
    def _read_record(self, path: Path) -> Optional[HoneycombRecord]:
        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except FileNotFoundError:
            return None
        key = payload.get("key") or self._key_from_path(path)
        created_at = float(payload.get("created_at", time.time()))
        updated_at = float(payload.get("updated_at", created_at))
        data = payload.get("data")
        return HoneycombRecord(
            key=key, data=data, created_at=created_at, updated_at=updated_at
        )

    def _write_record(self, path: Path, record: HoneycombRecord) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "key": record.key,
            "data": record.data,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
        tmp_path = path.with_suffix(f"{path.suffix}.tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        tmp_path.replace(path)

    # ------------------------------------------------------------------
    # Core storage API
    # ------------------------------------------------------------------
    def store(self, key: str, data: Any) -> HoneycombRecord:
        self._ensure_open()
        path = self._record_path(key)
        now = time.time()
        with self._lock:
            existing = self.get_record(key)
            created_at = existing.created_at if existing else now
            record = HoneycombRecord(
                key=key, data=data, created_at=created_at, updated_at=now
            )
            self._write_record(path, record)
        return record

    def load(self, key: str) -> Optional[Any]:
        record = self.get_record(key)
        return record.data if record else None

    def get_record(self, key: str) -> Optional[HoneycombRecord]:
        path = self._record_path(key)
        with self._lock:
            if not path.exists():
                return None
            return self._read_record(path)

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        with self._lock:
            keys = []
            for path in self._iter_record_paths():
                key = self._key_from_path(path)
                if prefix is None or key.startswith(prefix):
                    keys.append(key)
        keys.sort()
        return keys

    def remove(self, key: str) -> None:
        path = self._record_path(key)
        with self._lock:
            try:
                path.unlink()
            except FileNotFoundError:
                return
            self._cleanup_empty_directories(path.parent)

    def _cleanup_empty_directories(self, start: Path) -> None:
        current = start
        while current != self._base_dir and self._base_dir in current.parents:
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent

    def count(self, prefix: Optional[str] = None) -> int:
        return sum(1 for key in self.list_keys(prefix))

    def prune(self, prefix: str, *, older_than: float) -> int:
        with self._lock:
            paths = list(self._iter_record_paths())
        removed = 0
        for path in paths:
            key = self._key_from_path(path)
            if not key.startswith(prefix):
                continue
            record = self._read_record(path)
            if record is None or record.updated_at >= older_than:
                continue
            with self._lock:
                try:
                    path.unlink()
                except FileNotFoundError:
                    continue
                removed += 1
                self._cleanup_empty_directories(path.parent)
        return removed

    # ------------------------------------------------------------------
    # Metrics helpers
    # ------------------------------------------------------------------
    def comb_usage(self) -> List[Dict[str, Any]]:
        with self._lock:
            records = list(self._iter_records())
        aggregates: Dict[str, Dict[str, Any]] = {}
        for record in records:
            comb, _ = self._split_key(record.key)
            bucket = aggregates.setdefault(
                comb,
                {
                    "comb": comb,
                    "cells": 0,
                    "payload_bytes": 0,
                    "oldest": None,
                    "newest": None,
                },
            )
            bucket["cells"] += 1
            bucket["payload_bytes"] += self._payload_size(record.data)
            oldest = bucket["oldest"]
            newest = bucket["newest"]
            if oldest is None or record.created_at < float(oldest):
                bucket["oldest"] = record.created_at
            if newest is None or record.updated_at > float(newest):
                bucket["newest"] = record.updated_at
        return [aggregates[key] for key in sorted(aggregates.keys())]

    def prefix_metrics(self, prefix: str) -> Dict[str, Any]:
        cells = 0
        payload_bytes = 0
        oldest: Optional[float] = None
        newest: Optional[float] = None
        with self._lock:
            records = list(self._iter_records())
        for record in records:
            if not record.key.startswith(prefix):
                continue
            cells += 1
            payload_bytes += self._payload_size(record.data)
            if oldest is None or record.created_at < oldest:
                oldest = record.created_at
            if newest is None or record.updated_at > newest:
                newest = record.updated_at
        return {
            "cells": cells,
            "payload_bytes": payload_bytes,
            "oldest": oldest,
            "newest": newest,
        }

    def growth_samples(self, window_days: int = 30) -> List[Dict[str, Any]]:
        cutoff = time.time() - (window_days * 86400)
        buckets: Dict[str, int] = {}
        with self._lock:
            records = list(self._iter_records())
        for record in records:
            if record.created_at < cutoff:
                continue
            dt = datetime.fromtimestamp(record.created_at, tz=timezone.utc)
            bucket = dt.strftime("%Y-%m-%d")
            buckets[bucket] = buckets.get(bucket, 0) + 1
        return [
            {"date": date, "cells": buckets[date]} for date in sorted(buckets.keys())
        ]

    # ------------------------------------------------------------------
    # Honeycomb helpers
    # ------------------------------------------------------------------
    def append_conversation(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> HoneycombRecord:
        metadata = metadata.copy() if metadata else {}
        metadata.setdefault("role", role)
        cell_id = metadata.get("cell_id") or uuid.uuid4().hex
        metadata["cell_id"] = cell_id
        payload = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata,
            "timestamp": time.time(),
        }
        key = f"conversation/{conversation_id}/{cell_id}"
        return self.store(key, payload)

    def iter_conversation(self, conversation_id: str) -> Iterator[HoneycombRecord]:
        prefix = f"conversation/{conversation_id}/"
        with self._lock:
            records = [
                record
                for record in self._iter_records()
                if record.key.startswith(prefix)
            ]
        records.sort(key=lambda record: record.created_at)
        for record in records:
            yield record

    def query(
        self,
        prefix: str,
        *,
        limit: Optional[int] = None,
    ) -> List[HoneycombRecord]:
        with self._lock:
            records = [
                record
                for record in self._iter_records()
                if record.key.startswith(prefix)
            ]
        records.sort(key=lambda record: record.updated_at, reverse=True)
        if limit is not None:
            records = records[:limit]
        return records

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _payload_size(data: Any) -> int:
        try:
            payload = json.dumps(data, ensure_ascii=False)
        except TypeError:
            payload = json.dumps(str(data), ensure_ascii=False)
        return len(payload.encode("utf-8"))


__all__ = ["HoneycombStorage", "HoneycombRecord", "SCHEMA_VERSION"]
