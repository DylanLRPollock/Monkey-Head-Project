"""SQLite-backed telemetry persistence for HueyOS runtime tests."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SensorTelemetry:
    name: str
    value: Any
    timestamp: float
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIInteraction:
    timestamp: float
    prompt: str
    response: str
    model: str
    backend: str
    instruction: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "success"


@dataclass(frozen=True)
class TelemetryEvent:
    timestamp: float
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)


class TelemetryStore:
    """Small SQLite store for sensor readings, AI interactions, and events."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or Path.home() / ".hueyos" / "telemetry.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    provenance_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS ai_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    model TEXT NOT NULL,
                    backend TEXT NOT NULL,
                    instruction TEXT,
                    metadata_json TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                """)

    def log_sensor_reading(self, reading: Any) -> None:
        name = str(reading.name)
        value = reading.value
        timestamp = _coerce_timestamp(getattr(reading, "timestamp", None))
        provenance = _coerce_mapping(getattr(reading, "provenance", None))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sensor_readings
                    (name, value_json, timestamp, provenance_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    name,
                    _json_dump(value),
                    timestamp,
                    _json_dump(provenance),
                ),
            )

    def fetch_recent_sensor_readings(
        self, *, name: str | None = None, limit: int = 25
    ) -> list[SensorTelemetry]:
        query = (
            "SELECT name, value_json, timestamp, provenance_json "
            "FROM sensor_readings"
        )
        params: list[Any] = []
        if name is not None:
            query += " WHERE name = ?"
            params.append(name)
        query += " ORDER BY timestamp DESC, id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            SensorTelemetry(
                name=row["name"],
                value=json.loads(row["value_json"]),
                timestamp=float(row["timestamp"]),
                provenance=_coerce_mapping(json.loads(row["provenance_json"])),
            )
            for row in rows
        ]

    def log_ai_result(
        self,
        *,
        prompt: str,
        response: str,
        model: str,
        backend: str,
        instruction: str | None = None,
        metadata: dict[str, Any] | None = None,
        status: str = "success",
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ai_interactions
                    (timestamp, prompt, response, model, backend, instruction,
                     metadata_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    time.time(),
                    prompt,
                    response,
                    model,
                    backend,
                    instruction,
                    _json_dump(metadata or {}),
                    status,
                ),
            )

    def fetch_recent_ai_results(self, *, limit: int = 25) -> list[AIInteraction]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT timestamp, prompt, response, model, backend, instruction,
                       metadata_json, status
                FROM ai_interactions
                ORDER BY timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            AIInteraction(
                timestamp=float(row["timestamp"]),
                prompt=row["prompt"],
                response=row["response"],
                model=row["model"],
                backend=row["backend"],
                instruction=row["instruction"],
                metadata=_coerce_mapping(json.loads(row["metadata_json"])),
                status=row["status"],
            )
            for row in rows
        ]

    def log_event(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO events (timestamp, event_type, payload_json)
                VALUES (?, ?, ?)
                """,
                (time.time(), event_type, _json_dump(payload or {})),
            )

    def fetch_recent_events(
        self, *, event_type: str | None = None, limit: int = 25
    ) -> list[TelemetryEvent]:
        query = "SELECT timestamp, event_type, payload_json FROM events"
        params: list[Any] = []
        if event_type is not None:
            query += " WHERE event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp DESC, id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            TelemetryEvent(
                timestamp=float(row["timestamp"]),
                event_type=row["event_type"],
                payload=_coerce_mapping(json.loads(row["payload_json"])),
            )
            for row in rows
        ]


def _coerce_timestamp(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return time.time()


def _coerce_mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _json_dump(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


__all__ = [
    "AIInteraction",
    "SensorTelemetry",
    "TelemetryEvent",
    "TelemetryStore",
]
