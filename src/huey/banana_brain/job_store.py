"""
banana_brain.job_store — SQLite persistence for GPU jobs.

Responsibilities (from the Banana Brain design doc):
  * Persist every job and its state transitions.
  * Retain a bounded history of terminal jobs for the CLI and API.
  * Support recovery: list PENDING/RUNNING jobs at startup.
  * Provide an event log for reservations, cancellations and operator
    actions that fall between state transitions.
  * Fail loudly on schema or integrity problems; fail softly on transient
    disk errors (log and re-raise, so the scheduler's _persist handler
    can decide whether to continue).

Public API (all async; safe to call from any task):

  async start()                               -> None
  async stop()                                -> None
  async save(job)                             -> None
  async get(job_id)                           -> Job | None
  async list_by_state(states)                 -> list[Job]
  async list_recent(limit, states=None)       -> list[Job]
  async count_by_state()                      -> dict[str, int]
  async find_by_idempotency_key(key, adapter) -> Job | None
  async list_events(job_id, limit=100)        -> list[dict]
  async record_event(job_id, kind, detail)    -> None
  async prune()                               -> dict[str, int]

Lifecycle (called by banana-brain_scheduler.py):
  async start()
  async stop()

Contracts:

  Job (from job_models):
    to_dict() -> JSON-serialisable dict
    from_dict(dict) -> Job

  The scheduler calls save() from a finally block via _persist(); it
  must not raise on transient errors in a way that prevents the next
  save from succeeding. The store therefore opens its own connection per
  process, uses WAL + busy_timeout, and surfaces failures as exceptions
  the caller may ignore if it chooses.

Configuration fields consumed:
  database_path: Path                (required)
  job_retention_days: float          (default 7.0)
  job_max_terminal_rows: int         (default 10000)
  job_prune_interval_seconds: float  (default 3600.0)
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import sqlite3
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .job_models import (
    TERMINAL_STATES,
    Job,
)

__all__ = [
    "SCHEMA_VERSION",
    "JobStore",
    "JobStoreNotReady",
    "SchemaError",
]

LOG = logging.getLogger("banana_brain.job_store")

SCHEMA_VERSION = 1

DEFAULT_RETENTION_DAYS = 7.0
DEFAULT_MAX_TERMINAL_ROWS = 10_000
DEFAULT_PRUNE_INTERVAL_S = 3600.0
BUSY_TIMEOUT_MS = 5_000

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id                    TEXT PRIMARY KEY,
    adapter               TEXT NOT NULL,
    payload               TEXT NOT NULL,
    priority              INTEGER NOT NULL,
    state                 TEXT NOT NULL,
    exclusive             INTEGER NOT NULL DEFAULT 0,
    deadline              REAL,
    estimated_vram_bytes  INTEGER,
    owner                 TEXT,
    tags                  TEXT NOT NULL DEFAULT '{}',
    idempotency_key       TEXT,
    submitted_at          REAL,
    started_at            REAL,
    finished_at           REAL,
    attempts              INTEGER NOT NULL DEFAULT 0,
    max_attempts          INTEGER NOT NULL DEFAULT 1,
    last_error            TEXT,
    result                TEXT,
    version               INTEGER NOT NULL DEFAULT 0,
    created_at            REAL NOT NULL,
    updated_at            REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_state
    ON jobs(state, submitted_at);

CREATE INDEX IF NOT EXISTS idx_jobs_adapter_state
    ON jobs(adapter, state);

CREATE INDEX IF NOT EXISTS idx_jobs_updated
    ON jobs(updated_at);

CREATE INDEX IF NOT EXISTS idx_jobs_idempotency
    ON jobs(idempotency_key)
    WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS job_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id     TEXT NOT NULL,
    at         REAL NOT NULL,
    kind       TEXT NOT NULL,
    from_state TEXT,
    to_state   TEXT,
    detail     TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_job_events_job
    ON job_events(job_id, at);
"""


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class JobStoreNotReady(RuntimeError):
    """Raised when save()/list_by_state() are called before start() or after stop()."""


class SchemaError(RuntimeError):
    """Raised when the database file has an incompatible schema."""


# ---------------------------------------------------------------------------
# JobStore
# ---------------------------------------------------------------------------


