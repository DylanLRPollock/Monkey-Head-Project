"""SQLite persistence, query, event, migration, and pruning tests."""

from __future__ import annotations

import asyncio
import sqlite3
from types import SimpleNamespace
import time

import pytest

from huey.banana_brain.job_models import JobState, Priority
from huey.banana_brain.job_store import (
    JobStore,
    JobStoreNotReady,
    SchemaError,
    _maybe_loads,
    _cfg_get,
    _row_to_job,
    _rows_to_jobs,
)

from .conftest import make_job


@pytest.mark.asyncio
async def test_lifecycle_state_queries_events_and_idempotency(job_store):
    with pytest.raises(JobStoreNotReady):
        await JobStore({"database_path": "/tmp/not-started.db"}).save(make_job())
    with pytest.raises(JobStoreNotReady, match="already started"):
        await job_store.start()

    pending = make_job(
        priority=int(Priority.INTERACTIVE),
        payload={"prompt": "hello"},
        idempotency_key="same",
        owner="test",
        tags={"source": "unit"},
    )
    await job_store.save(pending)
    assert (await job_store.get(pending.id)).payload == {"prompt": "hello"}
    assert await job_store.find_by_idempotency_key("same", "fake") is not None
    assert await job_store.find_by_idempotency_key("same", "other") is None
    assert await job_store.find_by_idempotency_key("", "fake") is None

    pending.state = JobState.RUNNING
    pending.started_at = time.time()
    await job_store.save(pending)
    pending.state = JobState.COMPLETED
    pending.finished_at = time.time()
    pending.result = {"ok": True}
    await job_store.save(pending)
    assert len(await job_store.list_by_state([JobState.COMPLETED])) == 1
    assert len(await job_store.list_by_state(["pending", "completed"])) == 1
    assert await job_store.list_by_state([]) == []
    assert await job_store.list_recent(limit=0) == []
    assert await job_store.list_recent(states=[]) == []
    assert len(await job_store.list_recent()) == 1
    assert (await job_store.list_recent(limit=5, states=["completed"]))[0].result == {
        "ok": True
    }
    assert await job_store.count_by_state() == {"completed": 1}
    assert [
        event["to_state"] for event in await job_store.list_events(pending.id, limit=10)
    ] == ["completed", "running", "pending"]
    await job_store.record_event(pending.id, "operator", {"action": "review"})
    events = await job_store.list_events(pending.id)
    assert events[0]["detail"] == {"action": "review"}
    await job_store.record_event("gone", "late", {"ignored": True})
    assert await job_store.get("missing") is None


@pytest.mark.asyncio
async def test_prune_age_cap_and_active_rows(tmp_path):
    config = {
        "database_path": tmp_path / "prune.db",
        "job_retention_days": 0.00001,
        "job_max_terminal_rows": 2,
        "job_prune_interval_seconds": 0,
    }
    store = JobStore(config)
    await store.start()
    try:
        for i in range(4):
            job = make_job(payload={"index": i})
            job.id = f"terminal-{i}"
            job.state = JobState.COMPLETED
            job.submitted_at = time.time() - 100 - i
            job.finished_at = time.time() - 100 - i
            await store.save(job)
        active = make_job()
        active.id = "active"
        await store.save(active)
        counts = await store.prune()
        assert counts["aged_out"] == 4
        assert counts["over_cap"] == 0
        assert await store.get("active") is not None

        # A separate store uses the count cap with current timestamps.
        await store.stop()
        config2 = {
            "database_path": tmp_path / "cap.db",
            "job_retention_days": 0,
            "job_max_terminal_rows": 2,
            "job_prune_interval_seconds": 0,
        }
        capped = JobStore(config2)
        await capped.start()
        for i in range(4):
            job = make_job()
            job.id = f"cap-{i}"
            job.state = JobState.COMPLETED
            job.finished_at = time.time() - (4 - i)
            await capped.save(job)
        assert (await capped.prune())["over_cap"] == 2
        assert len(await capped.list_by_state(["completed"])) == 2
        await capped.stop()
    finally:
        await store.stop()


