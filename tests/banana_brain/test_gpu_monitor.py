"""Tests for huey.banana_brain.gpu_monitor."""

from __future__ import annotations

import asyncio
import time

import pytest

from huey.banana_brain.config import BananaBrainConfig
from huey.banana_brain.gpu_monitor import (
    DeviceIdentity,
    GPUHealth,
    GPUMonitor,
    GPUProcess,
    GPUStatus,
    NVMLUnavailable,
)


# ---------------------------------------------------------------------------
# Device selection
# ---------------------------------------------------------------------------

async def test_select_single_device_when_only_one_visible(
    test_config, fake_nvml
):
    monitor = GPUMonitor(test_config)
    await monitor.start()
    try:
        ident = await monitor.get_device_identity()
        assert ident is not None
        assert ident.uuid == fake_nvml.devices[0].uuid
        assert ident.name.startswith("Tesla V100")
    finally:
        await monitor.stop()


async def test_select_by_uuid(test_config, fake_nvml, tmp_path):
    cfg = BananaBrainConfig(
        device_uuid=fake_nvml.devices[0].uuid,
        poll_interval_seconds=0.05,
        max_staleness_seconds=1.0,
        database_path=tmp_path / "x.db",
    )
    monitor = GPUMonitor(cfg)
    await monitor.start()
    try:
        status = await monitor.get_status()
        assert status is not None
        assert status.identity.uuid == fake_nvml.devices[0].uuid
    finally:
        await monitor.stop()


async def test_select_by_pci_bus_id(test_config, fake_nvml, tmp_path):
    cfg = BananaBrainConfig(
        pci_bus_id=fake_nvml.devices[0].pci,
        poll_interval_seconds=0.05,
        max_staleness_seconds=1.0,
        database_path=tmp_path / "x.db",
    )
    monitor = GPUMonitor(cfg)
    await monitor.start()
    try:
        status = await monitor.get_status()
        assert status.identity.pci_bus_id == fake_nvml.devices[0].pci
    finally:
        await monitor.stop()


async def test_refuses_multi_gpu_without_identity(
    test_config, fake_nvml, tmp_path
):
    # Add a second device; no UUID/PCI configured.
    from .conftest import FakeNVMLHandle

    second = FakeNVMLHandle(
        index=1,
        uuid="GPU-22222222-2222-2222-2222-222222222222",
        name="GeForce RTX 4090",
        pci="0000:02:00.0",
    )
    fake_nvml.devices.append(second)
    fake_nvml.memory[second.uuid] = (24 << 30, 22 << 30, 2 << 30)

    cfg = BananaBrainConfig(
        poll_interval_seconds=0.05,
        max_staleness_seconds=1.0,
        database_path=tmp_path / "x.db",
    )
    monitor = GPUMonitor(cfg)
    with pytest.raises(NVMLUnavailable, match="multiple GPUs"):
        await monitor.start()


async def test_init_retries_and_fails_cleanly(test_config, fake_nvml):
    fake_nvml.fail_init = True
    # Shorten the init retry delays for a fast test.
    GPUMonitor.INIT_RETRY_DELAYS = (0.01, 0.01)
    monitor = GPUMonitor(test_config)
    with pytest.raises(NVMLUnavailable):
        await monitor.start()
    GPUMonitor.INIT_RETRY_DELAYS = (0.5, 1.0, 2.0, 5.0)


# ---------------------------------------------------------------------------
# Staleness
# ---------------------------------------------------------------------------

async def test_status_is_none_when_stale(test_config, fake_nvml):
    cfg = BananaBrainConfig(
        poll_interval_seconds=10.0,     # very long; we won't get a fresh poll
        max_staleness_seconds=0.05,
        database_path=test_config.database_path,
    )
    monitor = GPUMonitor(cfg)
    await monitor.start()
    try:
        status = await monitor.get_status()
        assert status is not None
        # Sleep past max_staleness without another poll.
        await asyncio.sleep(0.1)
        stale = await monitor.get_status()
        assert stale is None
    finally:
        await monitor.stop()


async def test_refresh_updates_staleness(test_config, fake_nvml):
    cfg = BananaBrainConfig(
        poll_interval_seconds=10.0,
        max_staleness_seconds=0.05,
        database_path=test_config.database_path,
    )
    monitor = GPUMonitor(cfg)
    await monitor.start()
    try:
        await asyncio.sleep(0.1)
        assert await monitor.get_status() is None
        refreshed = await monitor.refresh()
        assert refreshed is not None
        assert await monitor.get_status() is not None
    finally:
        await monitor.stop()


# ---------------------------------------------------------------------------
# Health and processes
# ---------------------------------------------------------------------------

async def test_health_fields_populated(test_config, fake_nvml):
    fake_nvml.temperature[fake_nvml.devices[0].uuid] = 90
    fake_nvml.throttle[fake_nvml.devices[0].uuid] = (
        fake_nvml.nvmlClocksThrottleReasonHwSlowdown
    )
    monitor = GPUMonitor(test_config)
    await monitor.start()
    try:
        status = await monitor.get_status()
        assert status.temperature_c == 90
        assert status.health.thermal_slowdown is True
        assert status.health.slowdown_threshold_c == 88
        assert status.health.shutdown_threshold_c == 95
    finally:
        await monitor.stop()


async def test_processes_reported(test_config, fake_nvml):
    import types

    fake_nvml.compute_procs[fake_nvml.devices[0].uuid] = [
        types.SimpleNamespace(pid=1234, usedGpuMemory=2 << 30),
        types.SimpleNamespace(pid=5678, usedGpuMemory=1 << 30),
    ]
    monitor = GPUMonitor(test_config)
    await monitor.start()
    try:
        status = await monitor.get_status()
        pids = {p.pid for p in status.processes}
        assert pids == {1234, 5678}
        # Unmanaged-process helper.
        unmanaged = status.unmanaged_processes({1234})
        assert [p.pid for p in unmanaged] == [5678]
    finally:
        await monitor.stop()


async def test_status_never_raises(test_config, fake_nvml):
    monitor = GPUMonitor(test_config)
    await monitor.start()
    try:
        fake_nvml.fail_poll = True
        # Even under a failing driver, get_status() returns None, not raise.
        await asyncio.sleep(0.2)
        assert await monitor.get_status() is None
    finally:
        await monitor.stop()
