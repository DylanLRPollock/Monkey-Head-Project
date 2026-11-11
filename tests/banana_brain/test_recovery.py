"""Recovery tests: restart the scheduler against the same job_store."""

from __future__ import annotations

import asyncio

import pytest

from huey.banana_brain.job_models import Job, JobState, Priority
from huey.banana_brain.job_store import JobStore
from huey.banana_brain.priority_manager import PriorityManager
from huey.banana_brain.scheduler import Scheduler
from huey.banana_brain.gpu_monitor import GPUMonitor
from huey.banana_brain.vram_manager import VRAMManager

from .conftest import FakeAdapter, make_job, wait_until


async def _build_scheduler(test_config, job_store, adapter, monitor):
    vram = VRAMManager(test_config, monitor)
    pm = PriorityManager(test_config)
    sched = Scheduler(
        config=test_config,
        job_store=job_store,
        gpu_monitor=monitor,
        vram_manager=vram,
        priority_manager=pm,
        adapters={adapter.name: adapter},
    )
    return sched


# ---------------------------------------------------------------------------
# PENDING survives restart
# ---------------------------------------------------------------------------

async def test_pending_jobs_requeued_on_restart(test_config, fake_nvml):
    store = JobStore(test_config)
    await store.start()
    monitor = GPUMonitor(test_config)
    await monitor.start()
    adapter = FakeAdapter("fake")

    try:
        sched = await _build_scheduler(test_config, store, adapter, monitor)
        await sched.start()
        # Submit a job, but block dispatch so it stays PENDING.
        sched.set_admission_checker(lambda job: False)
        submitted = await sched.submit(make_job())
        await sched.stop()

        stored = await store.get(submitted.id)
        assert stored.state is JobState.PENDING

        # Simulate a fresh scheduler against the same store.
        adapter2 = FakeAdapter("fake")
        sched2 = await _build_scheduler(test_config, store, adapter2, monitor)
        await sched2.start()
        try:
            async def terminal():
                j = await store.get(submitted.id)
                return j.state.is_terminal

            await wait_until(terminal, timeout=3.0)
            assert len(adapter2.executed) == 1
        finally:
            await sched2.stop()
    finally:
        await monitor.stop()
        await store.stop()


# ---------------------------------------------------------------------------
# RUNNING becomes PENDING on restart
# ---------------------------------------------------------------------------

async def test_running_jobs_requeued_as_pending(test_config, fake_nvml):
    store = JobStore(test_config)
    await store.start()
    monitor = GPUMonitor(test_config)
    await monitor.start()
    adapter = FakeAdapter("fake")

    try:
        sched = await _build_scheduler(test_config, store, adapter, monitor)
        await sched.start()

        # Simulate the crash scenario: write a RUNNING job directly.
        crashed = make_job()
        crashed.state = JobState.RUNNING
        crashed.submitted_at = 1_000_000.0
        crashed.started_at = 1_000_000.5
        crashed.attempts = 1
        await store.save(crashed)

        # Fresh scheduler must re-queue it.
        adapter2 = FakeAdapter("fake")
        sched2 = await _build_scheduler(test_config, store, adapter2, monitor)
        await sched2.start()
        try:
            async def terminal():
                j = await store.get(crashed.id)
                return j is not None and j.state.is_terminal

            await wait_until(terminal, timeout=3.0)
            stored = await store.get(crashed.id)
            assert stored.state is JobState.COMPLETED
            # Attempts counter preserved and incremented.
            assert stored.attempts == 2
            assert len(adapter2.executed) == 1
        finally:
            await sched2.stop()
    finally:
        await monitor.stop()
        await store.stop()


# ---------------------------------------------------------------------------
# Terminal jobs are not duplicated
# ---------------------------------------------------------------------------

async def test_completed_jobs_not_requeued(test_config, fake_nvml):
    store = JobStore(test_config)
    await store.start()
    monitor = GPUMonitor(test_config)
    await monitor.start()
    adapter = FakeAdapter("fake")

    try:
        sched = await _build_scheduler(test_config, store, adapter, monitor)
        await sched.start()
        submitted = await sched.submit(make_job())
        await wait_until(
            lambda: len(adapter.executed) == 1, timeout=2.0
        )
        # Wait for terminal state and persistence.
        await asyncio.sleep(0.1)
        await sched.stop()

        adapter2 = FakeAdapter("fake")
        sched2 = await _build_scheduler(test_config, store, adapter2, monitor)
        await sched2.start()
        try:
            # Give the dispatcher a chance to (incorrectly) re-run it.
            await asyncio.sleep(0.3)
            assert len(adapter2.executed) == 0
        finally:
            await sched2.stop()
    finally:
        await monitor.stop()
        await store.stop()


# ---------------------------------------------------------------------------
# Missing adapter is handled
# ---------------------------------------------------------------------------

async def test_job_with_removed_adapter_marked_failed(
    test_config, fake_nvml
):
    store = JobStore(test_config)
    await store.start()
    monitor = GPUMonitor(test_config)
    await monitor.start()

    try:
        orphan = make_job(adapter="removed_adapter")
        orphan.state = JobState.PENDING
        orphan.submitted_at = 1000.0
        await store.save(orphan)

        adapter = FakeAdapter("fake")
        sched = await _build_scheduler(test_config, store, adapter, monitor)
        await sched.start()
        try:
            stored = await store.get(orphan.id)
            assert stored.state is JobState.FAILED
            assert "adapter removed" in stored.last_error
        finally:
            await sched.stop()
    finally:
        await monitor.stop()
        await store.stop()


# ---------------------------------------------------------------------------
# Idempotency key prevents duplicates on re-submit
# ---------------------------------------------------------------------------

async def test_idempotency_key_lookup(test_config, fake_nvml):
    store = JobStore(test_config)
    await store.start()
    try:
        job = make_job()
        job.idempotency_key = "abc-123"
        await store.save(job)
        found = await store.find_by_idempotency_key("abc-123", job.adapter)
        assert found is not None
        assert found.id == job.id

        missing = await store.find_by_idempotency_key("nonexistent", job.adapter)
        assert missing is None
    finally:
        await store.stop()
