"""Honeycomb inspired structured storage for HueyOS agents."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, List, Optional

from monkey_head.utils.paths import ensure_subdirectory

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class HoneycombRecord:
    """Represents a single stored payload inside the honeycomb."""

    key: str
    data: Any
    created_at: float
    updated_at: float


class HoneycombStorage:
    """SQLite backed key-value store arranged using a honeycomb metaphor.

    Parameters
    ----------
    base_dir:
        Optional directory where the SQLite database should be created. When
        ``None`` the directory ``memory/LOGS/honeycomb`` inside the project is
        used. The directory is always created if it does not exist.
    db_filename:
        Name of the SQLite database file to create within ``base_dir``.
    """

    def __init__(
        self,
        base_dir: Optional[Path | str] = None,
        *,
        db_filename: str = "honeycomb.db",
    ) -> None:
        if base_dir is None:
            base_dir = ensure_subdirectory("LOGS", "honeycomb")
        else:
            base_dir = Path(base_dir)
            base_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = Path(base_dir) / db_filename
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._migrate()

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------
    def _migrate(self) -> None:
        """Run schema migrations ensuring backward compatibility."""

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("PRAGMA user_version")
            (current_version,) = cursor.fetchone()
            if current_version == 0:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS honeycomb_cells (
                        full_key   TEXT PRIMARY KEY,
                        comb       TEXT NOT NULL,
                        cell       TEXT NOT NULL,
                        payload    TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )
                    """
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_honeycomb_comb ON honeycomb_cells(comb)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_honeycomb_updated ON honeycomb_cells(updated_at)"
                )
                cursor.execute("PRAGMA user_version = 1")
                self._conn.commit()
            elif current_version > SCHEMA_VERSION:
                raise RuntimeError(
                    "Honeycomb storage schema is newer than this runtime supports"
                )

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _split_key(key: str) -> tuple[str, str]:
        """Split a key into ``comb`` and ``cell`` components."""

        if "/" in key:
            comb, cell = key.split("/", 1)
        else:
            comb, cell = "default", key
        return comb, cell

    # ------------------------------------------------------------------
    # Core storage API
    # ------------------------------------------------------------------
    def store(self, key: str, data: Any) -> HoneycombRecord:
        """Store ``data`` under ``key`` returning the resulting record."""

        payload = json.dumps(data, ensure_ascii=False)
        comb, cell = self._split_key(key)
        now = time.time()
        with self._lock:
            existing = self._fetch_record_metadata(key)
            created_at = existing.created_at if existing else now
            cursor = self._conn.cursor()
            cursor.execute(
                """
                INSERT INTO honeycomb_cells (full_key, comb, cell, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(full_key) DO UPDATE SET
                    comb=excluded.comb,
                    cell=excluded.cell,
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
                """,
                (key, comb, cell, payload, created_at, now),
            )
            self._conn.commit()
        return HoneycombRecord(key=key, data=data, created_at=created_at, updated_at=now)

    def load(self, key: str) -> Optional[Any]:
        """Return the stored payload for ``key`` or ``None`` when missing."""

        record = self.get_record(key)
        return record.data if record else None

    def get_record(self, key: str) -> Optional[HoneycombRecord]:
        """Return the full record for ``key`` including timestamps."""

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT full_key, payload, created_at, updated_at FROM honeycomb_cells WHERE full_key = ?",
                (key,),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return HoneycombRecord(
            key=row["full_key"],
            data=json.loads(row["payload"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_keys(self, prefix: Optional[str] = None) -> List[str]:
        """Return all keys or those beginning with ``prefix`` sorted lexicographically."""

        with self._lock:
            cursor = self._conn.cursor()
            if prefix is None:
                cursor.execute("SELECT full_key FROM honeycomb_cells ORDER BY full_key ASC")
            else:
                cursor.execute(
                    "SELECT full_key FROM honeycomb_cells WHERE full_key LIKE ? ORDER BY full_key ASC",
                    (f"{prefix}%",),
                )
            rows = cursor.fetchall()
        return [row["full_key"] for row in rows]

    def remove(self, key: str) -> None:
        """Remove ``key`` if it exists."""

        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("DELETE FROM honeycomb_cells WHERE full_key = ?", (key,))
            self._conn.commit()

    # ------------------------------------------------------------------
    # Honeycomb helpers
    # ------------------------------------------------------------------
    def append_conversation(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> HoneycombRecord:
        """Append a conversation entry stored under a deterministic honeycomb path."""

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
        """Yield conversation records for ``conversation_id`` ordered by time."""

        prefix = f"conversation/{conversation_id}/"
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                """
                SELECT full_key, payload, created_at, updated_at
                FROM honeycomb_cells
                WHERE full_key LIKE ?
                ORDER BY created_at ASC
                """,
                (f"{prefix}%",),
            )
            rows = cursor.fetchall()
        for row in rows:
            yield HoneycombRecord(
                key=row["full_key"],
                data=json.loads(row["payload"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def query(self, prefix: str, *, limit: Optional[int] = None) -> List[HoneycombRecord]:
        """Return records whose key begins with ``prefix`` sorted by recency."""

        with self._lock:
            cursor = self._conn.cursor()
            sql = (
                "SELECT full_key, payload, created_at, updated_at "
                "FROM honeycomb_cells WHERE full_key LIKE ? ORDER BY updated_at DESC"
            )
            params: list[Any] = [f"{prefix}%"]
            if limit is not None:
                sql += " LIMIT ?"
                params.append(limit)
            cursor.execute(sql, params)
            rows = cursor.fetchall()
        return [
            HoneycombRecord(
                key=row["full_key"],
                data=json.loads(row["payload"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the underlying SQLite connection."""

        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _fetch_record_metadata(self, key: str) -> Optional[HoneycombRecord]:
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT full_key, created_at, updated_at FROM honeycomb_cells WHERE full_key = ?",
                (key,),
            )
            row = cursor.fetchone()
        if not row:
            return None
        return HoneycombRecord(
            key=row["full_key"],
            data=None,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # Allow use as a context manager -----------------------------------
    def __enter__(self) -> "HoneycombStorage":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - passthrough
        self.close()


__all__ = ["HoneycombStorage", "HoneycombRecord", "SCHEMA_VERSION"]
