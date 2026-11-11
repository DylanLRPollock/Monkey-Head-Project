"""
Integration tests exercising the full composition root with stub adapters
and a fake NVML.

Covers:
  * End-to-end dispatch through the real scheduler + vram_manager +
    priority_manager with fake adapters.
  * The Ollama-then-ComfyUI take-turns scenario from the design doc.
  * Mode transition to GAMING suspends dispatch.
  * Safety halt via watchdog thermal event.
  * Shutdown drain.
"""

from __future__ import annotations

import asyncio
import time

import pytest
import pytest_asyncio

from huey.banana_brain.config import BananaBrainConfig
from huey.banana_brain.gpu_modes import GPUMode, GPUModeManager
from huey.banana_brain.gpu_monitor import GPUMonitor
from huey.banana_brain.job_models import JobState, Priority
from huey.banana_brain.job_store import JobStore
from huey.banana_brain.priority_manager import PriorityManager
from huey.banana_brain.scheduler import Scheduler
from huey.banana_brain.vram_manager import VRAMManager
from huey.banana_brain.watchdog import Severity, Watchdog

from .conftest import FakeAdapter, make_job, wait_until


GIB = 1024 ** 3


# ---------------------------------------------------------------------------
# Composition fixture
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def stack(test_config, fake_nvml, tmp_path):
    """
    Build the composition root with fake adapters and fake NVML.

    Yields a dict with all components for tests to manipulate.
    """
    cfg = BananaBrainConfig(
        shutdown_grace_seconds=3.0,
        poll_interval_seconds=0.05,
        max_staleness_seconds=1.0,
        vram_headroom_gib=1.0,
        priority_aging_interval_seconds=0.2,
        database_path=tmp_path / "integration.db",
        job_retention_days=0,
        job_max_terminal_rows=0,
        job_prune_interval_seconds=0,
        api_socket_path=tmp_path / "integration.sock",
        metrics_enabled=False,
        notifications_enabled=False,
        mode_persistence_enabled=False,
        watchdog_check_interval_seconds=0.05,
        watchdog_temperature_warn_c=70,
        watchdog_temperature_ceiling_c=80,
        watchdog_gpu_unavailable_warn_s=0.1,
        watchdog_gpu_unavailable_critical_s=0.3,
        watchdog_stuck_job_seconds=10,
        watchdog_lease_expiry_seconds=10,
    )

    store = JobStore(cfg)
    await store.start()
    monitor = GPUMonitor(cfg)
    await monitor.start()
    vram = VRAMManager(cfg, monitor)
    pm = PriorityManager(cfg)

    ollama = FakeAdapter("ollama", estimate_bytes=22 * GIB)
    comfyui = FakeAdapter("comfyui", estimate_bytes=8 * GIB)

    sched = Scheduler(
        config=cfg,
        job_store=store,
        gpu_monitor=monitor,
        vram_manager=vram,
        priority_manager=pm,
        adapters={"ollama": ollama, "comfyui": comfyui},
    )

    modes = GPUModeManager(
        cfg,
        scheduler=sched,
        priority_manager=pm,
        job_store=store,
        adapters={"ollama": ollama, "comfyui": comfyui},
    )

    watchdog = Watchdog(
        cfg,
        scheduler=sched,
        gpu_monitor=monitor,
        vram_manager=vram,
        job_store=store,
        adapters={"ollama": ollama, "comfyui": comfyui},
        mode_manager=modes,
    )

    await modes.start()
    await sched.start()
    await watchdog.start()

    try:
        yield {
            "config": cfg,
            "store": store,
            "monitor": monitor,
            "vram": vram,
            "pm": pm,
            "ollama": ollama,
            "comfyui": comfyui,
            "scheduler": sched,
            "modes": modes,
            "watchdog": watchdog,
            "fake_nvml": fake_nvml,
        }
    finally:
        await watchdog.stop()
        await sched.stop()
        await modes.stop()
        await monitor.stop()
        await store.stop()


# ---------------------------------------------------------------------------
# Take-turns scenario
# ---------------------------------------------------------------------------

async def test_ollama_then_comfyui_serial_dispatch(stack):
    sched = stack["scheduler"]
    ollama = stack["ollama"]
    comfyui = stack["comfyui"]
    store = stack["store"]

    # Simulate realistic durations so they truly serialise.
    async def ollama_run(job):
        await asyncio.sleep(0.15)
        return {"ok": True, "who": "ollama"}

    async def comfyui_run(job):
        await asyncio.sleep(0.15)
        return {"ok": True, "who": "comfyui"}

    ollama.on_execute = ollama_run
    comfyui.on_execute = comfyui_run

    a = await sched.submit(
        make_job(adapter="ollama", priority=int(Priority.INTERACTIVE),
                 payload={"prompt": "hi"})
    )
    b = await sched.submit(
        make_job(adapter="comfyui", priority=int(Priority.IMAGE),
                 payload={"workflow": {}})
    )

    async def both_done():
        ja = await store.get(a.id)
        jb = await store.get(b.id)
        return ja.state.is_terminal and jb.state.is_terminal

    await wait_until(both_done, timeout=5.0)

    # They must have run one after the other, not concurrently.
    events = []
    events.append((ollama.executed[0].started_at, "ollama_start"))
    events.append((comfyui.executed[0].started_at, "comfyui_start"))
    assert len(ollama.executed) == 1
    assert len(comfyui.executed) == 1
    # Ollama ran first (higher priority).
    assert ollama.executed[0].started_at < comfyui.executed[0].started_at


# ---------------------------------------------------------------------------
# Mode transition: GAMING blocks dispatch
# ---------------------------------------------------------------------------

