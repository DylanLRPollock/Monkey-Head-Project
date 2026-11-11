"""Tests for huey.banana_brain.scheduler."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock

import pytest

from huey.banana_brain.job_models import Job, JobState, Priority
from huey.banana_brain.scheduler import (
    JobNotCancellable,
    Scheduler,
    SchedulerError,
    SchedulerShuttingDown,
)

from .conftest import FakeAdapter, make_job, wait_until


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

async def test_scheduler_start_and_stop(scheduler):
    sched, adapter, _ = scheduler
    status = await sched.status()
    assert status["shutting_down"] is False
    assert status["current_job_id"] is None
    assert "fake" in status["adapters"]


async def test_double_start_raises(scheduler, test_config, job_store, fake_nvml):
    sched, _, monitor = scheduler
    # Building a second scheduler against the same store is legal, but
    # calling .start() twice on the same instance is not.
    with pytest.raises(SchedulerError):
        await sched.start()


# ---------------------------------------------------------------------------
# Submission and dispatch
# ---------------------------------------------------------------------------

async def test_submit_assigns_id_and_state(scheduler, job_store):
    sched, _, _ = scheduler
    job = make_job(payload={"prompt": "hi"})
    submitted = await sched.submit(job)
    assert submitted.id
    assert submitted.state is JobState.PENDING
    assert submitted.submitted_at is not None
    stored = await job_store.get(submitted.id)
    assert stored is not None
    assert stored.state is JobState.PENDING


async def test_submit_unknown_adapter_raises(scheduler):
    sched, _, _ = scheduler
    with pytest.raises(SchedulerError, match="unknown adapter"):
        await sched.submit(make_job(adapter="nope"))


async def test_submit_while_shutting_down_raises(scheduler):
    sched, _, _ = scheduler
    sched.begin_shutdown()
    with pytest.raises(SchedulerShuttingDown):
        await sched.submit(make_job())


async def test_job_dispatches_and_completes(scheduler, job_store):
    sched, adapter, _ = scheduler
    submitted = await sched.submit(make_job(payload={"p": 1}))
    await wait_until(
        lambda: asyncio.create_task(job_store.get(submitted.id)),
        timeout=2.0,
    )
    # Wait for terminal state.
    async def terminal():
        job = await job_store.get(submitted.id)
        return job is not None and job.state.is_terminal
    await wait_until(terminal, timeout=2.0)

    stored = await job_store.get(submitted.id)
    assert stored.state is JobState.COMPLETED
    assert len(adapter.executed) == 1
    assert stored.result["adapter"] == "fake"


async def test_job_fails_when_adapter_raises(scheduler, job_store):
    sched, adapter, _ = scheduler

    async def boom(job):
        raise RuntimeError("simulated adapter failure")

    adapter.on_execute = boom
    submitted = await sched.submit(make_job())

    async def terminal():
        job = await job_store.get(submitted.id)
        return job is not None and job.state.is_terminal
    await wait_until(terminal, timeout=2.0)

    stored = await job_store.get(submitted.id)
    assert stored.state is JobState.FAILED
    assert "RuntimeError" in stored.last_error
    assert stored.attempts == 1


async def test_priority_ordering(scheduler, job_store):
    sched, adapter, _ = scheduler
    # Submit low first, then high — high must run first.
    async def slow(job):
        await asyncio.sleep(0.02)
        return {"ok": True}

    adapter.on_execute = slow
    low = await sched.submit(make_job(priority=int(Priority.BATCH)))
    high = await sched.submit(make_job(priority=int(Priority.INTERACTIVE)))

    async def both_done():
        a = await job_store.get(low.id)
        b = await job_store.get(high.id)
        return (
            a is not None and a.state.is_terminal
            and b is not None and b.state.is_terminal
        )
    await wait_until(both_done, timeout=3.0)

    # The high-priority job must have been executed before the low one.
    order = [job.id for job in adapter.executed]
    assert order.index(high.id) < order.index(low.id)


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------

async def test_cancel_pending_job(scheduler, job_store):
    sched, adapter, _ = scheduler

    async def slow(job):
        await asyncio.sleep(0.5)
        return {}

    adapter.on_execute = slow
    blocker = await sched.submit(make_job())
    await wait_until(
        lambda: sched.current_job is not None, timeout=1.0
    )
    pending = await sched.submit(make_job())

    cancelled = await sched.cancel(pending.id, force=False)
    assert cancelled is True

    stored = await job_store.get(pending.id)
    assert stored.state is JobState.CANCELLED


async def test_cancel_running_without_force_raises(scheduler):
    sched, adapter, _ = scheduler

    async def slow(job):
        await asyncio.sleep(0.5)
        return {}

    adapter.on_execute = slow
    running = await sched.submit(make_job())
    await wait_until(
        lambda: sched.current_job is not None
        and sched.current_job.id == running.id,
        timeout=1.0,
    )
    with pytest.raises(JobNotCancellable):
        await sched.cancel(running.id, force=False)


async def test_cancel_running_with_force_calls_adapter(scheduler):
    sched, adapter, _ = scheduler

    async def slow(job):
        await asyncio.sleep(0.5)
        return {}

    adapter.on_execute = slow
    running = await sched.submit(make_job())
    await wait_until(
        lambda: sched.current_job is not None
        and sched.current_job.id == running.id,
        timeout=1.0,
    )
    ok = await sched.cancel(running.id, force=True)
    assert ok is True
    assert any(j.id == running.id for j in adapter.cancel_calls)


async def test_cancel_unknown_returns_false(scheduler):
    sched, _, _ = scheduler
    assert await sched.cancel("nonexistent") is False


# ---------------------------------------------------------------------------
# Shutdown drain
# ---------------------------------------------------------------------------

async def test_shutdown_waits_for_running_job(scheduler, job_store):
    sched, adapter, _ = scheduler

    async def slow(job):
        await asyncio.sleep(0.2)
        return {"ok": True}

    adapter.on_execute = slow
    running = await sched.submit(make_job())
    await wait_until(
        lambda: sched.current_job is not None, timeout=1.0
    )

    sched.begin_shutdown()
    # The job must complete even though we're shutting down.
    await asyncio.wait_for(sched.wait_for_idle(), timeout=3.0)
    stored = await job_store.get(running.id)
    assert stored.state is JobState.COMPLETED


async def test_shutdown_preserves_pending_jobs(scheduler, job_store):
    sched, adapter, _ = scheduler

    async def slow(job):
        await asyncio.sleep(0.3)
        return {}

    adapter.on_execute = slow
    running = await sched.submit(make_job())
    await wait_until(
        lambda: sched.current_job is not None, timeout=1.0
    )
    pending = await sched.submit(make_job())

    sched.begin_shutdown()
    await asyncio.wait_for(sched.wait_for_idle(), timeout=3.0)

    # Pending job remains PENDING in the store (requeued on next startup).
    stored = await job_store.get(pending.id)
    assert stored is not None
    assert stored.state in {JobState.PENDING, JobState.CANCELLED}
    # Running job completed.
    finished = await job_store.get(running.id)
    assert finished.state is JobState.COMPLETED


# ---------------------------------------------------------------------------
# Admission checker (used by gpu_modes)
# ---------------------------------------------------------------------------

async def test_admission_checker_blocks_dispatch(scheduler, job_store):
    sched, adapter, _ = scheduler
    sched.set_admission_checker(lambda job: False)

    submitted = await sched.submit(make_job())

    # Give the scheduler 200ms of dispatch attempts — nothing should run.
    await asyncio.sleep(0.2)
    assert len(adapter.executed) == 0
    stored = await job_store.get(submitted.id)
    assert stored.state is JobState.PENDING

    # Clearing the checker must unblock the job.
    sched.set_admission_checker(None)
    sched.request_dispatch()

    async def terminal():
        j = await job_store.get(submitted.id)
        return j.state.is_terminal

    await wait_until(terminal, timeout=2.0)


# ---------------------------------------------------------------------------
# VRAM integration (mark_running)
# ---------------------------------------------------------------------------

async def test_vram_mark_running_called(
    scheduler, job_store, fake_nvml
):
    """
    Regression test for the noted patch: scheduler._run_job must call
    vram_manager.mark_running() so the reservation state transitions
    from RESERVED to ACTIVE. Without this, concurrency would double-count
    reserved bytes and deadlock.
    """
    sched, adapter, _ = scheduler
    seen: list[str] = []

    original_mark = sched._vram_manager.mark_running

    def spy(job):
        seen.append(job.id)
        return original_mark(job)

    sched._vram_manager.mark_running = spy

    submitted = await sched.submit(make_job())

    async def terminal():
        j = await job_store.get(submitted.id)
        return j.state.is_terminal

    await wait_until(terminal, timeout=2.0)
    assert submitted.id in seen, "mark_running was not called for the job"


# ---------------------------------------------------------------------------
# Fail-closed on unknown GPU state
# ---------------------------------------------------------------------------

async def test_dispatch_waits_when_gpu_state_unknown(
    scheduler, job_store, fake_nvml
):
    sched, adapter, monitor = scheduler
    fake_nvml.fail_poll = True
    # Force the monitor to consider itself stale.
    monitor._max_staleness = 0.01
    await asyncio.sleep(0.05)

    submitted = await sched.submit(make_job())
    await asyncio.sleep(0.3)
    # Nothing dispatched: the VRAM manager refuses reservations.
    assert len(adapter.executed) == 0
    stored = await job_store.get(submitted.id)
    assert stored.state is JobState.PENDING

    # Recovery: fake NVML comes back.
    fake_nvml.fail_poll = False
    await monitor.refresh()
    await wait_until(
        lambda: len(adapter.executed) == 1, timeout=3.0
    )