class JobStore:
    """
    SQLite-backed job persistence.

    A single connection is opened at start() and shared across all
    methods, serialised through an asyncio.Lock. This is deliberate:
    SQLite allows only one writer at a time, and the scheduler is the
    only producer of writes anyway. Serialising explicitly makes the
    locking model obvious and avoids transaction interleaving surprises.
    """

    def __init__(self, config: Any) -> None:
        self._config = config

        db_path = _cfg_get(config, "database_path", "job_store_path")
        if not db_path:
            raise SchemaError(
                "database_path is required in config (e.g. data/banana-brain.db)"
            )
        self._db_path = Path(str(db_path)).expanduser()

        self._retention_days = float(
            _cfg_num(config, "job_retention_days", DEFAULT_RETENTION_DAYS)
        )
        self._max_terminal_rows = int(
            _cfg_num(config, "job_max_terminal_rows", DEFAULT_MAX_TERMINAL_ROWS)
        )
        self._prune_interval_s = float(
            _cfg_num(config, "job_prune_interval_seconds", DEFAULT_PRUNE_INTERVAL_S)
        )

        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()
        self._prune_task: asyncio.Task[None] | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._conn is not None:
            raise JobStoreNotReady("job_store already started")

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        LOG.info("opening job store at %s", self._db_path)

        try:
            conn = await asyncio.to_thread(self._open_connection)
        except Exception as exc:
            raise SchemaError(f"cannot open job store {self._db_path}: {exc}") from exc

        async with self._lock:
            self._conn = conn

        try:
            await asyncio.to_thread(self._init_schema, conn)
        except Exception:
            async with self._lock:
                self._conn = None
            await asyncio.to_thread(self._close_sync, conn)
            raise

        # Best-effort first prune. Do not block startup on it.
        try:
            counts = await self.prune()
            if any(counts.values()):
                LOG.info("initial prune: %s", counts)
        except Exception:
            LOG.exception("initial prune failed; continuing")

        if self._prune_interval_s > 0:
            self._prune_task = asyncio.create_task(
                self._prune_loop(), name="banana-brain-job-store-prune"
            )

        async with self._lock:
            total = await asyncio.to_thread(self._count_sync, conn, None)
        LOG.info("job_store ready (%d total rows)", total)

    async def stop(self) -> None:
        task = self._prune_task
        self._prune_task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        async with self._lock:
            conn = self._conn
            self._conn = None
        if conn is not None:
            await asyncio.to_thread(self._close_sync, conn)
        LOG.info("job_store stopped")

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def save(self, job: Job) -> None:
        """
        Upsert the job. On a state change, also insert a transition event
        in the same transaction.

        Raises JobStoreNotReady if the store is not running, or the
        underlying sqlite3 error on disk failure. Callers are expected to
        decide whether to continue; the scheduler's _persist() logs and
        continues.
        """
        async with self._lock:
            conn = self._conn
            if conn is None:
                raise JobStoreNotReady("job_store is not running")
            await asyncio.to_thread(self._save_sync, conn, job)

    async def record_event(
        self, job_id: str, kind: str, detail: dict[str, Any] | None = None
    ) -> None:
        """
        Append a free-form event for the CLI/postmortem.

        Used by the scheduler (optionally) to log VRAM reservations,
        operator cancellations, watchdog interventions, etc. Never raises
        if the job_id does not exist — the FK is deferrable, and this is
        diagnostic data whose loss must not break the main flow.
        """
        async with self._lock:
            conn = self._conn
            if conn is None:
                raise JobStoreNotReady("job_store is not running")
            await asyncio.to_thread(self._record_event_sync, conn, job_id, kind, detail)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def get(self, job_id: str) -> Job | None:
        async with self._lock:
            conn = self._require_conn()
            return await asyncio.to_thread(self._get_sync, conn, job_id)

    async def list_by_state(self, states: Iterable[Any]) -> list[Job]:
        """
        Return all jobs in the given states, ordered by submitted_at.
        Accepts strings or JobState members; both are normalised to their
        string value before the query.
        """
        state_values = tuple(sorted({str(s) for s in states}))
        if not state_values:
            return []
        async with self._lock:
            conn = self._require_conn()
            return await asyncio.to_thread(self._list_by_state_sync, conn, state_values)

    async def list_recent(
        self, limit: int = 50, states: Iterable[Any] | None = None
    ) -> list[Job]:
        """Most recent jobs by updated_at, for CLI history."""
        state_values: tuple[str, ...] | None = None
        if states is not None:
            state_values = tuple(sorted({str(s) for s in states}))
            if not state_values:
                return []
        async with self._lock:
            conn = self._require_conn()
            return await asyncio.to_thread(
                self._list_recent_sync, conn, limit, state_values
            )

    async def count_by_state(self) -> dict[str, int]:
        async with self._lock:
            conn = self._require_conn()
            return await asyncio.to_thread(self._count_by_state_sync, conn)

    async def find_by_idempotency_key(self, key: str, adapter: str) -> Job | None:
        if not key:
            return None
        async with self._lock:
            conn = self._require_conn()
            return await asyncio.to_thread(
                self._find_by_idempotency_sync, conn, key, adapter
            )

    async def list_events(self, job_id: str, limit: int = 100) -> list[dict[str, Any]]:
        async with self._lock:
            conn = self._require_conn()
            return await asyncio.to_thread(self._list_events_sync, conn, job_id, limit)

    # ------------------------------------------------------------------
    # Maintenance
    # ------------------------------------------------------------------

    async def prune(self) -> dict[str, int]:
        """
        Delete old terminal jobs and excess terminal rows.

        Returns a dict of counts ({"aged_out": N, "over_cap": M}). Runs
        inside a single transaction. Safe to call concurrently with
        reads; the asyncio lock serialises against writes.
        """
        async with self._lock:
            conn = self._require_conn()
            return await asyncio.to_thread(self._prune_sync, conn)

    # ------------------------------------------------------------------
    # Internal: sync helpers (called from asyncio.to_thread only)
    # ------------------------------------------------------------------

    def _open_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            str(self._db_path),
            timeout=BUSY_TIMEOUT_MS / 1000.0,
            check_same_thread=False,
            isolation_level=None,  # explicit transactions
        )
        try:
            conn.row_factory = sqlite3.Row
            # Write-ahead logging improves read concurrency and survives
            # crashes more gracefully than the default rollback journal.
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
            conn.execute("PRAGMA foreign_keys = ON")

            # Cheap smoke test: the DB file must be readable. If this fails,
            # the file is corrupt or not a SQLite database at all.
            conn.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
            return conn
        except Exception:
            self._close_sync(conn)
            raise

    def _close_sync(self, conn: sqlite3.Connection) -> None:
        try:
            conn.close()
        except Exception:
            LOG.debug("sqlite close raised; ignoring", exc_info=True)

    def _init_schema(self, conn: sqlite3.Connection) -> None:
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version > SCHEMA_VERSION:
            raise SchemaError(
                f"job store at {self._db_path} has schema version {version}, "
                f"but this binary understands up to {SCHEMA_VERSION}. "
                "Downgrade is not supported; migrate manually."
            )

        # executescript() implicitly commits any open transaction first, so
        # the transaction must be part of the script itself. This keeps the
        # schema and user_version update atomic on Python's sqlite3 driver.
        script = (
            "BEGIN IMMEDIATE;\n"
            + _SCHEMA_SQL
            + f"\nPRAGMA user_version = {SCHEMA_VERSION};\nCOMMIT;"
        )
        try:
            conn.executescript(script)
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise

    def _save_sync(self, conn: sqlite3.Connection, job: Job) -> None:
        data = job.to_dict()
        now = time.time()
        payload_json = _dumps(data["payload"])
        tags_json = _dumps(data.get("tags") or {})
        result_json = _dumps(data["result"]) if data.get("result") is not None else None

        row = (
            data["id"],
            data["adapter"],
            payload_json,
            int(data["priority"]),
            data["state"],
            1 if data["exclusive"] else 0,
            data["deadline"],
            data["estimated_vram_bytes"],
            data["owner"],
            tags_json,
            data["idempotency_key"],
            data["submitted_at"],
            data["started_at"],
            data["finished_at"],
            int(data["attempts"]),
            int(data["max_attempts"]),
            data["last_error"],
            result_json,
            int(data.get("version") or 0),
            now,  # created_at (used only on insert)
            now,  # updated_at
        )

        conn.execute("BEGIN IMMEDIATE")
        try:
            prev = conn.execute(
                "SELECT state FROM jobs WHERE id = ?", (data["id"],)
            ).fetchone()
            prev_state = prev["state"] if prev is not None else None

            conn.execute(
                """
                INSERT INTO jobs (
                    id, adapter, payload, priority, state, exclusive,
                    deadline, estimated_vram_bytes, owner, tags,
                    idempotency_key, submitted_at, started_at, finished_at,
                    attempts, max_attempts, last_error, result, version,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    adapter              = excluded.adapter,
                    payload              = excluded.payload,
                    priority             = excluded.priority,
                    state                = excluded.state,
                    exclusive            = excluded.exclusive,
                    deadline             = excluded.deadline,
                    estimated_vram_bytes = excluded.estimated_vram_bytes,
                    owner                = excluded.owner,
                    tags                 = excluded.tags,
                    idempotency_key      = excluded.idempotency_key,
                    submitted_at         = excluded.submitted_at,
                    started_at           = excluded.started_at,
                    finished_at          = excluded.finished_at,
                    attempts             = excluded.attempts,
                    max_attempts         = excluded.max_attempts,
                    last_error           = excluded.last_error,
                    result               = excluded.result,
                    version              = excluded.version,
                    updated_at           = excluded.updated_at
                """,
                row,
            )

            if prev_state != job.state.value:
                conn.execute(
                    "INSERT INTO job_events "
                    "(job_id, at, kind, from_state, to_state, detail) "
                    "VALUES (?, ?, 'transition', ?, ?, NULL)",
                    (job.id, now, prev_state, job.state.value),
                )

            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def _record_event_sync(
        self,
        conn: sqlite3.Connection,
        job_id: str,
        kind: str,
        detail: dict[str, Any] | None,
    ) -> None:
        now = time.time()
        detail_json = _dumps(detail) if detail is not None else None
        try:
            conn.execute(
                "INSERT INTO job_events (job_id, at, kind, detail) "
                "VALUES (?, ?, ?, ?)",
                (job_id, now, kind, detail_json),
            )
        except sqlite3.IntegrityError:
            # FK violation: the job row is gone (pruned between the event
            # being produced and being written). Drop the event; it is
            # diagnostic, not load-bearing.
            LOG.debug(
                "record_event: job %s no longer exists; dropping %s",
                job_id,
                kind,
            )

    def _get_sync(self, conn: sqlite3.Connection, job_id: str) -> Job | None:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return _row_to_job(row)

    def _list_by_state_sync(
        self, conn: sqlite3.Connection, states: tuple[str, ...]
    ) -> list[Job]:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE state IN "
            "(SELECT value FROM json_each(?)) "
            "ORDER BY submitted_at ASC, id ASC",
            (json.dumps([str(state) for state in states]),),
        ).fetchall()
        return _rows_to_jobs(rows)

    def _list_recent_sync(
        self,
        conn: sqlite3.Connection,
        limit: int,
        states: tuple[str, ...] | None,
    ) -> list[Job]:
        limit = max(0, int(limit))
        if limit == 0:
            return []
        if states:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE state IN "
                "(SELECT value FROM json_each(?)) "
                "ORDER BY updated_at DESC, id DESC LIMIT ?",
                (json.dumps([str(state) for state in states]), limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY updated_at DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return _rows_to_jobs(rows)

    def _count_by_state_sync(self, conn: sqlite3.Connection) -> dict[str, int]:
        rows = conn.execute(
            "SELECT state, COUNT(*) AS n FROM jobs GROUP BY state"
        ).fetchall()
        return {row["state"]: int(row["n"]) for row in rows}

    def _count_sync(self, conn: sqlite3.Connection, where_state: str | None) -> int:
        if where_state is None:
            row = conn.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM jobs WHERE state = ?",
                (where_state,),
            ).fetchone()
        return int(row["n"])

    def _find_by_idempotency_sync(
        self, conn: sqlite3.Connection, key: str, adapter: str
    ) -> Job | None:
        row = conn.execute(
            "SELECT * FROM jobs WHERE idempotency_key = ? AND adapter = ? "
            "ORDER BY created_at ASC LIMIT 1",
            (key, adapter),
        ).fetchone()
        return _row_to_job(row) if row is not None else None

    def _list_events_sync(
        self, conn: sqlite3.Connection, job_id: str, limit: int
    ) -> list[dict[str, Any]]:
        rows = conn.execute(
            "SELECT at, kind, from_state, to_state, detail FROM job_events "
            "WHERE job_id = ? ORDER BY at DESC, id DESC LIMIT ?",
            (job_id, max(1, int(limit))),
        ).fetchall()
        return [
            {
                "at": float(row["at"]),
                "kind": row["kind"],
                "from_state": row["from_state"],
                "to_state": row["to_state"],
                "detail": _maybe_loads(row["detail"]),
            }
            for row in rows
        ]

    def _prune_sync(self, conn: sqlite3.Connection) -> dict[str, int]:
        counts = {"aged_out": 0, "over_cap": 0}
        conn.execute("BEGIN IMMEDIATE")
        try:
            if self._retention_days > 0:
                cutoff = time.time() - self._retention_days * 86400.0
                cursor = conn.execute(
                    "DELETE FROM jobs WHERE state IN "
                    "(SELECT value FROM json_each(?)) "
                    "AND COALESCE(finished_at, updated_at) < ?",
                    (json.dumps([str(state) for state in TERMINAL_STATES]), cutoff),
                )
                counts["aged_out"] = cursor.rowcount or 0

            if self._max_terminal_rows > 0:
                total_terminal_row = conn.execute(
                    "SELECT COUNT(*) AS n FROM jobs "
                    "WHERE state IN (SELECT value FROM json_each(?))",
                    (json.dumps([str(state) for state in TERMINAL_STATES]),),
                ).fetchone()
                total_terminal = int(total_terminal_row["n"])
                excess = total_terminal - self._max_terminal_rows
                if excess > 0:
                    cursor = conn.execute(
                        "DELETE FROM jobs WHERE id IN ("
                        "  SELECT id FROM jobs "
                        "  WHERE state IN (SELECT value FROM json_each(?)) "
                        "  ORDER BY COALESCE(finished_at, updated_at) ASC "
                        "  LIMIT ?"
                        ")",
                        (
                            json.dumps([str(state) for state in TERMINAL_STATES]),
                            excess,
                        ),
                    )
                    counts["over_cap"] = cursor.rowcount or 0

            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return counts

    # ------------------------------------------------------------------
    # Internal: async helpers
    # ------------------------------------------------------------------

    def _require_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise JobStoreNotReady("job_store is not running")
        return self._conn

    async def _prune_loop(self) -> None:
        while True:
            try:
                await asyncio.sleep(self._prune_interval_s)
                counts = await self.prune()
                if any(counts.values()):
                    LOG.info("pruned job store: %s", counts)
            except asyncio.CancelledError:
                raise
            except Exception:
                LOG.exception("periodic prune failed; will retry")


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _maybe_loads(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return repr(value)
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        LOG.warning("job_store: unparseable JSON in column: %r", value[:80])
        return None


def _row_to_job(row: sqlite3.Row) -> Job:
    payload = _maybe_loads(row["payload"]) or {}
    tags = _maybe_loads(row["tags"]) or {}
    result = _maybe_loads(row["result"]) if row["result"] is not None else None
    data = {
        "id": row["id"],
        "adapter": row["adapter"],
        "payload": payload,
        "priority": int(row["priority"]),
        "state": row["state"],
        "exclusive": bool(row["exclusive"]),
        "deadline": row["deadline"],
        "estimated_vram_bytes": row["estimated_vram_bytes"],
        "owner": row["owner"],
        "tags": tags,
        "idempotency_key": row["idempotency_key"],
        "submitted_at": row["submitted_at"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "attempts": int(row["attempts"]),
        "max_attempts": int(row["max_attempts"]),
        "last_error": row["last_error"],
        "result": result,
        "version": int(row["version"]),
    }
    return Job.from_dict(data)


def _rows_to_jobs(rows: Iterable[sqlite3.Row]) -> list[Job]:
    """
    Convert rows to Jobs, skipping any row that fails to deserialise.

    A single corrupt row must not break recovery of the rest of the
    queue. The skip is logged at warning so operators can find the row.
    """
    jobs: list[Job] = []
    for row in rows:
        try:
            jobs.append(_row_to_job(row))
        except Exception:
            LOG.exception(
                "job_store: skipping unparseable row id=%s",
                row["id"] if "id" in row.keys() else "<unknown>",  # noqa: SIM118
            )
    return jobs


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def _cfg_get(config: Any, *names: str) -> Any:
    for name in names:
        if isinstance(config, dict):
            if name in config:
                return config[name]
            continue
        value = getattr(config, name, None)
        if value is not None:
            return value
    return None


def _cfg_num(config: Any, name: str, default: float) -> float:
    value = _cfg_get(config, name)
    return float(value) if isinstance(value, (int, float)) else default
