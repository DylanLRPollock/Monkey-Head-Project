"""Mode admission, transitions, and safety overlay behavior."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from huey.banana_brain.gpu_modes import (
    GPUMode,
    GPUModeManager,
    ModeTransitionError,
    _cfg_bool,
    _cfg_num,
    _cfg_str,
    _maybe_str,
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


def test_mode_config_and_workload_predicates():
    assert _cfg_str({"name": 0}, "name") is None
    assert _cfg_num({"n": "3"}, "n", 2.5) == 2.5
    assert _cfg_bool({}, "enabled", True) is True
    assert _cfg_bool({"enabled": False}, "enabled", True) is False
    assert _cfg_bool({"enabled": " YES "}, "enabled", False) is True
    assert _cfg_bool({"enabled": "no"}, "enabled", True) is False
    assert _cfg_bool({"enabled": 1}, "enabled", False) is True
    assert _maybe_str(None) is None
    assert _maybe_str(12) == "12"
    assert GPUModeManager._is_maintenance_workload(
        Job(adapter="fake", payload={}, exclusive=True)
    )
    assert GPUModeManager._is_maintenance_workload(
        Job(adapter="fake", payload={}, priority=int(Priority.EXCLUSIVE))
    )
    assert GPUModeManager._is_maintenance_workload(
        Job(adapter="fake", payload={}, tags={"maintenance": True})
    )
    assert not GPUModeManager._is_maintenance_workload(
        SimpleNamespace(priority="invalid", exclusive=False, tags={})
    )


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


@pytest.mark.asyncio
async def test_noop_transition_and_repeated_halt_are_idempotent(scheduler, job_store):
    sched, adapter, _ = scheduler
    modes = manager(sched, job_store, adapters={"fake": adapter})
    same = await modes.set_mode("mixed", reason="no change")
    assert same.success and same.elapsed_s == 0
    await modes.force_safety_halt("thermal risk")
    await modes.force_safety_halt("duplicate event")
    assert modes._safety_halt_reason == "thermal risk"
    await modes.clear_safety_halt(reason="not required twice")
    await modes.clear_safety_halt(reason="already cleared")
    assert not modes.safety_halted


@pytest.mark.asyncio
async def test_bad_persisted_state_uses_configured_default(
    tmp_path, scheduler, job_store
):
    path = tmp_path / "mode.json"
    path.write_text("not json", encoding="utf-8")
    sched, adapter, _ = scheduler
    modes = GPUModeManager(
        {
            "mode_default": "image",
            "mode_persistence_enabled": True,
            "mode_state_path": str(path),
        },
        scheduler=sched,
        priority_manager=sched._priority_manager,
        job_store=job_store,
        adapters={"fake": adapter},
    )
    await modes.start()
    try:
        assert modes.current_mode is GPUMode.IMAGE
    finally:
        await modes.stop()


@pytest.mark.asyncio
async def test_persisted_exclusive_mode_restores_previous_nonexclusive_mode(
    tmp_path, scheduler, job_store
):
    path = tmp_path / "mode.json"
    path.write_text(
        '{"mode":"gaming","previous_non_exclusive_mode":"image"}',
        encoding="utf-8",
    )
    sched, adapter, _ = scheduler
    modes = GPUModeManager(
        {"mode_persistence_enabled": True, "mode_state_path": str(path)},
        scheduler=sched,
        priority_manager=sched._priority_manager,
        job_store=job_store,
        adapters={"fake": adapter},
    )
    await modes.start()
    try:
        assert modes.current_mode is GPUMode.GAMING
        result = await modes.resume_previous()
        assert result.to_mode is GPUMode.IMAGE
    finally:
        await modes.stop()


@pytest.mark.asyncio
async def test_resume_drops_missing_and_terminal_suspended_jobs():
    pending = Job(adapter="audio", payload={})
    terminal = Job(adapter="audio", payload={}, state=JobState.CANCELLED)

    class Store:
        async def get(self, job_id):
            return pending if job_id == pending.id else terminal

    push = AsyncMock()
    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(push=push),
        job_store=Store(),
        adapters={},
    )
    modes._suspended_jobs = [pending, terminal, Job(adapter="audio", payload={})]
    assert await modes._resume_all_suspended() == 1
    push.assert_awaited_once_with(pending)
    assert modes._suspended_jobs == []


@pytest.mark.asyncio
async def test_resume_discards_job_when_store_read_fails():
    job = Job(adapter="audio", payload={})

    class BrokenStore:
        async def get(self, _job_id):
            raise OSError("database offline")

    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(push=AsyncMock()),
        job_store=BrokenStore(),
        adapters={},
    )
    modes._suspended_jobs = [job]
    assert await modes._resume_all_suspended() == 0
    assert modes._suspended_jobs == []


@pytest.mark.asyncio
async def test_cancel_suspended_persistence_failure_is_best_effort():
    job = Job(adapter="audio", payload={})

    class BrokenStore:
        async def save(self, _job):
            raise OSError("database offline")

    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(),
        job_store=BrokenStore(),
        adapters={},
    )
    modes._suspended_jobs = [job]
    assert await modes.cancel_suspended(job.id)
    assert job.state is JobState.CANCELLED
    assert await modes.get_suspended() == []


def test_admission_install_failure_and_wake_fallback():
    event = asyncio.Event()

    def fail_install(_checker):
        raise RuntimeError("cannot install checker")

    def fail_wake():
        raise RuntimeError("wake unavailable")

    scheduler = SimpleNamespace(
        set_admission_checker=fail_install,
        request_dispatch=fail_wake,
        _wake=event,
    )
    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=scheduler,
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    assert not modes._install_admission_check()
    modes._wake_scheduler()
    assert event.is_set()


@pytest.mark.asyncio
async def test_stop_tolerates_admission_uninstall_failure():
    def setter(_checker):
        return None

    scheduler = SimpleNamespace(set_admission_checker=setter)
    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=scheduler,
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    modes._admission_installed = True
    scheduler.set_admission_checker = lambda _checker: (_ for _ in ()).throw(
        RuntimeError("setter failed")
    )
    await modes.stop()


@pytest.mark.asyncio
async def test_safety_halt_and_clear_survive_queue_errors():
    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    modes._suspend_non_matching = AsyncMock(side_effect=RuntimeError("drain failed"))
    modes._resume_all_suspended = AsyncMock(side_effect=RuntimeError("resume failed"))
    await modes.force_safety_halt("unsafe temperature")
    assert modes.safety_halted
    await modes.clear_safety_halt(reason="cooled", cleared_by="operator")
    assert not modes.safety_halted
    modes._suspend_non_matching.assert_awaited_once()
    modes._resume_all_suspended.assert_awaited_once()


@pytest.mark.asyncio
async def test_current_job_timeout_handles_cancel_failure():
    scheduler = SimpleNamespace(
        current_job=SimpleNamespace(id="busy"),
        cancel=AsyncMock(side_effect=RuntimeError("cancel unavailable")),
    )
    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=scheduler,
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    assert await modes._await_current_job(0, force=True) == "busy"
    assert await modes._await_current_job(0, force=False) == "busy"
    scheduler.current_job = None
    assert await modes._await_current_job(0, force=False) is None


@pytest.mark.asyncio
async def test_resume_push_failure_is_best_effort():
    job = Job(adapter="audio", payload={})

    class BrokenQueue:
        async def push(self, _job):
            raise OSError("queue unavailable")

    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=SimpleNamespace(),
        priority_manager=BrokenQueue(),
        job_store=SimpleNamespace(get=AsyncMock(return_value=job)),
        adapters={},
    )
    modes._suspended_jobs = [job]
    assert await modes._resume_all_suspended() == 0
    assert modes._suspended_jobs == []


@pytest.mark.asyncio
async def test_adapter_unload_errors_do_not_abort_mode_work():
    async def fail(_needed):
        raise RuntimeError("model busy")

    modes = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={"bad": SimpleNamespace(unload_idle_models=fail), "none": object()},
    )
    await modes._unload_all_adapters()


def test_persistence_rejects_non_object_state_and_ignores_write_errors(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("[]", encoding="utf-8")
    modes = GPUModeManager(
        {"mode_persistence_enabled": True, "mode_state_path": str(path)},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    assert modes._load_persisted_state() is None
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("file", encoding="utf-8")
    modes._state_path = blocked_parent / "mode.json"
    modes._save_persisted_state()


@pytest.mark.asyncio
async def test_mode_fallback_queue_and_housekeeping_branches(monkeypatch):
    from types import SimpleNamespace

    from huey.banana_brain.gpu_modes import GPUMode, GPUModeManager
    from huey.banana_brain.job_models import Job

    manager = GPUModeManager(
        {"mode_persistence_enabled": False, "mode_drain_interval_s": 0.001},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    assert manager._install_admission_check() is False

    manager._safety_halted = True
    result = await manager.set_mode(GPUMode.IMAGE, reason="test overlay")
    assert result.success is True
    assert manager.safety_halted is True

    class Queue:
        def __init__(self):
            self.jobs = [
                Job(adapter="ollama", payload={}),
                Job(adapter="ollama", payload={}),
            ]
            self.remove_calls = 0

        async def peek(self):
            return self.jobs[0] if self.jobs else None

        async def remove(self, job_id):
            self.remove_calls += 1
            if self.remove_calls == 1:
                self.jobs.pop(0)
                return None
            return self.jobs.pop(0)

        async def push(self, _job):
            raise RuntimeError("queue restore failed")

    manager._priority_manager = Queue()
    manager.is_admission_allowed = lambda _job: True
    assert await manager._suspend_non_matching() == 0

    class Unloader:
        async def unload_idle_models(self, _amount):
            return 1024

    manager._adapters = {"test": Unloader()}
    await manager._unload_all_adapters()

    calls = 0

    async def controlled_wait(awaitable, _timeout):
        nonlocal calls
        calls += 1
        if calls % 2:
            awaitable.close()
            raise TimeoutError
        manager._housekeeping_stop.set()
        return await awaitable

    monkeypatch.setattr(asyncio, "wait_for", controlled_wait)
    manager._current_mode = GPUMode.AI
    await manager._housekeeping_loop()

    async def fail_drain():
        raise RuntimeError("drain unavailable")

    manager._housekeeping_stop.clear()
    calls = 0
    manager._current_mode = GPUMode.MAINTENANCE
    manager._suspend_non_matching = fail_drain
    await manager._housekeeping_loop()
