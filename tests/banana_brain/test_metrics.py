"""Unit coverage for GPU and job metrics aggregation."""

from __future__ import annotations

import math
import time
from types import SimpleNamespace

import pytest

from huey.banana_brain.metrics import (
    Aggregate,
    GPUSample,
    Metrics,
    _aggregate,
    _job_to_metric,
    _opt_float,
    _opt_int,
    _RingBuffer,
)


class Monitor:
    def __init__(self, status=None):
        self.status = status

    async def get_status(self):
        return self.status


class Store:
    def __init__(self, jobs=(), error=None):
        self.jobs = list(jobs)
        self.error = error
        self.calls = []

    async def list_recent(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.jobs


def status(at=100.0, **changes):
    fields = {
        "timestamp": at,
        "gpu_utilization_percent": 35,
        "memory_utilization_percent": 40,
        "used_vram_bytes": 100,
        "total_vram_bytes": 200,
        "temperature_c": 60,
        "power_watts": 75.5,
    }
    fields.update(changes)
    return SimpleNamespace(**fields)


def job(
    *,
    state="completed",
    submitted=90,
    started=92,
    finished=99,
    adapter="ollama",
    result=None,
    error=None,
):
    return SimpleNamespace(
        id="j1",
        adapter=adapter,
        state=state,
        submitted_at=submitted,
        started_at=started,
        finished_at=finished,
        result=result,
        last_error=error,
    )


def make_metrics(config=None, status_value=None, jobs=(), store_error=None):
    return Metrics(
        config or {},
        gpu_monitor=Monitor(status_value),
        job_store=Store(jobs, store_error),
    )


def test_ring_buffer_bounds_filters_and_clears():
    ring = _RingBuffer(2)
    with pytest.raises(ValueError):
        _RingBuffer(0)
    ring.append(SimpleNamespace(at=1))
    ring.append(SimpleNamespace(at=2))
    ring.append(SimpleNamespace(at=3))
    assert [x.at for x in ring.since(None)] == [2, 3]
    assert [x.at for x in ring.since(3)] == [3]
    assert len(ring) == 2
    ring.clear()
    assert len(ring) == 0


def test_sample_and_aggregate_values():
    sample = GPUSample(1, 2, 3, 4, 5, None, None)
    assert sample.to_dict()["vram_total_bytes"] == 5
    assert _aggregate([None, "bad", math.nan, math.inf]) == Aggregate()
    result = _aggregate([5, 1, 3, 2, 4])
    assert result.to_dict() == {
        "count": 5,
        "min": 1.0,
        "max": 5.0,
        "mean": 3.0,
        "p50": 3.0,
        "p95": 5.0,
        "p99": 5.0,
    }
    assert _opt_float("invalid") is None
    assert _opt_float("1.5") == 1.5
    assert _opt_int("invalid") is None
    assert _opt_int("3") == 3


def test_job_derivation_handles_dict_and_object_results():
    result = _job_to_metric(
        job(result={"load_duration_ns": "2000000000"}, error="  : empty")
    )
    assert result.wait_s == 2
    assert result.run_s == 7
    assert result.total_s == 9
    assert result.load_duration_s == 2
    assert result.error_class == "unknown"
    object_result = _job_to_metric(
        job(result=SimpleNamespace(metrics={"load_duration_ns": 1_500_000_000}))
    )
    assert object_result.load_duration_s == 1.5
    assert _job_to_metric(job(started=None, finished=None)).wait_s is None
    assert _job_to_metric(job(started=None, finished=None)).run_s is None
    assert _job_to_metric(job(started=95, finished=91)).run_s == 0
    assert _job_to_metric(job(submitted=None, started=0, finished=0)).total_s == 0
    assert (
        _job_to_metric(job(result={"load_duration_ns": "bad"})).load_duration_s is None
    )


@pytest.mark.asyncio
async def test_lifecycle_sampling_queries_and_serialized_snapshot():
    metrics = make_metrics(
        {"metrics_sample_interval_seconds": 0.01, "metrics_ring_size": 2},
        status(time.time()),
        [
            job(
                submitted=time.time() - 9,
                started=time.time() - 7,
                finished=time.time(),
                result={"load_duration_ns": 2_000_000_000},
            )
        ],
    )
    assert await metrics.query_gpu_utilization() == []
    await metrics.start()
    with pytest.raises(RuntimeError, match="already started"):
        await metrics.start()
    await metrics.sample_once()
    await metrics.sample_once()
    samples = await metrics.query_gpu_utilization()
    assert len(samples) == 2
    assert (await metrics.query_aggregate("gpu_utilization_percent")).mean == 35
    assert (await metrics.query_aggregate("temperature_c")).min == 60
    assert (await metrics.query_aggregate("power_watts")).max == 75.5
    assert (await metrics.query_aggregate("memory_utilization_percent")).count == 2
    with pytest.raises(ValueError, match="unknown sample_kind"):
        await metrics.query_aggregate("bad")
    metrics.record_model_load("comfy", "sd", -2)
    assert (await metrics.query_model_load_times(100))["comfy:sd"].min == 0
    snap = await metrics.snapshot(100)
    assert snap["gpu"]["sample_count"] == 2
    assert snap["jobs"]["terminal_count"] == 1
    assert snap["model_loads"]["ollama"]["mean"] == 2
    assert snap["uptime_seconds"] is not None
    await metrics.stop()
    await metrics.stop()
    assert metrics._sample_task is None


@pytest.mark.asyncio
async def test_disabled_metrics_and_missing_status_are_safe():
    disabled = make_metrics({"metrics_enabled": "false"}, status())
    await disabled.start()
    disabled.record_model_load("a", "b", 2)
    assert disabled._sample_task is None
    assert disabled._explicit_loads == {}
    await disabled.sample_once()
    assert len(await disabled.query_gpu_utilization()) == 1
    enabled = make_metrics({}, None)
    await enabled.sample_once()
    assert enabled._sample_count == 0
    assert (await enabled.snapshot())["gpu"]["current"] is None
    assert (await enabled.query_aggregate("power_watts")) == Aggregate()


@pytest.mark.asyncio
async def test_job_queries_groupings_errors_and_empty_store():
    now = time.time()
    jobs = [
        job(
            state="completed",
            submitted=now - 9,
            started=now - 7,
            finished=now,
            adapter="ollama",
            result={"load_duration_ns": 1_000_000_000},
        ),
        job(state="failed", finished=now, adapter="ollama", error="ValueError: bad"),
        job(state="failed", finished=now, adapter="audio", error=None),
        job(state="cancelled", finished=now, adapter="audio"),
        job(state="completed", finished=1, adapter="old"),
        job(state="completed", finished=None, adapter="unfinished"),
    ]
    metrics = make_metrics({}, jobs=jobs)
    recent = await metrics._load_jobs_since(50)
    assert len(recent) == 4
    assert metrics._job_store.calls[-1]["states"] == (
        "completed",
        "failed",
        "cancelled",
    )
    assert await metrics.query_throughput(3600, "state") == {
        "completed": {"count": 1, "per_hour": 1.0},
        "failed": {"count": 2, "per_hour": 2.0},
        "cancelled": {"count": 1, "per_hour": 1.0},
    }
    assert (await metrics.query_throughput(1, "adapter"))["ollama"]["per_hour"] == 7200
    assert await metrics.query_failures(3600, "error_class") == {
        "ValueError": 1,
        "unknown": 1,
    }
    assert (await metrics.query_failures(3600))["ollama"]["by_class"] == {
        "ValueError": 1
    }
    assert (await metrics.query_waiting_times(3600)).count == 4
    assert (await metrics.query_run_times(3600)).count == 4
    assert (await metrics.query_model_load_times(3600))["ollama"].count == 1
    with pytest.raises(ValueError):
        await metrics.query_throughput(10, "unknown")
    with pytest.raises(ValueError):
        await metrics.query_failures(10, "unknown")
    broken = make_metrics({}, store_error=RuntimeError("offline"))
    assert await broken._load_jobs_since(0) == []
    assert await broken.query_failures(10) == {}


@pytest.mark.asyncio
async def test_sampling_loop_continues_after_sample_error(monkeypatch):
    metrics = make_metrics({"metrics_sample_interval_seconds": 0.001})
    calls = 0

    async def flaky():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary")
        metrics._stop_event.set()

    monkeypatch.setattr(metrics, "sample_once", flaky)
    await metrics._sample_loop()
    assert calls == 2


def test_metrics_optional_integer_and_config_helper_paths():
    from huey.banana_brain.metrics import _cfg_bool, _cfg_get, _opt_int

    assert _opt_int(None) is None
    assert _opt_int("invalid") is None
    assert _cfg_get(SimpleNamespace(value="x"), "value") == "x"
    assert _cfg_get({}, "missing") is None
    assert _cfg_bool({"enabled": True}, "enabled", False) is True
    assert _cfg_bool({"enabled": " true "}, "enabled", False) is True
    assert _cfg_bool({"enabled": 1}, "enabled", False) is True


@pytest.mark.asyncio
async def test_metrics_initial_failure_malformed_sample_and_stop_paths(monkeypatch):
    metrics = make_metrics({"metrics_sample_interval_seconds": 60})

    async def fail_initial():
        raise RuntimeError("initial sample unavailable")

    monkeypatch.setattr(metrics, "sample_once", fail_initial)
    await metrics.start()
    await metrics.stop()

    malformed = make_metrics(
        status_value=SimpleNamespace(timestamp="not-a-timestamp")
    )
    await malformed.sample_once()
    assert malformed._sample_count == 0

    class EmptyBuffer:
        def __len__(self):
            return 0

    recorder = make_metrics()
    recorder._gpu_samples = EmptyBuffer()
    recorder.record_model_load("audio", "voice", 1.0)
    assert recorder._explicit_loads["audio:voice"] == [1.0]

    stopping = make_metrics({"metrics_sample_interval_seconds": 60})
    task = asyncio.create_task(stopping._sample_loop())
    await asyncio.sleep(0)
    stopping._stop_event.set()
    await task

    cancelling = make_metrics({"metrics_sample_interval_seconds": 60})
    entered = asyncio.Event()

    async def wait_for_cancel():
        entered.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(cancelling, "sample_once", wait_for_cancel)
    task = asyncio.create_task(cancelling._sample_loop())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