async def test_gaming_mode_blocks_dispatch(stack):
    sched = stack["scheduler"]
    modes = stack["modes"]
    adapter = stack["ollama"]
    store = stack["store"]

    async def slow(job):
        await asyncio.sleep(0.3)
        return {"ok": True}

    adapter.on_execute = slow

    running = await sched.submit(make_job(adapter="ollama"))
    await wait_until(
        lambda: sched.current_job is not None, timeout=1.0
    )

    # Transition to gaming. Should wait for the running job.
    result = await modes.set_mode(
        GPUMode.GAMING, reason="test", requested_by="test"
    )
    assert result.success
    assert result.to_mode is GPUMode.GAMING

    # Running job completed.
    stored = await store.get(running.id)
    assert stored.state is JobState.COMPLETED

    # New submissions are accepted but must NOT dispatch.
    blocked = await sched.submit(make_job(adapter="ollama"))
    await asyncio.sleep(0.3)
    stored = await store.get(blocked.id)
    assert stored.state is JobState.PENDING

    # Exit gaming; the suspended job should dispatch.
    await modes.set_mode(GPUMode.MIXED, reason="test resume", requested_by="test")

    async def terminal():
        j = await store.get(blocked.id)
        return j.state.is_terminal

    await wait_until(terminal, timeout=3.0)


async def test_mode_suspends_jobs_on_entry(stack):
    modes = stack["modes"]
    sched = stack["scheduler"]

    # Block admission so jobs stay pending.
    sched.set_admission_checker(lambda job: False)
    a = await sched.submit(make_job(adapter="ollama"))
    b = await sched.submit(make_job(adapter="comfyui"))

    await modes.set_mode(GPUMode.GAMING, reason="test", requested_by="test")

    suspended = await modes.get_suspended()
    suspended_ids = {j["id"] for j in suspended}
    assert {a.id, b.id} <= suspended_ids

    # Cancel one suspended job.
    assert await modes.cancel_suspended(a.id) is True
    suspended = await modes.get_suspended()
    assert a.id not in {j["id"] for j in suspended}


# ---------------------------------------------------------------------------
# Safety halt triggered by thermal event
# ---------------------------------------------------------------------------

async def test_thermal_event_triggers_safety_halt(stack):
    monitor = stack["monitor"]
    modes = stack["modes"]
    watchdog = stack["watchdog"]
    fake_nvml = stack["fake_nvml"]

    # Raise the temperature above the ceiling (80 in this stack).
    v100 = fake_nvml.devices[0]
    fake_nvml.temperature[v100.uuid] = 85

    # Force fresh poll and one watchdog iteration.
    await monitor.refresh()
    signals = await watchdog.run_once()

    critical = [s for s in signals if s.severity is Severity.CRITICAL]
    assert any(s.name == "temperature" for s in critical)

    state = await modes.get_state()
    assert state["safety_halted"] is True
    assert "temperature" in (state["safety_halt_reason"] or "").lower()


async def test_safety_halt_blocks_admission(stack):
    modes = stack["modes"]
    sched = stack["scheduler"]
    monitor = stack["monitor"]
    watchdog = stack["watchdog"]
    fake_nvml = stack["fake_nvml"]
    store = stack["store"]
    ollama = stack["ollama"]

    # Sanity: a job dispatches normally.
    async def fast(job):
        return {"ok": True}

    ollama.on_execute = fast
    baseline = await sched.submit(make_job(adapter="ollama"))

    async def baseline_done():
        j = await store.get(baseline.id)
        return j.state.is_terminal
    await wait_until(baseline_done, timeout=2.0)

    # Now trigger a halt.
    fake_nvml.temperature[fake_nvml.devices[0].uuid] = 85
    await monitor.refresh()
    await watchdog.run_once()
    assert (await modes.get_state())["safety_halted"] is True

    # New submissions accepted, but never dispatch.
    blocked = await sched.submit(make_job(adapter="ollama"))
    await asyncio.sleep(0.3)
    stored = await store.get(blocked.id)
    assert stored.state is JobState.PENDING

    # Operator clears the halt; job dispatches.
    await modes.clear_safety_halt(reason="test", cleared_by="test")

    async def blocked_done():
        j = await store.get(blocked.id)
        return j.state.is_terminal
    await wait_until(blocked_done, timeout=3.0)


# ---------------------------------------------------------------------------
# Fail-closed on GPU state loss
# ---------------------------------------------------------------------------

async def test_gpu_unavailable_refuses_admission(stack):
    monitor = stack["monitor"]
    scheduler = stack["scheduler"]
    adapter = stack["ollama"]
    fake_nvml = stack["fake_nvml"]
    store = stack["store"]

    fake_nvml.fail_poll = True
    # Force staleness.
    monitor._max_staleness = 0.01
    await asyncio.sleep(0.1)

    job = await scheduler.submit(make_job(adapter="ollama"))
    await asyncio.sleep(0.3)
    assert len(adapter.executed) == 0
    stored = await store.get(job.id)
    assert stored.state is JobState.PENDING


# ---------------------------------------------------------------------------
# Shutdown drain
# ---------------------------------------------------------------------------

async def test_shutdown_drains_running_job(stack):
    sched = stack["scheduler"]
    adapter = stack["ollama"]
    store = stack["store"]

    async def slow(job):
        await asyncio.sleep(0.3)
        return {"ok": True}

    adapter.on_execute = slow
    running = await sched.submit(make_job(adapter="ollama"))
    await wait_until(
        lambda: sched.current_job is not None, timeout=1.0
    )

    sched.begin_shutdown()
    await asyncio.wait_for(sched.wait_for_idle(), timeout=3.0)

    stored = await store.get(running.id)
    assert stored.state is JobState.COMPLETED
