"""Tests for huey.banana_brain.priority_manager."""

from __future__ import annotations

import time

import pytest

from huey.banana_brain.config import BananaBrainConfig
from huey.banana_brain.job_models import Priority
from huey.banana_brain.priority_manager import PriorityManager

from .conftest import make_job

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def pm(test_config: BananaBrainConfig):
    # Tight aging so tests run quickly.
    cfg = BananaBrainConfig(
        priority_aging_interval_seconds=0.1,
        priority_aging_step=1,
        priority_aging_cap=99,
        priority_overdue_boost=20,
        database_path=test_config.database_path,
    )
    return PriorityManager(cfg)


def _submit(pm: PriorityManager, *, priority: int, submitted_at=None, deadline=None):
    job = make_job(priority=priority, deadline=deadline)
    job.submitted_at = submitted_at if submitted_at is not None else time.time()
    return job


# ---------------------------------------------------------------------------
# Basic ordering
# ---------------------------------------------------------------------------


async def test_fifo_at_equal_priority(pm):
    now = time.time()
    a = _submit(pm, priority=50, submitted_at=now - 5)
    b = _submit(pm, priority=50, submitted_at=now - 3)
    await pm.push(b)  # pushed out of order
    await pm.push(a)
    head = await pm.peek(now=now)
    assert head.id == a.id


async def test_priority_beats_fifo(pm):
    now = time.time()
    low = _submit(pm, priority=int(Priority.BATCH), submitted_at=now - 0.05)
    high = _submit(pm, priority=int(Priority.INTERACTIVE), submitted_at=now)
    await pm.push(low)
    await pm.push(high)
    head = await pm.peek(now=now)
    assert head.id == high.id


async def test_id_tiebreak_is_stable(pm):
    now = time.time()
    a = _submit(pm, priority=50, submitted_at=now)
    b = _submit(pm, priority=50, submitted_at=now)
    a.id = "aaa"
    b.id = "bbb"
    await pm.push(b)
    await pm.push(a)
    head = await pm.peek(now=now)
    assert head.id == "aaa"


# ---------------------------------------------------------------------------
# Aging
# ---------------------------------------------------------------------------


async def test_aging_promotes_long_waiting_job(pm):
    # Fresh interactive (80) vs old batch (20) aged past it.
    now = time.time()
    fresh = _submit(pm, priority=int(Priority.INTERACTIVE), submitted_at=now)
    # 70 units of aging = 70 priority, 20 + 70 = 90 > 80.
    old = _submit(pm, priority=int(Priority.BATCH), submitted_at=now - 7.0)
    await pm.push(fresh)
    await pm.push(old)
    head = await pm.peek(now=now)
    assert head.id == old.id


async def test_aging_capped_below_safety(pm):
    # A job waiting forever must not exceed the aging_cap (99 by default).
    now = time.time()
    safety = _submit(pm, priority=int(Priority.SAFETY), submitted_at=now)
    ancient = _submit(pm, priority=int(Priority.MAINTENANCE), submitted_at=now - 10_000)
    await pm.push(ancient)
    await pm.push(safety)
    head = await pm.peek(now=now)
    assert head.id == safety.id  # SAFETY = 100 > aging_cap = 99


async def test_aging_disabled_when_interval_zero(test_config):
    cfg = BananaBrainConfig(
        priority_aging_interval_seconds=0,
        database_path=test_config.database_path,
    )
    pm = PriorityManager(cfg)
    now = time.time()
    old = _submit(pm, priority=20, submitted_at=now - 10_000)
    fresh = _submit(pm, priority=80, submitted_at=now)
    await pm.push(old)
    await pm.push(fresh)
    assert (await pm.peek(now=now)).id == fresh.id


# ---------------------------------------------------------------------------
# Deadlines
# ---------------------------------------------------------------------------


async def test_deadline_ordering_within_priority(pm):
    now = time.time()
    later = _submit(pm, priority=50, submitted_at=now, deadline=now + 100)
    sooner = _submit(pm, priority=50, submitted_at=now, deadline=now + 10)
    await pm.push(later)
    await pm.push(sooner)
    head = await pm.peek(now=now)
    assert head.id == sooner.id


async def test_deadline_beats_no_deadline_at_equal_priority(pm):
    now = time.time()
    with_dl = _submit(pm, priority=50, submitted_at=now, deadline=now + 100)
    no_dl = _submit(pm, priority=50, submitted_at=now)
    await pm.push(no_dl)
    await pm.push(with_dl)
    head = await pm.peek(now=now)
    assert head.id == with_dl.id


