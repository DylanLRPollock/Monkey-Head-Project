"""
banana_brain.metrics — operational metrics and time-series aggregation.

Responsibilities (from the Banana Brain design doc, §1 row 17):
  * Record GPU utilisation, VRAM, temperature and power samples over time.
  * Derive waiting times, run times, throughput and failure rates from
    job_store (no eager recording — the store already has the data).
  * Derive model load times from per-job results where the adapter reports
    them (currently Ollama via load_duration_ns).
  * Serve aggregates (min/max/mean/p50/p95/p99) for a caller-specified
    time window.

Public API:

  async start()                                       -> None
  async stop()                                        -> None
  async sample_once()                                 -> None    (tests)
  async snapshot(window_s=None)                       -> dict
  async query_gpu_utilization(window_s=None)          -> list[GPUSample]
  async query_aggregate(sample_kind, window_s)        -> Aggregate
  async query_throughput(window_s, group_by="adapter") -> dict
  async query_failures(window_s, group_by="adapter")   -> dict
  async query_waiting_times(window_s)                 -> Aggregate
  async query_run_times(window_s)                     -> Aggregate
  async query_model_load_times(window_s)              -> dict[str, Aggregate]
  def   record_model_load(adapter, model, duration_s) -> None    (optional)

Lifecycle (called by the composition root):
  async start()
  async stop()

Data sources:

  gpu_monitor.get_status()   -> GPUStatus | None   sampled periodically
  job_store.list_recent()    -> list[Job]          queried per metrics call
  job.result                 -> dict | JobResult   for load_duration_ns

Derivation notes:

  * Waiting time:  started_at - submitted_at. Excludes jobs that never ran.
  * Run time:      finished_at - started_at. Excludes jobs that never started.
  * Throughput:    terminal jobs in the window / window_hours. Reported per
                   adapter and overall.
  * Failures:      jobs with state == "failed" in the window. Reported per
                   adapter and by error class (first token of last_error).
  * Model loads:   only for adapters whose result contains "load_duration_ns"
                   and whose value is > 0. Ollama reports 0 when the model
                   was already resident, so a non-zero filter measures only
                   actual cold loads.

Configuration fields consumed:

  metrics_enabled:                  default true
  metrics_sample_interval_seconds:  default 10.0
  metrics_ring_size:                default 3600
  metrics_default_window_seconds:   default 3600

Constraints:

  * All query methods accept window_s=None, meaning "all available data."
  * The ring buffer is bounded; requesting a window longer than its coverage
    returns only the samples present, not an error.
  * Query methods return empty/zero aggregates rather than raising when no
    data is available. This is deliberate: /metrics must always respond.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import math
import time
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

__all__ = [
    "Aggregate",
    "GPUSample",
    "JobMetric",
    "Metrics",
]

LOG = logging.getLogger("banana_brain.metrics")

GIB = 1024**3


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GPUSample:
    """One point on the GPU time series."""

    at: float
    gpu_utilization_percent: int
    memory_utilization_percent: int
    vram_used_bytes: int
    vram_total_bytes: int
    temperature_c: int | None
    power_watts: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "at": self.at,
            "gpu_utilization_percent": self.gpu_utilization_percent,
            "memory_utilization_percent": self.memory_utilization_percent,
            "vram_used_bytes": self.vram_used_bytes,
            "vram_total_bytes": self.vram_total_bytes,
            "temperature_c": self.temperature_c,
            "power_watts": self.power_watts,
        }


@dataclass(frozen=True)
class JobMetric:
    """Derived timing view of a terminal job."""

    job_id: str
    adapter: str
    state: str  # "completed" | "failed" | "cancelled"
    submitted_at: float
    started_at: float | None
    finished_at: float
    wait_s: float | None
    run_s: float | None
    total_s: float
    load_duration_s: float | None
    error_class: str | None  # first token of last_error, if any


@dataclass(frozen=True)
class Aggregate:
    """Summary statistics for a numeric series."""

    count: int = 0
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    p50: float | None = None
    p95: float | None = None
    p99: float | None = None

    def to_dict(self) -> dict[str, float | None]:
        return {
            "count": self.count,
            "min": self.min,
            "max": self.max,
            "mean": self.mean,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
        }


# ---------------------------------------------------------------------------
# Ring buffer
# ---------------------------------------------------------------------------


class _RingBuffer:
    """
    Fixed-capacity FIFO. Discards oldest entries on overflow.

    Append is O(1); snapshot materialisation is O(n) but only called from
    query paths. Trades one copy for simple, predictable memory use.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("ring buffer capacity must be >= 1")
        self._capacity = int(capacity)
        self._items: list[Any] = []

    def __len__(self) -> int:
        return len(self._items)

    def append(self, item: Any) -> None:
        self._items.append(item)
        if len(self._items) > self._capacity:
            # Delete in one slice to keep this O(k) amortised, not O(n).
            excess = len(self._items) - self._capacity
            del self._items[:excess]

    def since(self, cutoff: float | None) -> list[Any]:
        if cutoff is None:
            return list(self._items)
        return [item for item in self._items if item.at >= cutoff]

    def clear(self) -> None:
        self._items.clear()


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class Metrics:
    """
    Time-series aggregator for GPU and job metrics.

    The only background activity is the GPU sample loop. Everything else is
    derived on demand from job_store, so the metrics class does not need to
    see individual jobs as they complete — it just queries them when asked.
    """

    DEFAULT_SAMPLE_INTERVAL_S = 10.0
    DEFAULT_RING_SIZE = 3600
    DEFAULT_WINDOW_S = 3600.0

    #: How many recent terminal jobs to fetch per metrics query. Bounds the
    #: cost of querying job_store; enough for ~10k jobs over the retention
    #: window at typical throughput.
    JOB_QUERY_LIMIT = 10_000

    def __init__(
        self,
        config: Any,
        *,
        gpu_monitor: Any,
        job_store: Any,
    ) -> None:
        self._config = config
        self._gpu_monitor = gpu_monitor
        self._job_store = job_store

        self._enabled = _cfg_bool(config, "metrics_enabled", True)
        self._sample_interval = float(
            _cfg_num(
                config,
                "metrics_sample_interval_seconds",
                self.DEFAULT_SAMPLE_INTERVAL_S,
            )
        )
        ring_size = int(_cfg_num(config, "metrics_ring_size", self.DEFAULT_RING_SIZE))
        self._default_window = float(
            _cfg_num(
                config,
                "metrics_default_window_seconds",
                self.DEFAULT_WINDOW_S,
            )
        )

        self._gpu_samples = _RingBuffer(ring_size)
        self._sample_task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self._started_at: float | None = None
        self._sample_count: int = 0

        #: Optional adapter-sourced model load times. Keyed by
        #: "adapter:model". Adapters that choose to report load durations
        #: via record_model_load() populate this; the default Ollama path
        #: derives them from job results at query time instead.
        self._explicit_loads: dict[str, list[float]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if not self._enabled:
            LOG.info("metrics disabled by config (metrics_enabled=false)")
            return
        if self._sample_task is not None:
            raise RuntimeError("metrics already started")

        self._started_at = time.time()
        # Prime the buffer with one sample so early queries are not empty.
        try:
            await self.sample_once()
        except Exception:
            LOG.exception("metrics: initial sample failed")

        self._stop_event.clear()
        self._sample_task = asyncio.create_task(
            self._sample_loop(), name="banana-brain-metrics"
        )
        LOG.info(
            "metrics ready (sample_interval=%.0fs, ring_size=%d, "
            "default_window=%.0fs)",
            self._sample_interval,
            len(self._gpu_samples),
            self._default_window,
        )

    async def stop(self) -> None:
        self._stop_event.set()
        task = self._sample_task
        self._sample_task = None
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        LOG.info("metrics stopped after %d GPU sample(s)", self._sample_count)

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------

    async def sample_once(self) -> None:
        """Take one GPU sample. Public for tests and CLI-driven probing."""
        status = await self._gpu_monitor.get_status()
        if status is None:
            return
        try:
            sample = GPUSample(
                at=float(status.timestamp),
                gpu_utilization_percent=int(
                    getattr(status, "gpu_utilization_percent", 0) or 0
                ),
                memory_utilization_percent=int(
                    getattr(status, "memory_utilization_percent", 0) or 0
                ),
                vram_used_bytes=int(getattr(status, "used_vram_bytes", 0) or 0),
                vram_total_bytes=int(getattr(status, "total_vram_bytes", 0) or 0),
                temperature_c=_opt_int(getattr(status, "temperature_c", None)),
                power_watts=_opt_float(getattr(status, "power_watts", None)),
            )
        except Exception:
            LOG.exception("metrics: could not build GPUSample from status")
            return
        self._gpu_samples.append(sample)
        self._sample_count += 1

    async def _sample_loop(self) -> None:
        while not self._stop_event.is_set():
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._sample_interval
                )
            if self._stop_event.is_set():
                return
            try:
                await self.sample_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOG.exception("metrics: sampling iteration failed; continuing")

    # ------------------------------------------------------------------
    # Optional explicit recording
    # ------------------------------------------------------------------

    def record_model_load(self, adapter: str, model: str, duration_s: float) -> None:
        """
        Record a model-load duration reported by an adapter.

        Adapters that already surface load times in their job results
        (Ollama) do not need to call this — those are picked up at query
        time. This hook exists for adapters that want to report loads that
        happen outside the per-job path (e.g. a preload on mode entry).

        Truncates the per-key buffer to the configured ring size.
        """
        if not self._enabled:
            return
        key = f"{adapter}:{model}"
        values = self._explicit_loads[key]
        values.append(max(0.0, float(duration_s)))
        if len(values) > len(self._gpu_samples) or len(values) > 3600:
            # Keep an upper bound in sync with the GPU buffer capacity.
            del values[: len(values) - min(len(values), 3600)]

    # ------------------------------------------------------------------
    # Snapshot (the /metrics response body)
    # ------------------------------------------------------------------

    async def snapshot(self, window_s: float | None = None) -> dict[str, Any]:
        """Aggregate everything into one JSON-serialisable dict."""
        window = float(window_s or self._default_window)
        cutoff = time.time() - window

        gpu_recent = self._gpu_samples.since(cutoff)
        gpu_current = gpu_recent[-1] if gpu_recent else None

        jobs = await self._load_jobs_since(cutoff)

        return {
            "window_s": window,
            "generated_at": time.time(),
            "uptime_seconds": (
                round(time.time() - self._started_at, 1)
                if self._started_at is not None
                else None
            ),
            "gpu": {
                "current": gpu_current.to_dict() if gpu_current else None,
                "sample_count": len(gpu_recent),
                "gpu_utilization_percent": _aggregate(
                    s.gpu_utilization_percent for s in gpu_recent
                ).to_dict(),
                "memory_utilization_percent": _aggregate(
                    s.memory_utilization_percent for s in gpu_recent
                ).to_dict(),
                "temperature_c": _aggregate(
                    s.temperature_c for s in gpu_recent
                ).to_dict(),
                "power_watts": _aggregate(s.power_watts for s in gpu_recent).to_dict(),
            },
            "jobs": self._job_summary(jobs, window),
            "model_loads": self._model_loads_summary(jobs),
        }

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    async def query_gpu_utilization(
        self, window_s: float | None = None
    ) -> list[GPUSample]:
        cutoff = time.time() - float(window_s) if window_s else None
        return self._gpu_samples.since(cutoff)

    async def query_aggregate(
        self, sample_kind: str, window_s: float | None = None
    ) -> Aggregate:
        cutoff = time.time() - float(window_s) if window_s else None
        samples = self._gpu_samples.since(cutoff)
        if sample_kind == "gpu_utilization_percent":
            values = [s.gpu_utilization_percent for s in samples]
        elif sample_kind == "memory_utilization_percent":
            values = [s.memory_utilization_percent for s in samples]
        elif sample_kind == "temperature_c":
            values = [s.temperature_c for s in samples]
        elif sample_kind == "power_watts":
            values = [s.power_watts for s in samples]
        else:
            raise ValueError(f"unknown sample_kind {sample_kind!r}")
        return _aggregate(values)

    async def query_throughput(
        self,
        window_s: float,
        group_by: str = "adapter",
    ) -> dict[str, Any]:
        cutoff = time.time() - float(window_s)
        jobs = await self._load_jobs_since(cutoff)
        return self._throughput_from_jobs(jobs, window_s, group_by=group_by)

    async def query_failures(
        self,
        window_s: float,
        group_by: str = "adapter",
    ) -> dict[str, Any]:
        cutoff = time.time() - float(window_s)
        jobs = await self._load_jobs_since(cutoff)
        return self._failures_from_jobs(jobs, group_by=group_by)

    async def query_waiting_times(self, window_s: float) -> Aggregate:
        cutoff = time.time() - float(window_s)
        jobs = await self._load_jobs_since(cutoff)
        return _aggregate(j.wait_s for j in jobs)

    async def query_run_times(self, window_s: float) -> Aggregate:
        cutoff = time.time() - float(window_s)
        jobs = await self._load_jobs_since(cutoff)
        return _aggregate(j.run_s for j in jobs)

    async def query_model_load_times(self, window_s: float) -> dict[str, Aggregate]:
        cutoff = time.time() - float(window_s)
        jobs = await self._load_jobs_since(cutoff)
        by_key: dict[str, list[float]] = defaultdict(list)
        for job in jobs:
            if job.load_duration_s and job.load_duration_s > 0:
                by_key[f"{job.adapter}"].append(job.load_duration_s)
        # Merge in explicit loads (adapter-reported, non-job-sourced).
        for key, values in self._explicit_loads.items():
            if values:
                by_key[key].extend(values)
        return {key: _aggregate(values) for key, values in by_key.items()}

    # ------------------------------------------------------------------
    # Job derivation
    # ------------------------------------------------------------------

    async def _load_jobs_since(self, cutoff: float) -> list[JobMetric]:
        """
        Fetch recent terminal jobs from job_store and derive timing metrics.

        The query returns the most recent JOB_QUERY_LIMIT terminal jobs; we
        then filter by finished_at >= cutoff. This is exact as long as no
        more than JOB_QUERY_LIMIT terminal jobs completed in the window —
        which holds easily at the scales this scheduler targets. If a very
        busy deployment exceeds the limit, extend job_store with a
        list_finished_since(cutoff) method.
        """
        try:
            jobs = await self._job_store.list_recent(
                limit=self.JOB_QUERY_LIMIT,
                states=("completed", "failed", "cancelled"),
            )
        except Exception:
            LOG.exception("metrics: job_store.list_recent failed")
            return []

        metrics: list[JobMetric] = []
        for job in jobs:
            finished_at = getattr(job, "finished_at", None)
            if finished_at is None or finished_at < cutoff:
                continue
            metrics.append(_job_to_metric(job))
        return metrics

    def _job_summary(self, jobs: list[JobMetric], window_s: float) -> dict[str, Any]:
        return {
            "terminal_count": len(jobs),
            "throughput": self._throughput_from_jobs(
                jobs, window_s, group_by="adapter"
            ),
            "failures": self._failures_from_jobs(jobs, group_by="adapter"),
            "waiting_times_s": _aggregate(j.wait_s for j in jobs).to_dict(),
            "run_times_s": _aggregate(j.run_s for j in jobs).to_dict(),
            "total_times_s": _aggregate(j.total_s for j in jobs).to_dict(),
        }

    def _throughput_from_jobs(
        self, jobs: list[JobMetric], window_s: float, *, group_by: str
    ) -> dict[str, Any]:
        window_hours = max(1.0 / 3600.0, float(window_s) / 3600.0)
        if group_by == "adapter":
            counts: dict[str, int] = defaultdict(int)
            for job in jobs:
                counts[job.adapter] += 1
            return {
                adapter: {
                    "count": count,
                    "per_hour": round(count / window_hours, 3),
                }
                for adapter, count in counts.items()
            }
        if group_by == "state":
            counts = defaultdict(int)
            for job in jobs:
                counts[job.state] += 1
            return {
                state: {
                    "count": count,
                    "per_hour": round(count / window_hours, 3),
                }
                for state, count in counts.items()
            }
        raise ValueError(f"unknown group_by {group_by!r}")

    def _failures_from_jobs(
        self, jobs: list[JobMetric], *, group_by: str
    ) -> dict[str, Any]:
        failures = [j for j in jobs if j.state == "failed"]
        if group_by == "adapter":
            counts: dict[str, int] = defaultdict(int)
            classes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
            for job in failures:
                counts[job.adapter] += 1
                if job.error_class:
                    classes[job.adapter][job.error_class] += 1
            return {
                adapter: {
                    "count": count,
                    "by_class": dict(sorted(classes[adapter].items())),
                }
                for adapter, count in counts.items()
            }
        if group_by == "error_class":
            counts = defaultdict(int)
            for job in failures:
                counts[job.error_class or "unknown"] += 1
            return dict(sorted(counts.items()))
        raise ValueError(f"unknown group_by {group_by!r}")

    def _model_loads_summary(self, jobs: list[JobMetric]) -> dict[str, Any]:
        by_adapter: dict[str, list[float]] = defaultdict(list)
        for job in jobs:
            if job.load_duration_s and job.load_duration_s > 0:
                by_adapter[job.adapter].append(job.load_duration_s)
        for key, values in self._explicit_loads.items():
            if values:
                by_adapter[key].extend(values)
        return {key: _aggregate(values).to_dict() for key, values in by_adapter.items()}


