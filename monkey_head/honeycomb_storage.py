"""Honeycomb-inspired persistent storage with SQLite backing.

This module replaces the earlier JSON-based Honeycomb storage with a
structured SQLite implementation. Data is sharded into logical
"honeycomb" clusters derived from hashed keys and supports replicated
metadata alongside rich conversation history suitable for agent memory.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConversationEntry:
    """A single conversation message stored within a honeycomb cell."""

    cell_key: str
    agent: str
    role: str
    content: str
    created_at: datetime
    metadata: Dict[str, Any]


class HoneycombStorage:
    """Fault-tolerant honeycomb storage backed by SQLite."""

    DEFAULT_DB_FILENAME = "honeycomb.sqlite3"

    def __init__(
        self,
        base_dir: str | Path = "memory/HONEYCOMB",
        replicas: int = 2,
        db_filename: str = DEFAULT_DB_FILENAME,
    ) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / db_filename
        self.replicas = max(1, replicas)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._conn.row_factory = sqlite3.Row
        self._apply_migrations()

    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the SQLite connection."""

        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------
    def _apply_migrations(self) -> None:
        """Apply schema migrations ensuring backwards compatibility."""

        with self._lock:
            cursor = self._conn.execute("PRAGMA user_version")
            (version,) = cursor.fetchone()

            if version < 1:
                self._conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS honeycomb_cells (
                        cell_key TEXT PRIMARY KEY,
                        cluster TEXT NOT NULL,
                        data TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS honeycomb_replicas (
                        cell_key TEXT NOT NULL,
                        replica_index INTEGER NOT NULL,
                        cluster TEXT NOT NULL,
                        PRIMARY KEY (cell_key, replica_index)
                    );

                    CREATE TABLE IF NOT EXISTS conversation_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cell_key TEXT NOT NULL,
                        agent TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        metadata TEXT
                    );
                    """
                )
                self._conn.execute("PRAGMA user_version = 1")

            if version < 2:
                # Reserved for future migrations to avoid recreating structures.
                self._conn.execute("PRAGMA user_version = 2")

            self._conn.commit()

    # ------------------------------------------------------------------
    def _cluster_ids(self, key: str) -> List[str]:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        clusters: List[str] = []
        for index in range(self.replicas):
            start = index * 2
            end = start + 2
            clusters.append(digest[start:end])
        return clusters or [digest[:2]]

    # ------------------------------------------------------------------
    def _write_cell(self, key: str, cluster: str, payload: str, updated_at: str) -> None:
        self._conn.execute(
            """
            INSERT INTO honeycomb_cells (cell_key, cluster, data, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cell_key) DO UPDATE SET
                cluster=excluded.cluster,
                data=excluded.data,
                updated_at=excluded.updated_at
            """,
            (key, cluster, payload, updated_at),
        )

    # ------------------------------------------------------------------
    def _write_replicas(self, key: str, clusters: Iterable[str]) -> None:
        self._conn.execute(
            "DELETE FROM honeycomb_replicas WHERE cell_key = ?",
            (key,),
        )
        self._conn.executemany(
            """
            INSERT INTO honeycomb_replicas (cell_key, replica_index, cluster)
            VALUES (?, ?, ?)
            """,
            ((key, index, cluster) for index, cluster in enumerate(clusters)),
        )

    # ------------------------------------------------------------------
    def store(self, key: str, data: Dict[str, Any]) -> None:
        """Persist JSON-serialisable data for a honeycomb key."""

        payload = json.dumps(data, sort_keys=True)
        updated_at = datetime.utcnow().isoformat()
        clusters = self._cluster_ids(key)

        with self._lock, self._conn:
            self._write_cell(key, clusters[0], payload, updated_at)
            self._write_replicas(key, clusters)

    # ------------------------------------------------------------------
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve JSON data for the given key, if present."""

        with self._lock:
            row = self._conn.execute(
                "SELECT data FROM honeycomb_cells WHERE cell_key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row["data"])

    # ------------------------------------------------------------------
    def remove(self, key: str) -> None:
        """Remove the honeycomb cell and associated replicas and history."""

        with self._lock, self._conn:
            self._conn.execute(
                "DELETE FROM conversation_entries WHERE cell_key = ?",
                (key,),
            )
            self._conn.execute(
                "DELETE FROM honeycomb_replicas WHERE cell_key = ?",
                (key,),
            )
            self._conn.execute(
                "DELETE FROM honeycomb_cells WHERE cell_key = ?",
                (key,),
            )

    # ------------------------------------------------------------------
    def list_keys(self) -> List[str]:
        """Return all known honeycomb keys sorted alphabetically."""

        with self._lock:
            rows = self._conn.execute(
                "SELECT cell_key FROM honeycomb_cells ORDER BY cell_key ASC"
            ).fetchall()
        return [row["cell_key"] for row in rows]

    # ------------------------------------------------------------------
    def append_conversation(
        self,
        key: str,
        agent: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a conversation entry linked to the honeycomb key."""

        metadata_json = json.dumps(metadata or {}, sort_keys=True)
        created_at = datetime.utcnow().isoformat()

        with self._lock, self._conn:
            clusters = self._cluster_ids(key)
            if self.load(key) is None:
                self._write_cell(
                    key,
                    clusters[0],
                    json.dumps({}, sort_keys=True),
                    created_at,
                )
                self._write_replicas(key, clusters)

            self._conn.execute(
                """
                INSERT INTO conversation_entries
                    (cell_key, agent, role, content, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (key, agent, role, content, created_at, metadata_json),
            )

            base_payload = self.load(key) or {}
            stats = {
                "conversation_count": self._conversation_count_locked(key),
                "last_speaker": agent,
                "last_role": role,
                "last_updated": created_at,
            }
            base_payload.update(stats)
            self._write_cell(
                key,
                clusters[0],
                json.dumps(base_payload, sort_keys=True),
                created_at,
            )

    # ------------------------------------------------------------------
    def _conversation_count_locked(self, key: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) as total FROM conversation_entries WHERE cell_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return 0
        if "total" in row.keys():
            return int(row["total"])
        return int(row[0])

    # ------------------------------------------------------------------
    def get_conversation(self, key: str, limit: Optional[int] = None) -> List[ConversationEntry]:
        """Return ordered conversation history for a given honeycomb key."""

        query = (
            "SELECT cell_key, agent, role, content, created_at, metadata "
            "FROM conversation_entries WHERE cell_key = ? "
            "ORDER BY id ASC"
        )
        if limit is not None:
            query += " LIMIT ?"
            params: Iterable[Any] = (key, limit)
        else:
            params = (key,)

        with self._lock:
            rows = self._conn.execute(query, params).fetchall()

        entries: List[ConversationEntry] = []
        for row in rows:
            metadata_raw = row["metadata"]
            metadata = json.loads(metadata_raw) if metadata_raw else {}
            entries.append(
                ConversationEntry(
                    cell_key=row["cell_key"],
                    agent=row["agent"],
                    role=row["role"],
                    content=row["content"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    metadata=metadata,
                )
            )
        return entries


__all__ = ["HoneycombStorage", "ConversationEntry"]

