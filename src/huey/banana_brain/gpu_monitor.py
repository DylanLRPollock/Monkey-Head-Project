"""
banana_brain.gpu_monitor — NVML-based monitor for the primary GPU.

Responsibilities (from the Banana Brain design doc):
  * Detect the V100 by UUID or PCI bus identity, not by index.
  * Report real free/used/reserved VRAM, utilisation, temperature and power.
  * Enumerate GPU processes so the scheduler can recognise unmanaged work.
  * Keep running when NVML temporarily fails, while refusing to report
    memory state that might be stale. Fail closed: get_status() -> None.

Public API (all async except where noted; safe to call from any task):
  async start()                 -> None
  async stop()                  -> None
  async get_status()            -> GPUStatus | None
  async refresh()               -> GPUStatus | None   force one poll
  def   request_refresh()       -> None               wake the poll loop
  async get_device_identity()   -> DeviceIdentity | None

Lifecycle (called by banana-brain_scheduler.py):
  async start()
  async stop()

Contracts expected by callers:
  * GPUStatus.total_vram_bytes / free_vram_bytes / used_vram_bytes /
    reserved_vram_bytes are integers in bytes.
  * get_status() returns None if NVML is unavailable, the device is lost,
    or the snapshot is stale. Never raises.

Dependency:
  pip install nvidia-ml-py
  (imports as `pynvml`; the PyPI `pynvml` package is deprecated)
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "DeviceIdentity",
    "GPUHealth",
    "GPUMonitor",
    "GPUProcess",
    "GPUStatus",
    "NVMLUnavailable",
]

LOG = logging.getLogger("banana_brain.gpu_monitor")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeviceIdentity:
    """Stable identity for a GPU, independent of enumeration order."""

    index: int
    name: str
    uuid: str
    pci_bus_id: str
    serial: str | None = None

    def matches(self, *, uuid: str | None, pci_bus_id: str | None) -> bool:
        if uuid and self.uuid.upper() == uuid.upper():
            return True
        return bool(pci_bus_id and self.pci_bus_id.lower() == pci_bus_id.lower())


@dataclass(frozen=True)
class GPUProcess:
    """One process with memory allocated on the GPU."""

    pid: int
    used_memory_bytes: int | None  # None when NVML cannot report it
    kind: str  # "compute" or "graphics"


@dataclass(frozen=True)
class GPUHealth:
    """Health flags derived from NVML thresholds and error state."""

    device_lost: bool = False
    thermal_slowdown: bool = False
    power_brake: bool = False
    shutdown_threshold_c: int | None = None
    slowdown_threshold_c: int | None = None
    power_limit_watts: float | None = None
    throttle_reasons: int = 0


@dataclass(frozen=True)
class GPUStatus:
    """Snapshot of one GPU at one instant."""

    identity: DeviceIdentity
    timestamp: float

    total_vram_bytes: int
    free_vram_bytes: int
    used_vram_bytes: int
    reserved_vram_bytes: int

    gpu_utilization_percent: int
    memory_utilization_percent: int
    temperature_c: int | None
    power_watts: float | None

    processes: tuple[GPUProcess, ...] = field(default_factory=tuple)
    health: GPUHealth = field(default_factory=GPUHealth)

    # ---- Convenience ------------------------------------------------------

    @property
    def vram_free_fraction(self) -> float:
        if self.total_vram_bytes <= 0:
            return 0.0
        return self.free_vram_bytes / self.total_vram_bytes

    def managed_pids(self, known_pids: set[int]) -> frozenset[int]:
        """PIDs in this snapshot that the caller already knows about."""
        return frozenset(p.pid for p in self.processes if p.pid in known_pids)

    def unmanaged_processes(self, known_pids: set[int]) -> tuple[GPUProcess, ...]:
        """
        Processes not in `known_pids`.

        `known_pids` is whatever the scheduler/adapter layer tracks. This
        monitor does not decide what is managed — it only reports.
        """
        return tuple(p for p in self.processes if p.pid not in known_pids)


class NVMLUnavailable(RuntimeError):
    """Internal: NVML could not be initialised or queried."""


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------


class GPUMonitor:
    """
    Polls NVML in a background task and publishes the latest GPUStatus.

    The poll loop is resilient: a single failed poll logs and is retried on
    the next interval. A failed *initialisation* raises at start() so the
    process exits loudly rather than running without safety information.
    """

    #: Default polling interval. 2s is fine for scheduling decisions; the
    #: scheduler's own REFRESH_INTERVAL_S (5s) tolerates this comfortably.
    DEFAULT_POLL_INTERVAL_S = 2.0

    #: After this long without a successful poll, get_status() returns None.
    DEFAULT_MAX_STALENESS_S = 5.0

    #: Initialisation retry backoff, in seconds.
    INIT_RETRY_DELAYS = (0.5, 1.0, 2.0, 5.0)

    def __init__(self, config: Any) -> None:
        self._config = config

        self._device_uuid: str | None = _cfg_str(config, "device_uuid", "gpu_uuid")
        self._pci_bus_id: str | None = _cfg_str(config, "pci_bus_id", "gpu_pci_bus_id")
        self._poll_interval = float(
            _cfg_num(config, "poll_interval_seconds", self.DEFAULT_POLL_INTERVAL_S)
        )
        self._max_staleness = float(
            _cfg_num(config, "max_staleness_seconds", self.DEFAULT_MAX_STALENESS_S)
        )

        self._nvml: Any = None  # pynvml module, once imported
        self._handle: Any = None  # nvmlDevice_t
        self._identity: DeviceIdentity | None = None
        self._last_status: GPUStatus | None = None
        self._last_success_monotonic: float | None = None

        self._poll_task: asyncio.Task[None] | None = None
        self._wake = asyncio.Event()
        self._stopping = False
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._poll_task is not None:
            raise RuntimeError("gpu_monitor already started")

        await asyncio.to_thread(self._init_nvml_with_retry)
        # First poll synchronously so start() either succeeds with a real
        # snapshot or fails loudly. Do not enter the loop blind.
        await self.refresh()
        if self._last_status is None:
            raise NVMLUnavailable(
                "NVML initialised but the first device poll failed; refusing to "
                "start without GPU memory visibility"
            )

        self._stopping = False
        self._poll_task = asyncio.create_task(
            self._poll_loop(), name="banana-brain-gpu-monitor"
        )
        ident = self._identity
        LOG.info(
            "gpu_monitor started: %s (%s) uuid=%s pci=%s, poll=%.1fs",
            ident.name,
            f"index {ident.index}",
            ident.uuid,
            ident.pci_bus_id,
            self._poll_interval,
        )

    async def stop(self) -> None:
        self._stopping = True
        self._wake.set()
        task = self._poll_task
        self._poll_task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await asyncio.to_thread(self._shutdown_nvml)
        LOG.info("gpu_monitor stopped")

    # ------------------------------------------------------------------
    # Public queries
    # ------------------------------------------------------------------

    async def get_status(self) -> GPUStatus | None:
        """
        Latest snapshot, or None if unavailable/stale.

        Never raises. Returning None is the contract that tells the
        scheduler and vram_manager to fail closed.
        """
        async with self._lock:
            status = self._last_status
            last_ok = self._last_success_monotonic

        if status is None or last_ok is None:
            return None
        age = time.monotonic() - last_ok
        if age > self._max_staleness:
            LOG.warning(
                "GPU status is stale (%.1fs old, max %.1fs); reporting unavailable",
                age,
                self._max_staleness,
            )
            return None
        return status

    async def refresh(self) -> GPUStatus | None:
        """Force one poll now. Used after model unloads to confirm release."""
        try:
            status = await asyncio.to_thread(self._poll_once)
        except Exception:
            LOG.exception("forced GPU poll failed")
            return None
        if status is not None:
            await self._publish(status)
        return status

    def request_refresh(self) -> None:
        """Wake the poll loop for an immediate poll (fire-and-forget)."""
        self._wake.set()

    async def get_device_identity(self) -> DeviceIdentity | None:
        return self._identity

    # ------------------------------------------------------------------
    # Poll loop
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        consecutive_failures = 0
        while not self._stopping:
            try:
                status = await asyncio.to_thread(self._poll_once)
                if status is None:
                    raise NVMLUnavailable("poll returned no status")
                await self._publish(status)
                if consecutive_failures:
                    LOG.info(
                        "GPU monitoring recovered after %d failed poll(s)",
                        consecutive_failures,
                    )
                consecutive_failures = 0
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                consecutive_failures += 1
                # Log the first failure at warning, then throttle to avoid
                # flooding logs during a persistent driver issue.
                if consecutive_failures == 1 or consecutive_failures % 30 == 0:
                    LOG.warning(
                        "GPU poll failed (%d consecutive): %s: %s",
                        consecutive_failures,
                        type(exc).__name__,
                        exc,
                    )

            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._wake.wait(), timeout=self._poll_interval)
            self._wake.clear()

    async def _publish(self, status: GPUStatus) -> None:
        async with self._lock:
            self._last_status = status
            self._last_success_monotonic = time.monotonic()

    # ------------------------------------------------------------------
    # NVML initialisation (runs in a worker thread)
    # ------------------------------------------------------------------

    def _init_nvml_with_retry(self) -> None:
        import pynvml  # nvidia-ml-py; imports as pynvml

        self._nvml = pynvml

        last_exc: BaseException | None = None
        for attempt, delay in enumerate((0.0, *self.INIT_RETRY_DELAYS), start=1):
            if delay:
                time.sleep(delay)
            try:
                pynvml.nvmlInit()
                self._handle = self._select_device()
                self._identity = self._read_identity(self._handle)
                LOG.info(
                    "NVML ready (driver %s, CUDA %s)",
                    self._safe(lambda: pynvml.nvmlSystemGetDriverVersion(), "?"),
                    self._safe(lambda: pynvml.nvmlSystemGetCudaDriverVersion_v2(), "?"),
                )
                return
            except Exception as exc:
                last_exc = exc
                LOG.warning(
                    "NVML init attempt %d/%d failed: %s: %s",
                    attempt,
                    len(self.INIT_RETRY_DELAYS) + 1,
                    type(exc).__name__,
                    exc,
                )
                with contextlib.suppress(Exception):
                    pynvml.nvmlShutdown()

        raise NVMLUnavailable(
            f"NVML could not be initialised after "
            f"{len(self.INIT_RETRY_DELAYS) + 1} attempts: {last_exc}"
        )

    def _shutdown_nvml(self) -> None:
        if self._nvml is None:
            return
        try:
            self._nvml.nvmlShutdown()
        except Exception:
            LOG.debug("nvmlShutdown raised; ignoring", exc_info=True)
        finally:
            self._handle = None

    def _select_device(self) -> Any:  # noqa: C901,RUF100
        """
        Resolve the configured GPU by UUID or PCI bus ID.

        Selection policy, in order:
          1. Explicit uuid from config.
          2. Explicit pci_bus_id from config.
          3. If exactly one NVML device is visible, use it.
          4. Otherwise refuse: multi-GPU hosts must specify which device
             Banana Brain owns. Guessing is how the wrong card gets drained.
        """
        nvml = self._nvml

        if self._device_uuid:
            try:
                handle = nvml.nvmlDeviceGetHandleByUUID(self._device_uuid)
                LOG.info("selected GPU by UUID %s", self._device_uuid)
                return handle
            except Exception as exc:
                raise NVMLUnavailable(
                    f"configured device_uuid {self._device_uuid!r} not found: {exc}"
                ) from exc

        if self._pci_bus_id:
            try:
                handle = nvml.nvmlDeviceGetHandleByPciBusId_v2(self._pci_bus_id)
                LOG.info("selected GPU by PCI bus ID %s", self._pci_bus_id)
                return handle
            except Exception as exc:
                raise NVMLUnavailable(
                    f"configured pci_bus_id {self._pci_bus_id!r} not found: {exc}"
                ) from exc

        count = nvml.nvmlDeviceGetCount_v2()
        if count == 1:
            return nvml.nvmlDeviceGetHandleByIndex_v2(0)

        names = []
        for i in range(count):
            try:
                h = nvml.nvmlDeviceGetHandleByIndex_v2(i)
                names.append(
                    f"  index={i} name={self._safe(lambda h=h: nvml.nvmlDeviceGetName(h), '?')}"
                    f" uuid={self._safe(lambda h=h: nvml.nvmlDeviceGetUUID(h), '?')}"
                )
            except Exception:
                names.append(f"  index={i} <unqueryable>")
        raise NVMLUnavailable(
            "multiple GPUs visible and no device_uuid / pci_bus_id configured; "
            "refusing to guess. Visible devices:\n" + "\n".join(names)
        )

    def _read_identity(self, handle: Any) -> DeviceIdentity:
        nvml = self._nvml
        pci = self._safe(lambda: nvml.nvmlDeviceGetPciInfo_v3(handle), None)
        pci_bus = getattr(pci, "busId", None) if pci is not None else None
        if isinstance(pci_bus, bytes):
            pci_bus = pci_bus.decode("utf-8", "replace")
        return DeviceIdentity(
            index=self._safe(lambda: nvml.nvmlDeviceGetIndex(handle), -1),
            name=str(self._safe(lambda: nvml.nvmlDeviceGetName(handle), "unknown")),
            uuid=str(self._safe(lambda: nvml.nvmlDeviceGetUUID(handle), "")),
            pci_bus_id=str(pci_bus or ""),
            serial=self._optional_str(lambda: nvml.nvmlDeviceGetSerial(handle)),
        )

    # ------------------------------------------------------------------
    # One poll (runs in a worker thread)
    # ------------------------------------------------------------------

    def _poll_once(self) -> GPUStatus | None:
        nvml = self._nvml
        handle = self._handle
        identity = self._identity
        if nvml is None or handle is None or identity is None:
            return None

        now = time.time()

        mem = nvml.nvmlDeviceGetMemoryInfo(handle)
        total = int(mem.total)
        free = int(mem.free)
        used = int(mem.used)
        reserved = int(getattr(mem, "reserved", 0) or 0)

        rates = self._safe(lambda: nvml.nvmlDeviceGetUtilizationRates(handle), None)
        gpu_util = int(getattr(rates, "gpu", 0) or 0)
        mem_util = int(getattr(rates, "memory", 0) or 0)

        temperature = self._safe(
            lambda: nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU),
            None,
        )
        power_mw = self._safe(lambda: nvml.nvmlDeviceGetPowerUsage(handle), None)
        power_w = (float(power_mw) / 1000.0) if power_mw is not None else None

        health = self._read_health(handle)
        processes = self._read_processes(handle)

        return GPUStatus(
            identity=identity,
            timestamp=now,
            total_vram_bytes=total,
            free_vram_bytes=free,
            used_vram_bytes=used,
            reserved_vram_bytes=reserved,
            gpu_utilization_percent=gpu_util,
            memory_utilization_percent=mem_util,
            temperature_c=int(temperature) if temperature is not None else None,
            power_watts=power_w,
            processes=processes,
            health=health,
        )

    def _read_health(self, handle: Any) -> GPUHealth:
        nvml = self._nvml
        shutdown_c = self._safe(
            lambda: nvml.nvmlDeviceGetTemperatureThreshold(
                handle, nvml.NVML_TEMPERATURE_THRESHOLD_SHUTDOWN
            ),
            None,
        )
        slowdown_c = self._safe(
            lambda: nvml.nvmlDeviceGetTemperatureThreshold(
                handle, nvml.NVML_TEMPERATURE_THRESHOLD_SLOWDOWN
            ),
            None,
        )
        limit_mw = self._safe(
            lambda: nvml.nvmlDeviceGetEnforcedPowerLimit(handle), None
        )
        throttle = self._safe(
            lambda: nvml.nvmlDeviceGetCurrentClocksThrottleReasons(handle), 0
        )
        throttle = int(throttle or 0)

        hw_slowdown = getattr(nvml, "nvmlClocksThrottleReasonHwSlowdown", 0x8)
        sw_slowdown = getattr(nvml, "nvmlClocksThrottleReasonSwThermalSlowdown", 0x20)
        power_brake = getattr(
            nvml, "nvmlClocksThrottleReasonHwPowerBrakeSlowdown", 0x80
        )
        return GPUHealth(
            thermal_slowdown=bool(throttle & (hw_slowdown | sw_slowdown)),
            power_brake=bool(throttle & power_brake),
            shutdown_threshold_c=int(shutdown_c) if shutdown_c is not None else None,
            slowdown_threshold_c=int(slowdown_c) if slowdown_c is not None else None,
            power_limit_watts=(
                float(limit_mw) / 1000.0 if limit_mw is not None else None
            ),
            throttle_reasons=throttle,
        )

    def _read_processes(self, handle: Any) -> tuple[GPUProcess, ...]:
        """
        Enumerate compute and graphics processes.

        On failure of either query we return what we have and log once at
        debug. A missing process list is not fatal: it degrades the
        scheduler's ability to distinguish managed from unmanaged work,
        but VRAM totals are still authoritative.
        """
        nvml = self._nvml
        out: list[GPUProcess] = []
        for kind, fn_name in (
            ("compute", "nvmlDeviceGetComputeRunningProcesses"),
            ("graphics", "nvmlDeviceGetGraphicsRunningProcesses"),
        ):
            fn = getattr(nvml, fn_name, None)
            if not callable(fn):
                continue
            try:
                procs = fn(handle)
            except Exception as exc:
                LOG.debug("%s failed: %s", fn_name, exc)
                continue
            for p in procs:
                raw = getattr(p, "usedGpuMemory", None)
                used = int(raw) if isinstance(raw, int) and raw >= 0 else None
                out.append(
                    GPUProcess(pid=int(p.pid), used_memory_bytes=used, kind=kind)
                )

        # Deduplicate by pid (a process can appear in both lists).
        seen: dict[int, GPUProcess] = {}
        for proc in out:
            existing = seen.get(proc.pid)
            if existing is None or (
                existing.used_memory_bytes is None and proc.used_memory_bytes
            ):
                seen[proc.pid] = proc
        return tuple(seen.values())

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe(fn: Any, default: Any) -> Any:
        try:
            return fn()
        except Exception:
            return default

    @staticmethod
    def _optional_str(fn: Any) -> str | None:
        try:
            value = fn()
        except Exception:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8", "replace")
        return str(value) if value else None


# ---------------------------------------------------------------------------
# Config helpers (tolerant of dataclass, mapping, or attribute access)
# ---------------------------------------------------------------------------


def _cfg_get(config: Any, *names: str) -> Any:
    for name in names:
        if isinstance(config, dict):
            if name in config:
                return config[name]
            continue
        value = getattr(config, name, None)
        if value is not None:
            return value
    return None


def _cfg_str(config: Any, *names: str) -> str | None:
    value = _cfg_get(config, *names)
    return str(value) if value else None


def _cfg_num(config: Any, name: str, default: float) -> float:
    value = _cfg_get(config, name)
    return float(value) if isinstance(value, (int, float)) else default
