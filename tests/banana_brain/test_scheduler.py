"""Tests for huey.banana_brain.scheduler."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from huey.banana_brain.job_models import JobState, Priority
from huey.banana_brain.scheduler import (
    JobNotCancellable,
    SchedulerError,
    SchedulerShuttingDown,
)

from .conftest import make_job, wait_until

# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


async def test_scheduler_start_and_stop(scheduler):
    sched, _adapter, _ = scheduler
    status = await sched.status()
    assert status["shutting_down"] is False
    assert status["current_job_id"] is None
    assert "fake" in status["adapters"]


async def test_double_start_raises(scheduler, test_config, job_store, fake_nvml):
    sched, _, _monitor = scheduler
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


async def test_scheduler_idle_timeout_and_dispatch_guards(scheduler):
    sched, _, _ = scheduler
    sched.set_admission_checker(lambda _job: False)
    job = make_job()
    job.id = None
    job.priority = None
    submitted = await sched.submit(job)
    assert submitted.id
    assert submitted.priority is not None
    assert await sched.wait_until_empty(timeout=0) is False
    assert await sched._try_dispatch_next() is False

    def broken_checker(_job):
        raise RuntimeError("policy unavailable")

    sched.set_admission_checker(broken_checker)
    assert await sched._try_dispatch_next() is False

    sched.set_admission_checker(None)
    sched._shutting_down = True
    assert await sched._try_dispatch_next() is False
    sched._shutting_down = False
    sched._current_job = submitted
    assert await sched._try_dispatch_next() is False
    sched._current_job = None
    assert await sched.cancel(submitted.id) is True
    assert await sched.wait_until_empty(timeout=0) is True


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
    # Hold dispatch until both jobs are queued so the assertion measures
    # queue priority rather than submission timing.
    sched.set_admission_checker(lambda job: False)
    low = await sched.submit(make_job(priority=int(Priority.BATCH)))
    high = await sched.submit(make_job(priority=int(Priority.INTERACTIVE)))
    sched.set_admission_checker(None)
    sched.request_dispatch()

    async def both_done():
        a = await job_store.get(low.id)
        b = await job_store.get(high.id)
        return (
            a is not None
            and a.state.is_terminal
            and b is not None
            and b.state.is_terminal
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
    await sched.submit(make_job())
    await wait_until(lambda: sched.current_job is not None, timeout=1.0)
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
        lambda: sched.current_job is not None and sched.current_job.id == running.id,
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
        lambda: sched.current_job is not None and sched.current_job.id == running.id,
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
    await wait_until(lambda: sched.current_job is not None, timeout=1.0)

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
    await wait_until(lambda: sched.current_job is not None, timeout=1.0)
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


async def test_vram_mark_running_called(scheduler, job_store, fake_nvml):
    """
    Regression test for the noted patch: scheduler._run_job must call
    vram_manager.mark_running() so the reservation state transitions
    from RESERVED to ACTIVE. Without this, concurrency would double-count
    reserved bytes and deadlock.
    """
    sched, _adapter, _ = scheduler
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


async def test_dispatch_waits_when_gpu_state_unknown(scheduler, job_store, fake_nvml):
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
    sched.request_dispatch()
    await wait_until(lambda: len(adapter.executed) == 1, timeout=3.0)


async def test_estimate_vram_prefers_explicit_then_uses_default_on_adapter_error(
    scheduler,
):
    sched, adapter, _ = scheduler
    explicit = make_job(estimated_vram_bytes=1234)
    assert await sched._estimate_vram(explicit) == 1234

    async def fail_estimate(_job):
        raise RuntimeError("estimate unavailable")

    adapter.estimate_vram = fail_estimate
    unestimated = make_job()
    assert await sched._estimate_vram(unestimated) == sched.DEFAULT_VRAM_ESTIMATE_BYTES


async def test_reservation_retries_after_adapter_releases_memory(scheduler):
    sched, adapter, monitor = scheduler
    required = 4 * 1024**3
    monitor.get_status = AsyncMock(
        side_effect=[
            SimpleNamespace(free_vram_bytes=1),
            SimpleNamespace(free_vram_bytes=required + 1),
        ]
    )
    sched._vram_manager.try_reserve = AsyncMock(side_effect=[False, True])

    async def unload(_needed):
        return required

    adapter.on_unload = unload
    assert await sched._reserve_memory(make_job(), required)
    assert adapter.unload_calls == [required]
    assert sched._vram_manager.try_reserve.await_count == 2


async def test_reservation_fails_closed_when_monitor_unavailable(scheduler):
    sched, _, monitor = scheduler
    monitor.get_status = AsyncMock(return_value=None)
    assert not await sched._free_memory_for(make_job(), 100)


async def test_persistence_failure_does_not_abort_scheduler(scheduler, job_store):
    sched, _, _ = scheduler
    job_store.save = AsyncMock(side_effect=OSError("database unavailable"))
    await sched._persist(make_job())
    job_store.save.assert_awaited_once()


async def test_recovery_store_failure_is_logged_and_ignored(scheduler, job_store):
    sched, _, _ = scheduler
    job_store.list_by_state = AsyncMock(side_effect=OSError("database unavailable"))
    await sched._recover_unfinished()
    job_store.list_by_state.assert_awaited_once()


async def test_submit_normalizes_missing_id_and_default_priority(scheduler):
    sched, _, _ = scheduler
    sched._priority_manager.default_priority = lambda _job: int(Priority.BACKGROUND)
    job = make_job(id="", priority=None, submitted_at=0, attempts=0)
    submitted = await sched.submit(job)
    assert submitted.id
    assert submitted.priority == int(Priority.BACKGROUND)
    assert submitted.submitted_at > 0
    assert submitted.started_at is None
    assert submitted.finished_at is None
    assert submitted.attempts == 0


async def test_submit_requires_adapter(scheduler):
    sched, _, _ = scheduler
    with pytest.raises(SchedulerError, match=r"job.adapter is required"):
        await sched.submit(SimpleNamespace(adapter=None, id="", priority=0))


async def test_wait_until_empty_reports_empty_and_timeout(scheduler):
    sched, _, _ = scheduler
    assert await sched.wait_until_empty(timeout=0.1) is True
    sched.set_admission_checker(lambda _job: False)
    await sched.submit(make_job())
    assert await sched.wait_until_empty(timeout=0) is False


async def test_cancel_force_swallows_adapter_cancel_error(scheduler):
    sched, adapter, _ = scheduler
    running = make_job()
    sched._current_job = running

    async def fail_cancel(_job):
        raise RuntimeError("adapter cancel failed")

    adapter.request_cancel = fail_cancel
    assert await sched.cancel(running.id, force=True) is True
    sched._current_job = None


async def test_reserve_memory_fails_when_manager_raises(scheduler):
    sched, _, _ = scheduler
    sched._vram_manager.try_reserve = AsyncMock(
        side_effect=RuntimeError("reservation failed")
    )
    assert await sched._reserve_memory(make_job(), 100) is False


async def test_reserve_memory_fails_when_retry_raises(scheduler):
    sched, adapter, monitor = scheduler
    monitor.get_status = AsyncMock(
        side_effect=[
            SimpleNamespace(free_vram_bytes=1),
            SimpleNamespace(free_vram_bytes=101),
        ]
    )
    sched._vram_manager.try_reserve = AsyncMock(
        side_effect=[False, RuntimeError("retry failed")]
    )
    adapter.on_unload = AsyncMock(return_value=100)
    assert await sched._reserve_memory(make_job(), 100) is False


async def test_free_memory_continues_after_unload_error_and_requires_delta(scheduler):
    sched, adapter, monitor = scheduler
    monitor.get_status = AsyncMock(
        side_effect=[
            SimpleNamespace(free_vram_bytes=100),
            SimpleNamespace(free_vram_bytes=100),
        ]
    )
    adapter.on_unload = AsyncMock(side_effect=RuntimeError("unload failed"))
    assert await sched._free_memory_for(make_job(), 20) is False
    adapter.on_unload.assert_awaited_once_with(20)


async def test_dispatch_refuses_when_admission_checker_raises(scheduler):
    sched, _, _ = scheduler
    sched.set_admission_checker(lambda _job: (_ for _ in ()).throw(ValueError()))
    await sched._priority_manager.push(make_job())
    assert await sched._try_dispatch_next() is False


async def test_dispatch_releases_reservation_when_job_disappears(scheduler):
    sched, _, _ = scheduler
    job = make_job()
    await sched._priority_manager.push(job)
    sched._vram_manager.try_reserve = AsyncMock(return_value=True)
    sched._priority_manager.remove = AsyncMock(return_value=None)
    sched._vram_manager.release = Mock()
    assert await sched._try_dispatch_next() is False
    sched._vram_manager.release.assert_called_once_with(job)


async def test_run_job_marks_missing_adapter_failed(scheduler, job_store):
    sched, _, _ = scheduler
    job = make_job(adapter="removed")
    await sched._run_job(job)
    assert job.state is JobState.FAILED
    assert "no adapter registered" in job.last_error
    assert job.finished_at is not None


async def test_run_job_propagates_cancellation_after_persisting(scheduler):
    sched, adapter, _ = scheduler

    async def cancel(_job):
        raise asyncio.CancelledError

    adapter.on_execute = cancel
    job = make_job()
    with pytest.raises(asyncio.CancelledError):
        await sched._run_job(job)
    assert job.state is JobState.CANCELLED
    assert job.finished_at is not None


async def test_stop_cancels_dispatch_task_that_does_not_join(scheduler):
    sched, _, _ = scheduler
    current = sched._dispatch_task
    current.cancel()
    with pytest.raises(asyncio.CancelledError):
        await current
    sched._dispatch_task = asyncio.create_task(asyncio.sleep(30))
    sched._idle.set()
    sched.DISPATCH_TASK_JOIN_S = 0
    await sched.stop()
    assert sched._dispatch_task is None


async def test_dispatch_loop_recovers_from_iteration_error_and_timeout(scheduler):
    sched, _, _ = scheduler
    await sched.stop()
    sched._shutting_down = False
    sched.REFRESH_INTERVAL_S = 0.001
    attempts = 0

    async def dispatch_once():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient dispatch failure")
        sched._shutting_down = True
        return False

    sched._try_dispatch_next = dispatch_once
    await sched._dispatch_loop()
    assert attempts == 2
    assert sched._idle.is_set()


@pytest.mark.asyncio
async def test_remaining_scheduler_lifecycle_branches(scheduler, monkeypatch):
    sched, adapter, _ = scheduler

    current = make_job(id="busy", state=JobState.RUNNING)
    sched._current_job = current
    assert await sched.wait_until_empty(timeout=0.01) is False
    assert sched.is_shutting_down is False

    monkeypatch.setattr(adapter, "request_cancel", None, raising=False)
    assert await sched.cancel("busy", force=True) is True
    sched._current_job = None

    def fail_mark_running(_job):
        raise RuntimeError("reservation state unavailable")

    monkeypatch.setattr(sched._vram_manager, "mark_running", fail_mark_running)
    await sched._run_job(make_job())
    monkeypatch.undo()

    async def cancelled_dispatch():
        raise asyncio.CancelledError

    monkeypatch.setattr(sched, "_try_dispatch_next", cancelled_dispatch)
    with pytest.raises(asyncio.CancelledError):
        await sched._dispatch_loop()
    monkeypatch.undo()

    before = SimpleNamespace(free_vram_bytes=100)

    status_values = iter((before, None))

    async def get_status():
        return next(status_values)

    monkeypatch.setattr(sched._gpu_monitor, "get_status", get_status)
    sched._adapters["without-unloader"] = object()
    assert await sched._free_memory_for(make_job(), 10) is False
