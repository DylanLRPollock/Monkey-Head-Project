"""Tests for huey.banana_brain.vram_manager."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from huey.banana_brain.config import BananaBrainConfig
from huey.banana_brain.job_models import Job
from huey.banana_brain.vram_manager import (
    ReservationState,
    VRAMManager,
)

from .conftest import make_job


GIB = 1024 ** 3


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def stub_monitor():
    """A monitor stub whose get_status can be controlled per test."""

    class _Stub:
        def __init__(self):
            self.status = None
            self.refresh_result = None

        async def get_status(self):
            return self.status

        async def refresh(self):
            self.status = self.refresh_result
            return self.status

    return _Stub()


@pytest.fixture
def vram(test_config, stub_monitor):
    return VRAMManager(test_config, stub_monitor)


def _status(total_gib=32, free_gib=30):
    from types import SimpleNamespace
    return SimpleNamespace(
        total_vram_bytes=total_gib * GIB,
        free_vram_bytes=free_gib * GIB,
        used_vram_bytes=(total_gib - free_gib) * GIB,
    )


# ---------------------------------------------------------------------------
# Admission
# ---------------------------------------------------------------------------

async def test_reserve_success(vram, stub_monitor, test_config):
    stub_monitor.status = _status(total_gib=32, free_gib=30)
    job = make_job()
    ok = await vram.try_reserve(job, 5 * GIB)
    assert ok is True
    assert vram.reservation_count() == 1
    assert vram.committed_bytes() == 5 * GIB


async def test_reserve_fails_when_gpu_state_unknown(vram, stub_monitor):
    stub_monitor.status = None
    ok = await vram.try_reserve(make_job(), 1 * GIB)
    assert ok is False
    snap = await vram.snapshot()
    assert snap["last_refusal"]["reason"] == "gpu_state_unknown"


async def test_reserve_fails_insufficient_vram(vram, stub_monitor):
    # Headroom = 1 GiB (from test_config), free = 4 GiB -> allocatable = 3.
    stub_monitor.status = _status(total_gib=32, free_gib=4)
    ok = await vram.try_reserve(make_job(), 5 * GIB)
    assert ok is False
    snap = await vram.snapshot()
    assert snap["last_refusal"]["reason"] == "insufficient_vram"


async def test_headroom_enforced(vram, stub_monitor):
    stub_monitor.status = _status(total_gib=32, free_gib=2)
    # free=2 GiB, headroom=1 GiB -> only 1 GiB allocatable.
    assert await vram.try_reserve(make_job(), 1 * GIB) is True
    assert await vram.try_reserve(make_job(), 1 * GIB) is False


async def test_implausible_nvml_data_refused(vram, stub_monitor):
    stub_monitor.status = _status(total_gib=32, free_gib=100)  # free > total
    ok = await vram.try_reserve(make_job(), 1 * GIB)
    assert ok is False
    snap = await vram.snapshot()
    assert snap["last_refusal"]["reason"] == "implausible_nvml_data"


async def test_zero_and_negative_estimates_refused(vram, stub_monitor):
    stub_monitor.status = _status()
    assert await vram.try_reserve(make_job(), 0) is False
    assert await vram.try_reserve(make_job(), -1) is False


async def test_estimate_exceeds_total(vram, stub_monitor):
    stub_monitor.status = _status(total_gib=32, free_gib=32)
    ok = await vram.try_reserve(make_job(), 40 * GIB)
    assert ok is False
    snap = await vram.snapshot()
    assert snap["last_refusal"]["reason"] == "estimate_exceeds_total"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

async def test_reserve_is_idempotent_for_same_job(vram, stub_monitor):
    stub_monitor.status = _status()
    job = make_job()
    assert await vram.try_reserve(job, 5 * GIB) is True
    # Second call with the same size is a no-op.
    assert await vram.try_reserve(job, 5 * GIB) is True
    assert vram.reservation_count() == 1
    assert vram.committed_bytes() == 5 * GIB


async def test_reserve_excludes_self_from_committed(vram, stub_monitor):
    """
    Regression: the scheduler calls try_reserve twice for the same job
    (initial + retry-after-freeing). The second call must not see the
    first call's reservation as competing.
    """
    stub_monitor.status = _status(free_gib=10)
    job = make_job()
    assert await vram.try_reserve(job, 6 * GIB) is True
    # Second call: if self counted, free(10) - self(6) - headroom(1) = 3,
    # which would refuse 6. Excluded: free(10) - 0 - 1 = 9 -> accepted.
    assert await vram.try_reserve(job, 6 * GIB, refresh=False) is True


# ---------------------------------------------------------------------------
# Release and mark_running
# ---------------------------------------------------------------------------

async def test_release_frees_commitment(vram, stub_monitor):
    stub_monitor.status = _status(free_gib=3)
    job = make_job()
    assert await vram.try_reserve(job, 2 * GIB) is True
    vram.release(job)
    assert vram.reservation_count() == 0
    assert vram.committed_bytes() == 0


async def test_release_is_idempotent(vram, stub_monitor):
    stub_monitor.status = _status()
    job = make_job()
    await vram.try_reserve(job, 1 * GIB)
    vram.release(job)
    vram.release(job)     # must not raise
    assert vram.reservation_count() == 0


async def test_mark_running_removes_from_committed(vram, stub_monitor):
    """
    After mark_running, the reservation is ACTIVE: the bytes are already
    visible in NVML's free_vram_bytes, so counting them again would
    double-book them against new admissions.
    """
    stub_monitor.status = _status()
    job = make_job()
    await vram.try_reserve(job, 5 * GIB)
    assert vram.committed_bytes() == 5 * GIB

    vram.mark_running(job)
    assert vram.reservation_count() == 1
    assert vram.committed_bytes() == 0    # not double-counted


async def test_mark_running_unknown_job_is_noop(vram):
    vram.mark_running(make_job())  # no reservation exists; must not raise


# ---------------------------------------------------------------------------
# available_bytes
# ---------------------------------------------------------------------------

async def test_available_bytes_returns_none_when_unknown(vram, stub_monitor):
    stub_monitor.status = None
    assert await vram.available_bytes() is None


async def test_available_bytes_after_reservation(vram, stub_monitor):
    stub_monitor.status = _status(total_gib=32, free_gib=10)
    assert await vram.available_bytes() == 9 * GIB    # 10 - 1 headroom

    job = make_job()
    await vram.try_reserve(job, 4 * GIB)
    assert await vram.available_bytes() == 5 * GIB    # 10 - 4 - 1
