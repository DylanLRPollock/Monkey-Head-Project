"""Tests for huey.banana_brain.gpu_monitor."""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace

import pytest

from huey.banana_brain.config import BananaBrainConfig
from huey.banana_brain.gpu_monitor import (
    DeviceIdentity,
    GPUMonitor,
    GPUStatus,
    NVMLUnavailable,
)

# ---------------------------------------------------------------------------
# Device selection
# ---------------------------------------------------------------------------


async def test_select_single_device_when_only_one_visible(test_config, fake_nvml):
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


async def test_refuses_multi_gpu_without_identity(test_config, fake_nvml, tmp_path):
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
        poll_interval_seconds=10.0,  # very long; we won't get a fresh poll
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
    test_config = replace(test_config, max_staleness_seconds=0.05)
    monitor = GPUMonitor(test_config)
    await monitor.start()
    try:
        fake_nvml.fail_poll = True
        # Even under a failing driver, get_status() returns None, not raise.
        await asyncio.sleep(0.2)
        assert await monitor.get_status() is None
    finally:
        await monitor.stop()


def test_device_identity_and_status_helpers():
    identity = DeviceIdentity(
        index=0, name="GPU", uuid="GPU-ABC", pci_bus_id="0000:01:00.0"
    )
    assert identity.matches(uuid="gpu-abc", pci_bus_id=None)
    assert identity.matches(uuid=None, pci_bus_id="0000:01:00.0")
    assert not identity.matches(uuid=None, pci_bus_id="0000:02:00.0")
    status = GPUStatus(
        identity=identity,
        timestamp=time.time(),
        total_vram_bytes=100,
        free_vram_bytes=25,
        used_vram_bytes=75,
        reserved_vram_bytes=0,
        gpu_utilization_percent=0,
        memory_utilization_percent=0,
        temperature_c=None,
        power_watts=None,
    )
    assert status.vram_free_fraction == 0.25
    assert status.managed_pids(set()) == frozenset()
    zero_total = replace(status, total_vram_bytes=0)
    assert zero_total.vram_free_fraction == 0.0


async def test_monitor_rejects_second_start_and_stop_is_idempotent(
    test_config, fake_nvml
):
    monitor = GPUMonitor(test_config)
    await monitor.stop()
    await monitor.start()
    try:
        with pytest.raises(RuntimeError, match="already started"):
            await monitor.start()
    finally:
        await monitor.stop()
    await monitor.stop()


async def test_start_refuses_when_first_poll_has_no_snapshot(test_config, fake_nvml):
    monitor = GPUMonitor(test_config)
    monitor._poll_once = lambda: None
    with pytest.raises(NVMLUnavailable, match="first device poll failed"):
        await monitor.start()
    assert monitor._poll_task is None
    await monitor.stop()


async def test_refresh_logs_poll_exception_and_returns_none(test_config):
    monitor = GPUMonitor(test_config)

    def fail_poll():
        raise RuntimeError("driver error")

    monitor._poll_once = fail_poll
    assert await monitor.refresh() is None


async def test_process_enumeration_handles_missing_and_failing_nvml_apis(
    test_config, fake_nvml
):
    monitor = GPUMonitor(test_config)
    await monitor.start()
    try:
        handle = monitor._handle
        fake_nvml.nvmlDeviceGetComputeRunningProcesses = None
        fake_nvml.nvmlDeviceGetGraphicsRunningProcesses = None
        assert monitor._read_processes(handle) == ()

        fake_nvml.nvmlDeviceGetComputeRunningProcesses = lambda _handle: (
            _ for _ in ()
        ).throw(RuntimeError("NVML process query failed"))
        fake_nvml.nvmlDeviceGetGraphicsRunningProcesses = lambda _handle: [
            type("Process", (), {"pid": 44, "usedGpuMemory": 0})()
        ]
        process = monitor._read_processes(handle)[0]
        assert process.pid == 44
        assert process.used_memory_bytes == 0
        assert process.kind == "graphics"
    finally:
        await monitor.stop()


async def test_poll_loop_recovers_after_a_failed_poll(test_config):
    monitor = GPUMonitor(test_config)
    identity = DeviceIdentity(index=0, name="GPU", uuid="GPU-test", pci_bus_id="")
    status = GPUStatus(
        identity=identity,
        timestamp=time.time(),
        total_vram_bytes=100,
        free_vram_bytes=50,
        used_vram_bytes=50,
        reserved_vram_bytes=0,
        gpu_utilization_percent=0,
        memory_utilization_percent=0,
        temperature_c=40,
        power_watts=10,
    )
    attempts = 0

    def poll_once():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient poll failure")
        monitor._stopping = True
        return status

    monitor._poll_once = poll_once
    await monitor._poll_loop()
    assert attempts == 2
    assert await monitor.get_status() == status