async def test_deadline_does_not_override_priority(pm):
    now = time.time()
    low_soon = _submit(
        pm, priority=int(Priority.BATCH), submitted_at=now, deadline=now + 1
    )
    high_no_dl = _submit(pm, priority=int(Priority.INTERACTIVE), submitted_at=now)
    await pm.push(low_soon)
    await pm.push(high_no_dl)
    assert (await pm.peek(now=now)).id == high_no_dl.id


async def test_overdue_job_gets_boost(pm):
    now = time.time()
    # Batch at 20 with +20 overdue = 40; background at 40 wins on tie-break.
    # Make the overdue job meaningfully behind then boost it past.
    overdue = _submit(pm, priority=35, submitted_at=now, deadline=now - 10)
    competitor = _submit(pm, priority=50, submitted_at=now)
    await pm.push(overdue)
    await pm.push(competitor)
    # 35 + 20 = 55 > 50.
    assert (await pm.peek(now=now)).id == overdue.id


# ---------------------------------------------------------------------------
# remove / size / clear
# ---------------------------------------------------------------------------


async def test_remove_returns_job_or_none(pm):
    job = _submit(pm, priority=50)
    await pm.push(job)
    assert (await pm.remove(job.id)).id == job.id
    assert await pm.remove(job.id) is None


async def test_size_and_clear(pm):
    jobs = [_submit(pm, priority=50) for _ in range(3)]
    for j in jobs:
        await pm.push(j)
    assert await pm.size() == 3
    cleared = await pm.clear()
    assert len(cleared) == 3
    assert await pm.size() == 0


async def test_push_replaces_same_id(pm):
    a = _submit(pm, priority=50)
    await pm.push(a)
    a.priority = 60
    await pm.push(a)
    assert await pm.size() == 1
    head = await pm.peek()
    assert head.priority == 60


# ---------------------------------------------------------------------------
# Snapshot
# ---------------------------------------------------------------------------


async def test_snapshot_ordered_head_first(pm):
    now = time.time()
    low = _submit(pm, priority=20, submitted_at=now)
    high = _submit(pm, priority=80, submitted_at=now)
    await pm.push(low)
    await pm.push(high)
    snap = await pm.snapshot(now=now)
    assert snap["size"] == 2
    assert snap["entries"][0]["id"] == high.id
    assert (
        snap["entries"][0]["effective_priority"]
        > snap["entries"][1]["effective_priority"]
    )


async def test_snapshot_limit(pm):
    now = time.time()
    for i in range(5):
        await pm.push(_submit(pm, priority=i * 10, submitted_at=now))
    snap = await pm.snapshot(now=now, limit=2)
    assert snap["size"] == 5
    assert len(snap["entries"]) == 2


async def test_lifecycle_validation_and_empty_operations(pm, caplog):
    await pm.start()
    await pm.stop()
    assert await pm.remove("") is None
    assert await pm.peek() is None
    assert await pm.head_is_exclusive() is False
    assert pm.default_priority(None) == int(Priority.BACKGROUND)
    with pytest.raises(ValueError, match="non-empty id"):
        await pm.push(None)
    with pytest.raises(ValueError, match="non-empty id"):
        await pm.push(type("NoId", (), {"id": ""})())


async def test_lifecycle_discards_pending_jobs_and_exclusive_head(pm, caplog):
    job = _submit(pm, priority=int(Priority.INTERACTIVE))
    job.exclusive = True
    await pm.push(job)
    assert await pm.head_is_exclusive()
    await pm.stop()
    assert await pm.size() == 0
    assert "job(s) discarded" in caplog.text


async def test_aging_handles_missing_or_future_submission_time(pm):
    now = time.time()
    job = _submit(pm, priority=40)
    job.submitted_at = None
    assert pm._age(job, now) == 0
    job.submitted_at = now + 100
    assert pm._age(job, now) == 0


async def test_nonpositive_aging_step_disables_bonus(test_config):
    cfg = BananaBrainConfig(
        priority_aging_interval_seconds=1,
        priority_aging_step=0,
        database_path=test_config.database_path,
    )
    pm = PriorityManager(cfg)
    old = _submit(pm, priority=20, submitted_at=0)
    assert pm._aging_bonus(old, time.time()) == 0


def test_config_number_helper_accepts_mapping_and_attribute_defaults():
    from huey.banana_brain.priority_manager import _cfg_num

    assert _cfg_num({}, "missing", 4.0) == 4.0
    assert _cfg_num(SimpleNamespace(value=2), "value", 4.0) == 2.0