@pytest.mark.asyncio
async def test_schema_errors_bad_database_and_forward_version(tmp_path):
    with pytest.raises(SchemaError, match="database_path is required"):
        JobStore({})
    bad_db = tmp_path / "bad.db"
    bad_db.write_text("not a sqlite database")
    with pytest.raises(SchemaError, match="cannot open job store"):
        await JobStore({"database_path": bad_db}).start()

    newer_db = tmp_path / "newer.db"
    connection = sqlite3.connect(newer_db)
    connection.execute("PRAGMA user_version = 99")
    connection.close()
    store = JobStore({"database_path": newer_db, "job_prune_interval_seconds": 0})
    with pytest.raises(SchemaError, match="schema version 99"):
        await store.start()
    assert store._conn is None


@pytest.mark.asyncio
async def test_row_helpers_skip_corrupt_rows_and_decode_malformed_values(job_store):
    assert _maybe_loads(None) is None
    assert _maybe_loads(b'{"x":1}') == {"x": 1}
    assert _maybe_loads(b"\xff") == "b'\\xff'"
    assert _maybe_loads({"value": 1}) == {"value": 1}
    assert _maybe_loads("not-json") is None
    job = make_job()
    await job_store.save(job)
    rows = job_store._conn.execute("SELECT * FROM jobs")
    row = rows.fetchone()
    assert _row_to_job(row).id == job.id
    broken = dict(row)
    broken["state"] = "not-a-state"
    assert _rows_to_jobs([broken]) == []


@pytest.mark.asyncio
async def test_read_operations_require_running_store(tmp_path):
    store = JobStore({"database_path": tmp_path / "not-open.db"})
    with pytest.raises(JobStoreNotReady):
        await store.get("job")
    with pytest.raises(JobStoreNotReady):
        await store.record_event("job", "test")
    assert _cfg_get(SimpleNamespace(value=3), "missing", "value") == 3
    assert _cfg_get({}, "missing") is None


@pytest.mark.asyncio
async def test_periodic_prune_retries_after_failure(tmp_path):
    store = JobStore(
        {
            "database_path": tmp_path / "prune-retry.db",
            "job_prune_interval_seconds": 0.005,
        }
    )
    attempts = 0
    retried = asyncio.Event()

    async def fail_prune():
        nonlocal attempts
        attempts += 1
        if attempts >= 2:
            retried.set()
        raise OSError("temporary database issue")

    store.prune = fail_prune
    await store.start()
    try:
        await asyncio.wait_for(retried.wait(), timeout=1)
    finally:
        await store.stop()
    assert attempts >= 2


@pytest.mark.asyncio
async def test_write_and_prune_transactions_roll_back_on_sqlite_errors(
    tmp_path,
):
    store = JobStore(
        {
            "database_path": tmp_path / "rollback.db",
            "job_retention_days": 0,
            "job_prune_interval_seconds": 0,
        }
    )
    await store.start()
    try:
        job = make_job()
        await store.save(job)
        store._conn.execute(
            "CREATE TRIGGER block_job_update BEFORE UPDATE ON jobs "
            "BEGIN SELECT RAISE(ABORT, 'blocked'); END"
        )
        job.state = JobState.RUNNING
        with pytest.raises(sqlite3.IntegrityError):
            await store.save(job)
        assert store._conn.in_transaction is False
        store._conn.execute("DROP TRIGGER block_job_update")

        old = make_job()
        old.state = JobState.COMPLETED
        old.finished_at = time.time() - 100
        await store.save(old)
        store._conn.execute(
            "CREATE TRIGGER block_job_delete BEFORE DELETE ON jobs "
            "BEGIN SELECT RAISE(ABORT, 'blocked'); END"
        )
        store._retention_days = 0.00001
        with pytest.raises(sqlite3.IntegrityError):
            await store.prune()
        assert store._conn.in_transaction is False
    finally:
        await store.stop()