# ---------------------------------------------------------------------------
# Derivation
# ---------------------------------------------------------------------------


def _job_to_metric(job: Any) -> JobMetric:
    submitted_at = float(getattr(job, "submitted_at", None) or 0.0)
    started_at = _opt_float(getattr(job, "started_at", None))
    finished_at = float(getattr(job, "finished_at", None) or 0.0)
    state = str(getattr(job.state, "value", job.state))

    wait_s = (started_at - submitted_at) if started_at else None
    run_s = (finished_at - started_at) if started_at and finished_at else None
    total_s = max(0.0, finished_at - submitted_at) if submitted_at else 0.0

    load_duration_ns: int | None = None
    result = getattr(job, "result", None)
    if isinstance(result, dict):
        load_duration_ns = _opt_int(result.get("load_duration_ns"))
    elif result is not None:
        # JobResult carries metrics; check for load_duration there too.
        metrics = getattr(result, "metrics", None)
        if isinstance(metrics, dict):
            load_duration_ns = _opt_int(metrics.get("load_duration_ns"))

    last_error = getattr(job, "last_error", None)
    error_class = None
    if isinstance(last_error, str) and last_error:
        # "RuntimeError: ollama returned 500: ..." -> "RuntimeError"
        error_class = last_error.split(":", 1)[0].strip() or "unknown"

    return JobMetric(
        job_id=str(getattr(job, "id", "")),
        adapter=str(getattr(job, "adapter", "")),
        state=state,
        submitted_at=submitted_at,
        started_at=started_at,
        finished_at=finished_at,
        wait_s=max(0.0, wait_s) if wait_s is not None else None,
        run_s=max(0.0, run_s) if run_s is not None else None,
        total_s=total_s,
        load_duration_s=(
            load_duration_ns / 1e9
            if load_duration_ns is not None and load_duration_ns > 0
            else None
        ),
        error_class=error_class,
    )


def _aggregate(values: Iterable[Any]) -> Aggregate:
    clean: list[float] = []
    for value in values:
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if math.isnan(numeric) or math.isinf(numeric):
            continue
        clean.append(numeric)

    if not clean:
        return Aggregate()

    clean.sort()
    n = len(clean)

    def _at(p: float) -> float:
        # Nearest-rank percentile; adequate for the sample sizes involved.
        idx = min(n - 1, max(0, math.ceil(p * n) - 1))
        return clean[idx]

    return Aggregate(
        count=n,
        min=round(clean[0], 4),
        max=round(clean[-1], 4),
        mean=round(sum(clean) / n, 4),
        p50=round(_at(0.50), 4),
        p95=round(_at(0.95), 4),
        p99=round(_at(0.99), 4),
    )


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _opt_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _opt_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def _cfg_get(config: Any, name: str) -> Any:
    if isinstance(config, dict):
        return config.get(name)
    return getattr(config, name, None)


def _cfg_num(config: Any, name: str, default: float) -> float:
    value = _cfg_get(config, name)
    return float(value) if isinstance(value, (int, float)) else default


def _cfg_bool(config: Any, name: str, default: bool) -> bool:
    value = _cfg_get(config, name)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
