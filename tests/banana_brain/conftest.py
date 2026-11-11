"""
Shared fixtures and fakes for the Banana Brain test suite.

Provides:
  * fake_nvml:  a stub `pynvml` module that can be installed via
                install_fake_nvml() and configured per-test.
  * FakeAdapter, SlowFakeAdapter, FailingFakeAdapter: in-memory adapters
                that implement the scheduler's adapter contract.
  * config():   a BananaBrainConfig with test-friendly defaults.
  * job_store(): a JobStore backed by a temp SQLite file.
  * scheduler(): a fully-wired Scheduler with fake adapter(s).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import sys
import tempfile
import time
import types
from pathlib import Path
from typing import Any, Optional
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from huey.banana_brain.config import BananaBrainConfig
from huey.banana_brain.job_models import Job, JobState, Priority
from huey.banana_brain.job_store import JobStore
from huey.banana_brain.priority_manager import PriorityManager
from huey.banana_brain.scheduler import Scheduler


# ---------------------------------------------------------------------------
# pytest-asyncio default
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "integration: end-to-end tests using the composition root"
    )


# ---------------------------------------------------------------------------
# Fake NVML
# ---------------------------------------------------------------------------

class FakeNVMLHandle:
    def __init__(self, index: int, uuid: str, name: str, pci: str) -> None:
        self.index = index
        self.uuid = uuid
        self.name = name
        self.pci = pci


class FakeNVMLModule(types.ModuleType):
    """
    Drop-in replacement for `pynvml` / `nvidia-ml-py`.

    Configure via the class attributes before installing; mutate them
    between polls in tests to simulate thermal or lost-device events.
    """

    # Constants that gpu_monitor reads.
    NVML_TEMPERATURE_GPU = 0
    NVML_TEMPERATURE_THRESHOLD_SHUTDOWN = 0
    NVML_TEMPERATURE_THRESHOLD_SLOWDOWN = 1
    nvmlClocksThrottleReasonHwSlowdown = 0x8
    nvmlClocksThrottleReasonSwThermalSlowdown = 0x20
    nvmlClocksThrottleReasonHwPowerBrakeSlowdown = 0x80

    def __init__(self) -> None:
        super().__init__("pynvml")
        self.initialized = False
        self.fail_init = False
        self.devices: list[FakeNVMLHandle] = []
        self.memory: dict[str, tuple[int, int, int]] = {}   # uuid -> (total, free, used)
        self.temperature: dict[str, int] = {}
        self.power_mw: dict[str, int] = {}
        self.util: dict[str, tuple[int, int]] = {}          # uuid -> (gpu, mem)
        self.throttle: dict[str, int] = {}
        self.compute_procs: dict[str, list[Any]] = {}
        self.graphics_procs: dict[str, list[Any]] = {}
        self.fail_poll = False
        self.driver_version = "999.99"
        self.cuda_version = 12000

    # ---- lifecycle ----

    def nvmlInit(self) -> None:
        if self.fail_init:
            raise RuntimeError("fake nvml init failure")
        self.initialized = True

    def nvmlShutdown(self) -> None:
        self.initialized = False

    def nvmlSystemGetDriverVersion(self) -> str:
        return self.driver_version

    def nvmlSystemGetCudaDriverVersion_v2(self) -> int:
        return self.cuda_version

    # ---- enumeration ----

    def nvmlDeviceGetCount_v2(self) -> int:
        return len(self.devices)

    def nvmlDeviceGetHandleByIndex_v2(self, index: int) -> FakeNVMLHandle:
        return self.devices[index]

    def nvmlDeviceGetHandleByUUID(self, uuid: str) -> FakeNVMLHandle:
        for dev in self.devices:
            if dev.uuid == uuid:
                return dev
        raise RuntimeError(f"no such UUID {uuid!r}")

    def nvmlDeviceGetHandleByPciBusId_v2(self, pci: str) -> FakeNVMLHandle:
        for dev in self.devices:
            if dev.pci == pci:
                return dev
        raise RuntimeError(f"no such PCI {pci!r}")

    # ---- identity ----

    def nvmlDeviceGetIndex(self, handle: FakeNVMLHandle) -> int:
        return handle.index

    def nvmlDeviceGetName(self, handle: FakeNVMLHandle) -> str:
        return handle.name

    def nvmlDeviceGetUUID(self, handle: FakeNVMLHandle) -> str:
        return handle.uuid

    def nvmlDeviceGetPciInfo_v3(self, handle: FakeNVMLHandle) -> Any:
        return types.SimpleNamespace(busId=handle.pci)

    def nvmlDeviceGetSerial(self, handle: FakeNVMLHandle) -> str:
        return ""

    # ---- poll ----

    def nvmlDeviceGetMemoryInfo(self, handle: FakeNVMLHandle) -> Any:
        if self.fail_poll:
            raise RuntimeError("fake poll failure")
        total, free, used = self.memory.get(handle.uuid, (32 << 30, 30 << 30, 2 << 30))
        return types.SimpleNamespace(total=total, free=free, used=used, reserved=0)

    def nvmlDeviceGetUtilizationRates(self, handle: FakeNVMLHandle) -> Any:
        gpu, mem = self.util.get(handle.uuid, (0, 0))
        return types.SimpleNamespace(gpu=gpu, memory=mem)

    def nvmlDeviceGetTemperature(self, handle: FakeNVMLHandle, kind: int) -> int:
        return self.temperature.get(handle.uuid, 45)

    def nvmlDeviceGetPowerUsage(self, handle: FakeNVMLHandle) -> int:
        return self.power_mw.get(handle.uuid, 70_000)

    def nvmlDeviceGetTemperatureThreshold(self, handle: FakeNVMLHandle, kind: int) -> int:
        if kind == self.NVML_TEMPERATURE_THRESHOLD_SHUTDOWN:
            return 95
        return 88

    def nvmlDeviceGetEnforcedPowerLimit(self, handle: FakeNVMLHandle) -> int:
        return 250_000

    def nvmlDeviceGetCurrentClocksThrottleReasons(self, handle: FakeNVMLHandle) -> int:
        return self.throttle.get(handle.uuid, 0)

    def nvmlDeviceGetComputeRunningProcesses(self, handle: FakeNVMLHandle) -> list[Any]:
        return list(self.compute_procs.get(handle.uuid, []))

    def nvmlDeviceGetGraphicsRunningProcesses(self, handle: FakeNVMLHandle) -> list[Any]:
        return list(self.graphics_procs.get(handle.uuid, []))


@pytest.fixture
def fake_nvml(monkeypatch: pytest.MonkeyPatch) -> FakeNVMLModule:
    """
    Install a fresh FakeNVMLModule as `pynvml` for the duration of a test.

    A single V100 is configured by default; tests that need multi-GPU
    scenarios add entries to `fake.devices` before starting the monitor.
    """
    module = FakeNVMLModule()
    v100 = FakeNVMLHandle(
        index=0,
        uuid="GPU-11111111-1111-1111-1111-111111111111",
        name="Tesla V100-SXM2-32GB",
        pci="0000:01:00.0",
    )
    module.devices = [v100]
    module.memory[v100.uuid] = (32 << 30, 30 << 30, 2 << 30)
    module.util[v100.uuid] = (5, 10)
    module.temperature[v100.uuid] = 45
    module.power_mw[v100.uuid] = 70_000

    monkeypatch.setitem(sys.modules, "pynvml", module)
    yield module
    monkeypatch.delitem(sys.modules, "pynvml", raising=False)


# ---------------------------------------------------------------------------
# Stub adapters
# ---------------------------------------------------------------------------

class FakeAdapter:
    """
    In-memory adapter satisfying the scheduler's contract.

    Each instance tracks the jobs it executed, the model unloads it was
    asked to perform, and exposes hooks for tests to intercept behaviour:

      on_execute:    async callback(job) -> result dict
      on_unload:     async callback(needed_bytes) -> freed bytes

    The default behaviour is "succeed immediately" with a result dict
    containing the job id.
    """

    def __init__(self, name: str, *, estimate_bytes: int = 1 << 30) -> None:
        self.name = name
        self.estimate_bytes = estimate_bytes
        self.executed: list[Job] = []
        self.unload_calls: list[int] = []
        self.cancel_calls: list[Job] = []
        self.on_execute: Optional[Any] = None
        self.on_unload: Optional[Any] = None
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def execute(self, job: Job) -> dict[str, Any]:
        self.executed.append(job)
        if self.on_execute is not None:
            return await self.on_execute(job)
        return {"ok": True, "job_id": job.id, "adapter": self.name}

    async def estimate_vram(self, job: Job) -> int:
        return self.estimate_bytes

    async def unload_idle_models(self, needed_bytes: int) -> int:
        self.unload_calls.append(needed_bytes)
        if self.on_unload is not None:
            return await self.on_unload(needed_bytes)
        return 0

    async def request_cancel(self, job: Job) -> bool:
        self.cancel_calls.append(job)
        return True


@pytest.fixture
def fake_adapter() -> FakeAdapter:
    return FakeAdapter("fake")


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BananaBrainTestConfig(BananaBrainConfig):
    """Base config plus component options accepted by the scheduler stack."""

    job_retention_days: float = 0.0
    job_max_terminal_rows: int = 0
    job_prune_interval_seconds: float = 0.0
    metrics_enabled: bool = False
    notifications_enabled: bool = False
    mode_persistence_enabled: bool = False
    watchdog_check_interval_seconds: float = 0.1
    watchdog_temperature_warn_c: float = 70.0
    watchdog_gpu_unavailable_warn_s: float = 0.1
    watchdog_gpu_unavailable_critical_s: float = 0.3
    watchdog_lease_expiry_seconds: float = 10.0


@pytest.fixture
def test_config(tmp_path: Path) -> BananaBrainTestConfig:
    """
    BananaBrainConfig tuned for tests: fast polling, small headroom,
    Unix API socket in tmp_path, terminal-row pruning disabled.
    """
    return BananaBrainTestConfig(
        shutdown_grace_seconds=5.0,
        poll_interval_seconds=0.05,
        max_staleness_seconds=1.0,
        vram_headroom_gib=1.0,
        priority_aging_interval_seconds=0.2,
        priority_aging_step=1,
        priority_aging_cap=99,
        priority_overdue_boost=20,
        database_path=tmp_path / "test.db",
        job_retention_days=0,        # disable pruning
        job_max_terminal_rows=0,     # disable pruning
        job_prune_interval_seconds=0,
        api_socket_path=tmp_path / "test.sock",
        metrics_enabled=False,
        notifications_enabled=False,
        mode_persistence_enabled=False,
        watchdog_check_interval_seconds=0.1,
    )


# ---------------------------------------------------------------------------
# Job store
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def job_store(test_config: BananaBrainConfig):
    store = JobStore(test_config)
    await store.start()
    try:
        yield store
    finally:
        await store.stop()


# ---------------------------------------------------------------------------
# Priority manager
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def priority_manager(test_config: BananaBrainConfig):
    pm = PriorityManager(test_config)
    await pm.start()
    try:
        yield pm
    finally:
        await pm.stop()


# ---------------------------------------------------------------------------
# Scheduler + fake adapter
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def scheduler(test_config, job_store, fake_nvml):
    """
    A fully-wired Scheduler with one FakeAdapter and a real JobStore.

    GPU monitor and VRAM manager are real, backed by the fake NVML module,
    so tests exercise the actual admission path (not a mock).
    """
    from huey.banana_brain.gpu_monitor import GPUMonitor
    from huey.banana_brain.vram_manager import VRAMManager

    monitor = GPUMonitor(test_config)
    await monitor.start()

    adapter = FakeAdapter("fake")
    vram = VRAMManager(test_config, monitor)

    scheduler = Scheduler(
        config=test_config,
        job_store=job_store,
        gpu_monitor=monitor,
        vram_manager=vram,
        priority_manager=PriorityManager(test_config),
        adapters={"fake": adapter},
    )
    await scheduler.start()
    try:
        yield scheduler, adapter, monitor
    finally:
        await scheduler.stop()
        await monitor.stop()


# ---------------------------------------------------------------------------
# Convenience builders
# ---------------------------------------------------------------------------

def make_job(
    *,
    adapter: str = "fake",
    priority: int = int(Priority.BACKGROUND),
    payload: Optional[dict[str, Any]] = None,
    **kwargs: Any,
) -> Job:
    return Job(
        adapter=adapter,
        payload=payload or {},
        priority=priority,
        **kwargs,
    )


async def wait_until(
    predicate,
    *,
    timeout: float = 5.0,
    interval: float = 0.02,
) -> None:
    """
    Poll `predicate()` until it returns truthy, or raise after `timeout`.

    Used to avoid flaky `await asyncio.sleep(...)` between scheduler ticks.
    """
    deadline = time.monotonic() + timeout
    while True:
        result = predicate()
        if asyncio.iscoroutine(result):
            result = await result
        if result:
            return
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"wait_until: condition not met within {timeout:.1f}s"
            )
        await asyncio.sleep(interval)


pytest_asyncio.fixture
async def wait_until_fixture():
    return wait_until