async def test_configured_missing_device_fails(
    test_config, fake_nvml, tmp_path, monkeypatch
):
    monkeypatch.setattr(GPUMonitor, "INIT_RETRY_DELAYS", (0.001,))
    cfg = BananaBrainConfig(
        device_uuid="GPU-does-not-exist",
        poll_interval_seconds=0.05,
        max_staleness_seconds=1,
        database_path=tmp_path / "missing-device.db",
    )
    with pytest.raises(NVMLUnavailable, match="not found"):
        await GPUMonitor(cfg).start()


async def test_device_health_reports_power_brake(test_config, fake_nvml):
    fake_nvml.throttle[fake_nvml.devices[0].uuid] = (
        fake_nvml.nvmlClocksThrottleReasonHwPowerBrakeSlowdown
    )
    monitor = GPUMonitor(test_config)
    await monitor.start()
    try:
        status = await monitor.get_status()
        assert status.health.power_brake is True
        assert status.health.thermal_slowdown is False
    finally:
        await monitor.stop()


async def test_processes_are_deduplicated_and_unknown_memory_is_preserved(
    test_config, fake_nvml
):
    import types

    gpu_uuid = fake_nvml.devices[0].uuid
    fake_nvml.compute_procs[gpu_uuid] = [
        types.SimpleNamespace(pid=11, usedGpuMemory=None),
        types.SimpleNamespace(pid=12, usedGpuMemory=-1),
    ]
    fake_nvml.graphics_procs[gpu_uuid] = [
        types.SimpleNamespace(pid=11, usedGpuMemory=1024),
    ]
    monitor = GPUMonitor(test_config)
    await monitor.start()
    try:
        status = await monitor.get_status()
        by_pid = {process.pid: process for process in status.processes}
        assert len(by_pid) == 2
        assert by_pid[11].used_memory_bytes == 1024
        assert by_pid[12].used_memory_bytes is None
    finally:
        await monitor.stop()


async def test_select_by_uuid_missing_and_pci_missing(
    test_config, fake_nvml, tmp_path, monkeypatch
):
    monkeypatch.setattr(GPUMonitor, "INIT_RETRY_DELAYS", (0.001,))
    for field, value in (
        ("device_uuid", "missing"),
        ("pci_bus_id", "0000:ff:00.0"),
    ):
        cfg = BananaBrainConfig(
            **{field: value},
            poll_interval_seconds=0.05,
            max_staleness_seconds=1,
            database_path=tmp_path / f"{field}.db",
        )
        with pytest.raises(NVMLUnavailable, match="not found"):
            await GPUMonitor(cfg).start()


def test_safe_and_optional_string_helpers():
    assert GPUMonitor._safe(lambda: 1, 0) == 1
    assert GPUMonitor._safe(lambda: 1 / 0, "fallback") == "fallback"
    assert GPUMonitor._optional_str(lambda: b"hello") == "hello"
    assert GPUMonitor._optional_str(lambda: "") is None
    assert GPUMonitor._optional_str(lambda: (_ for _ in ()).throw(OSError())) is None


@pytest.mark.asyncio
async def test_unavailable_poll_refresh_shutdown_and_config_edges(
    test_config, monkeypatch
):
    from types import SimpleNamespace

    from huey.banana_brain.gpu_monitor import _cfg_get

    monitor = GPUMonitor(test_config)
    assert await monitor.get_status() is None
    assert await monitor.get_device_identity() is None
    monitor.request_refresh()
    assert monitor._wake.is_set()
    assert monitor._poll_once() is None
    assert _cfg_get({"fallback": 2}, "primary", "fallback") == 2
    assert _cfg_get(SimpleNamespace(value=3), "value") == 3

    class BrokenNVML:
        def nvmlShutdown(self):
            raise RuntimeError("shutdown failed")

    monitor._nvml = BrokenNVML()
    monitor._handle = object()
    monitor._shutdown_nvml()
    assert monitor._handle is None

    async def cancelled_to_thread(*_args, **_kwargs):
        raise asyncio.CancelledError

    monkeypatch.setattr("huey.banana_brain.gpu_monitor.asyncio.to_thread", cancelled_to_thread)
    with pytest.raises(asyncio.CancelledError):
        await monitor._poll_loop()


def test_multi_gpu_listing_handles_unqueryable_device_and_decodes_pci(test_config):
    from types import SimpleNamespace

    monitor = GPUMonitor(test_config)

    class MultipleNVML:
        def nvmlDeviceGetCount_v2(self):
            return 2

        def nvmlDeviceGetHandleByIndex_v2(self, index):
            if index == 0:
                raise RuntimeError("device disappeared")
            return object()

        def nvmlDeviceGetName(self, _handle):
            return "Tesla V100"

        def nvmlDeviceGetUUID(self, _handle):
            return "GPU-123"

        def nvmlDeviceGetPciInfo_v3(self, _handle):
            return SimpleNamespace(busId=b"0000:01:00.0")

        def nvmlDeviceGetIndex(self, _handle):
            return 1

        def nvmlDeviceGetSerial(self, _handle):
            return "serial"

    monitor._nvml = MultipleNVML()
    with pytest.raises(NVMLUnavailable, match="unqueryable"):
        monitor._select_device()

    identity = monitor._read_identity(object())
    assert identity.pci_bus_id == "0000:01:00.0"
