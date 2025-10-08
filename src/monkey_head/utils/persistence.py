"""Persistent telemetry storage utilities."""

from __future__ import annotations

import json
import math
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .paths import ensure_subdirectory

try:  # pragma: no cover - optional import for type checking
    from huey.hardware.plugins import SensorReading
except Exception:  # pragma: no cover - avoid import cycles at runtime
    SensorReading = Any  # type: ignore[assignment]


@dataclass(frozen=True)
class SensorTelemetry:
    name: str
    timestamp: float
    value: Any
    provenance: Dict[str, Any]


@dataclass(frozen=True)
class AIInteraction:
    timestamp: float
    prompt: str
    response: str
    model: Optional[str]
    backend: Optional[str]
    instruction: Optional[str]
    metadata: Dict[str, Any]
    status: str


@dataclass(frozen=True)
class SystemEvent:
    timestamp: float
    event: str
    payload: Dict[str, Any]


class TelemetryStore:
    """SQLite-backed persistence for sensor, AI, and system events."""

    def __init__(self, path: Optional[Path | str] = None) -> None:
        base_dir = ensure_subdirectory("LOGS", "telemetry")
        if path is None:
            path = base_dir / "telemetry.db"
        else:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
        self._path = Path(path)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        self._initialise_schema()

    # ------------------------------------------------------------------
    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # ------------------------------------------------------------------
    def log_sensor_reading(self, reading: SensorReading) -> None:
        timestamp = self._normalise_timestamp(getattr(reading, "timestamp", None))
        payload = {
            "name": getattr(reading, "name", None),
            "timestamp": timestamp,
            "value": getattr(reading, "value", None),
            "provenance": getattr(reading, "provenance", {}),
        }
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO sensor_readings (name, timestamp, value, provenance)
                VALUES (?, ?, ?, ?)
                """,
                (
                    str(payload["name"]),
                    float(payload["timestamp"]),
                    self._dump_json(payload["value"]),
                    self._dump_json(payload["provenance"]),
                ),
            )

    # ------------------------------------------------------------------
    def log_ai_result(
        self,
        *,
        prompt: str,
        response: str,
        model: Optional[str],
        backend: Optional[str],
        instruction: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "success",
    ) -> None:
        metadata = metadata or {}
        timestamp = time.time()
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO ai_results (timestamp, prompt, response, model, backend, instruction, metadata, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    self._truncate(prompt),
                    self._truncate(response),
                    model,
                    backend,
                    instruction,
                    self._dump_json(metadata),
                    status,
                ),
            )

    # ------------------------------------------------------------------
    def log_event(self, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        payload = payload or {}
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO system_events (timestamp, event, payload)
                VALUES (?, ?, ?)
                """,
                (time.time(), event, self._dump_json(payload)),
            )

    # ------------------------------------------------------------------
    def fetch_recent_sensor_readings(
        self,
        *,
        name: Optional[str] = None,
        limit: int = 50,
    ) -> List[SensorTelemetry]:
        query = "SELECT name, timestamp, value, provenance FROM sensor_readings"
        params: Sequence[Any]
        if name:
            query += " WHERE name = ?"
            params = (name,)
        else:
            params = ()
        query += " ORDER BY timestamp DESC LIMIT ?"
        params = (*params, limit)
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        records: List[SensorTelemetry] = []
        for row in rows:
            records.append(
                SensorTelemetry(
                    name=row["name"],
                    timestamp=float(row["timestamp"]),
                    value=self._load_json(row["value"]),
                    provenance=self._load_json(row["provenance"], default={}),
                )
            )
        return records

    # ------------------------------------------------------------------
    def fetch_recent_ai_results(self, *, limit: int = 50) -> List[AIInteraction]:
        query = """
            SELECT timestamp, prompt, response, model, backend, instruction, metadata, status
            FROM ai_results
            ORDER BY timestamp DESC
            LIMIT ?
        """
        with self._lock:
            rows = self._conn.execute(query, (limit,)).fetchall()
        results: List[AIInteraction] = []
        for row in rows:
            results.append(
                AIInteraction(
                    timestamp=float(row["timestamp"]),
                    prompt=row["prompt"],
                    response=row["response"],
                    model=row["model"],
                    backend=row["backend"],
                    instruction=row["instruction"],
                    metadata=self._load_json(row["metadata"], default={}),
                    status=row["status"],
                )
            )
        return results

    # ------------------------------------------------------------------
    def fetch_recent_events(self, *, limit: int = 100) -> List[SystemEvent]:
        query = "SELECT timestamp, event, payload FROM system_events ORDER BY timestamp DESC LIMIT ?"
        with self._lock:
            rows = self._conn.execute(query, (limit,)).fetchall()
        return [
            SystemEvent(
                timestamp=float(row["timestamp"]),
                event=row["event"],
                payload=self._load_json(row["payload"], default={}),
            )
            for row in rows
        ]

    # ------------------------------------------------------------------
    def _initialise_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    value TEXT,
                    provenance TEXT
                )
                """,
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT,
                    backend TEXT,
                    instruction TEXT,
                    metadata TEXT,
                    status TEXT
                )
                """,
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event TEXT NOT NULL,
                    payload TEXT
                )
                """,
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sensor_ts ON sensor_readings(timestamp)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sensor_name_ts ON sensor_readings(name, timestamp)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ai_results_ts ON ai_results(timestamp)"
            )

    # ------------------------------------------------------------------
    @staticmethod
    def _dump_json(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=_stringify)

    @staticmethod
    def _load_json(value: Any, *, default: Any = None) -> Any:
        if value is None:
            return default
        try:
            return json.loads(value)
        except Exception:
            return default if default is not None else value

    @staticmethod
    def _truncate(value: str, limit: int = 4096) -> str:
        if len(value) <= limit:
            return value
        return value[: limit - 3] + "..."

    @staticmethod
    def _normalise_timestamp(value: Any) -> float:
        """Convert *value* to a float timestamp, falling back to ``time.time``."""

        if value is None:
            return time.time()
        if isinstance(value, (int, float)):
            if math.isfinite(value):
                return float(value)
            return time.time()
        try:
            converted = float(value)
        except (TypeError, ValueError):
            return time.time()
        if math.isfinite(converted):
            return converted
        return time.time()


def _stringify(value: Any) -> Any:
    try:
        return str(value)
    except Exception:  # pragma: no cover - fallback for exotic objects
        return repr(value)


__all__ = [
    "AIInteraction",
    "SensorTelemetry",
    "SystemEvent",
    "TelemetryStore",
]
