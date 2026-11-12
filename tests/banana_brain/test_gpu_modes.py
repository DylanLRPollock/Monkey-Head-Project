"""Mode admission, transitions, and safety overlay behavior."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from huey.banana_brain.gpu_modes import (
    GPUMode,
    GPUModeManager,
    ModeTransitionError,
    _parse_mode,
)
from huey.banana_brain.job_models import Job, JobState, Priority


def manager(scheduler, job_store, *, adapters=None):
    return GPUModeManager(
        {"mode_persistence_enabled": False, "mode_transition_timeout_s": 0.01},
        scheduler=scheduler,
        priority_manager=scheduler._priority_manager,
        job_store=job_store,
        adapters=adapters or {},
    )


def test_parse_mode_accepts_names_and_rejects_unknown():
    assert _parse_mode("gaming") is GPUMode.GAMING
    assert _parse_mode(GPUMode.AI) is GPUMode.AI
    with pytest.raises(ModeTransitionError):
        _parse_mode("invalid")


@pytest.mark.asyncio
async def test_mode_transition_suspends_and_restores_pending_jobs(scheduler, job_store):
    sched, adapter, _ = scheduler
    modes = manager(sched, job_store, adapters={"fake": adapter})
    await modes.start()
    try:
        job = Job(adapter="fake", payload={}, priority=int(Priority.INTERACTIVE))
        await job_store.save(job)
        await sched._priority_manager.push(job)
        result = await modes.set_mode("gaming", reason="operator session")
        assert result.success
        assert result.suspended_count == 1
        assert modes.current_mode is GPUMode.GAMING
        assert not modes.is_admission_allowed(job)
        assert (await modes.get_suspended())[0]["id"] == job.id

        await modes.set_mode("ai", reason="resume workloads")
        assert modes.current_mode is GPUMode.AI
        assert await sched._priority_manager.size() == 1
        assert await modes.get_suspended() == []
    finally:
        await modes.stop()


@pytest.mark.asyncio
async def test_maintenance_admits_only_maintenance_jobs(scheduler, job_store):
    sched, adapter, _ = scheduler
    modes = manager(sched, job_store, adapters={"fake": adapter})
    await modes.start()
    try:
        await modes.set_mode(GPUMode.MAINTENANCE, reason="benchmark")
        maintenance = Job(
            adapter="fake",
            payload={"task": "benchmark"},
            priority=int(Priority.MAINTENANCE),
            tags={"maintenance": "yes"},
        )
        normal = Job(
            adapter="fake",
            payload={"task": "generate"},
            priority=int(Priority.INTERACTIVE),
        )
        assert modes.is_admission_allowed(maintenance)
        assert not modes.is_admission_allowed(normal)
        assert await modes.resume_previous()
        assert modes.current_mode is GPUMode.MIXED
    finally:
        await modes.stop()


@pytest.mark.asyncio
async def test_safety_halt_blocks_jobs_then_clear_resumes_queue(scheduler, job_store):
    sched, adapter, _ = scheduler
    modes = manager(sched, job_store, adapters={"fake": adapter})
    await modes.start()
    try:
        job = Job(adapter="fake", payload={})
        await job_store.save(job)
        await sched._priority_manager.push(job)
        await modes.force_safety_halt("over temperature")
        assert modes.safety_halted
        assert not modes.is_admission_allowed(job)
        assert await modes.get_suspended()

        await modes.clear_safety_halt(
            reason="temperature normal", cleared_by="operator"
        )
        assert not modes.safety_halted
        assert await sched._priority_manager.size() == 1
    finally:
        await modes.stop()


@pytest.mark.asyncio
async def test_cancel_suspended_persists_terminal_state(scheduler, job_store):
    sched, adapter, _ = scheduler
    modes = manager(sched, job_store, adapters={"fake": adapter})
    await modes.start()
    try:
        job = Job(adapter="fake", payload={})
        await job_store.save(job)
        await sched._priority_manager.push(job)
        await modes.set_mode("gaming", reason="pause queue")
        assert await modes.cancel_suspended(job.id)
        assert not await modes.cancel_suspended(job.id)
        assert (await job_store.get(job.id)).state is JobState.CANCELLED
        assert await modes.get_suspended() == []
        state = await modes.get_state()
        assert state["mode"] == "gaming"
        assert state["suspended_jobs"] == 0
    finally:
        await modes.stop()


@pytest.mark.asyncio
async def test_housekeeping_suspends_jobs_added_during_exclusive_mode(
    scheduler, job_store
):
    sched, adapter, _ = scheduler
    modes = GPUModeManager(
        {"mode_persistence_enabled": False, "mode_drain_interval_s": 0.01},
        scheduler=sched,
        priority_manager=sched._priority_manager,
        job_store=job_store,
        adapters={"fake": adapter},
    )
    await modes.start()
    try:
        await modes.set_mode("gaming", reason="exclusive")
        job = Job(adapter="fake", payload={})
        await job_store.save(job)
        await sched._priority_manager.push(job)
        for _ in range(50):
            if await modes.get_suspended():
                break
            await asyncio.sleep(0.01)
        assert (await modes.get_suspended())[0]["id"] == job.id
    finally:
        await modes.stop()


@pytest.mark.asyncio
async def test_mode_is_persisted_and_restored(tmp_path, scheduler, job_store):
    sched, adapter, _ = scheduler
    config = {
        "mode_persistence_enabled": True,
        "mode_state_path": str(tmp_path / "mode.json"),
    }
    modes = GPUModeManager(
        config,
        scheduler=sched,
        priority_manager=sched._priority_manager,
        job_store=job_store,
        adapters={"fake": adapter},
    )
    await modes.start()
    await modes.set_mode("image", reason="image work", requested_by="cli")
    await modes.stop()
    restored = GPUModeManager(
        config,
        scheduler=sched,
        priority_manager=sched._priority_manager,
        job_store=job_store,
        adapters={"fake": adapter},
    )
    await restored.start()
    try:
        assert restored.current_mode is GPUMode.IMAGE
        state = await restored.get_state()
        assert state["mode_reason"] == "image work"
        assert state["mode_requested_by"] == "cli"
    finally:
        await restored.stop()


@pytest.mark.asyncio
async def test_forced_mode_transition_reports_still_running_job():
    current = SimpleNamespace(id="busy-job")
    scheduler = SimpleNamespace(
        current_job=current,
        set_admission_checker=lambda checker: None,
        request_dispatch=lambda: None,
        cancel=AsyncMock(return_value=True),
    )
    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=scheduler,
        priority_manager=SimpleNamespace(peek=AsyncMock(return_value=None)),
        job_store=SimpleNamespace(),
        adapters={},
    )
    result = await modes.set_mode("gaming", reason="operator", force=True, timeout=0)
    assert not result.success
    assert result.interrupted_job_id == "busy-job"
    assert "still running" in result.error
    scheduler.cancel.assert_awaited_once_with("busy-job", force=True)
