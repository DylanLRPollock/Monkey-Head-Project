"""Mode admission, transitions, and safety overlay behavior."""

import pytest

from huey.banana_brain.gpu_modes import (
    GPUMode,
    GPUModeManager,
    ModeTransitionError,
    _parse_mode,
)
from huey.banana_brain.job_models import Job, Priority


def manager(scheduler, job_store, test_config, *, adapters=None):
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
    modes = manager(sched, job_store, None, adapters={"fake": adapter})
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
    modes = manager(sched, job_store, None, adapters={"fake": adapter})
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
    modes = manager(sched, job_store, None, adapters={"fake": adapter})
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
