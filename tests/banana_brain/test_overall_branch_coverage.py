"""Targeted tests for the remaining Banana Brain branch arcs."""

from __future__ import annotations

import argparse
import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer, make_mocked_request

from huey.banana_brain.audio_adapter import AudioAdapter
from huey.banana_brain.comfyui_adapter import ComfyUIAdapter
from huey.banana_brain.config import BananaBrainConfig, ConfigError, _to_bool
from huey.banana_brain.gpu_modes import GPUMode, GPUModeManager
from huey.banana_brain.gpu_monitor import GPUMonitor
from huey.banana_brain.job_models import Job, Priority
from huey.banana_brain.metrics import JobMetric, Metrics, _job_to_metric
from huey.banana_brain.notifications import (
    NotificationLevel,
    WebhookBackend,
)
from huey.banana_brain.ollama_adapter import OllamaAdapter
from huey.banana_brain.priority_manager import PriorityManager
from huey.banana_brain import scheduler_api as api_module
from huey.banana_brain import scheduler_cli as cli

from .conftest import make_job
from .test_audio_adapter import Response as AudioResponse
from .test_audio_adapter import adapter as make_audio_adapter
from .test_notifications import note
from .test_scheduler_api import make_api
from .test_watchdog import make_watchdog


@pytest.mark.asyncio
async def test_audio_optional_stop_synthesis_and_probe_branches():
    empty = AudioAdapter({}, object())
    await empty.stop()

    coqui = make_audio_adapter(
        {
            "audio_tts_backend": "coqui",
            "audio_tts_base_url": "http://coqui",
        },
        AudioResponse(audio=b"wave"),
    )
    coqui._tts_default_model = ""
    result = await coqui.execute(
        make_job(
            payload={"task": "synthesize", "text": "hello", "voice": "", "model": ""}
        )
    )
    body = coqui._session.calls[0][2]["json"]
    assert result["backend"] == "coqui"
    assert "speaker" not in body
    assert "model_name" not in body

    probe = make_audio_adapter(
        {"audio_tts_backend": "coqui", "audio_tts_base_url": "http://coqui"},
        AudioResponse(status=200),
    )
    await probe._probe_tts()


@pytest.mark.asyncio
async def test_comfyui_poll_continues_after_nonterminal_history():
    adapter = ComfyUIAdapter(BananaBrainConfig(), vram_manager=None)
    terminal = {"status": {"status_str": "success"}}
    adapter._get_history_entry = AsyncMock(
        side_effect=[{"status": {"status_str": "running"}}, terminal]
    )
    result = await adapter._poll_until_done(
        object(),
        "prompt",
        timeout=1,
        poll_interval=0,
        job=make_job(adapter="comfyui", payload={}),
    )
    assert result is terminal


def test_to_bool_rejects_non_bool_non_string():
    with pytest.raises(ConfigError, match="expected bool"):
        _to_bool("enabled", 1, source="test")


@pytest.mark.asyncio
async def test_gpu_mode_restore_stop_cancel_and_housekeeping_branches(tmp_path):
    state_path = tmp_path / "mode.json"
    state_path.write_text(
        '{"mode":"gaming","previous_non_exclusive_mode":""}', encoding="utf-8"
    )
    restored = GPUModeManager(
        {"mode_persistence_enabled": True, "mode_state_path": str(state_path)},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    await restored.start()
    assert restored.current_mode is GPUMode.GAMING
    await restored.stop()

    no_uninstall = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=SimpleNamespace(set_admission_checker=object()),
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    no_uninstall._admission_installed = True
    await no_uninstall.stop()

    jobs = [Job(adapter="audio", payload={})]
    manager = GPUModeManager(
        {"mode_persistence_enabled": False},
        scheduler=SimpleNamespace(),
        priority_manager=SimpleNamespace(),
        job_store=SimpleNamespace(),
        adapters={},
    )
    manager._suspended_jobs = jobs
    assert await manager.cancel_suspended("missing") is False
    manager._housekeeping_stop.set()
    await manager._housekeeping_loop()


def test_gpu_monitor_deduplicates_process_memory_updates(test_config):
    monitor = GPUMonitor(test_config)

    class NVML:
        def nvmlDeviceGetComputeRunningProcesses(self, _handle):
            return [
                SimpleNamespace(pid=1, usedGpuMemory=4096),
                SimpleNamespace(pid=2, usedGpuMemory=None),
            ]

        def nvmlDeviceGetGraphicsRunningProcesses(self, _handle):
            return [
                SimpleNamespace(pid=1, usedGpuMemory=None),
                SimpleNamespace(pid=2, usedGpuMemory=2048),
            ]

    monitor._nvml = NVML()
    processes = {item.pid: item for item in monitor._read_processes(object())}
    assert processes[1].used_memory_bytes == 4096
    assert processes[2].used_memory_bytes == 2048


@pytest.mark.asyncio
async def test_job_store_schema_without_transaction_and_empty_prune(
    job_store, monkeypatch
):
    class BadSchema:
        in_transaction = False

        def execute(self, statement, *_args):
            if statement == "PRAGMA user_version":
                return SimpleNamespace(fetchone=lambda: (0,))
            raise AssertionError(statement)

        def executescript(self, _script):
            raise RuntimeError("schema failed")

    with pytest.raises(RuntimeError, match="schema failed"):
        job_store._init_schema(BadSchema())

    calls = 0

    async def sleep_once_then_cancel(_seconds):
        nonlocal calls
        calls += 1
        if calls > 1:
            raise asyncio.CancelledError

    async def empty_prune():
        return {"expired": 0}

    monkeypatch.setattr(asyncio, "sleep", sleep_once_then_cancel)
    monkeypatch.setattr(job_store, "prune", empty_prune)
    with pytest.raises(asyncio.CancelledError):
        await job_store._prune_loop()
    assert calls == 2


@pytest.mark.asyncio
async def test_metrics_empty_loads_and_non_dict_job_metrics():
    store = SimpleNamespace(list_recent=AsyncMock(return_value=[]))
    metrics = Metrics({}, gpu_monitor=SimpleNamespace(), job_store=store)
    metrics._explicit_loads["empty"] = []
    assert await metrics.query_model_load_times(60) == {}

    no_load = JobMetric(
        job_id="j",
        adapter="ollama",
        state="completed",
        submitted_at=1,
        started_at=2,
        finished_at=3,
        wait_s=1,
        run_s=1,
        total_s=2,
        load_duration_s=0,
        error_class=None,
    )
    assert metrics._model_loads_summary([no_load]) == {}
    item = SimpleNamespace(
        id="j",
        adapter="ollama",
        state="completed",
        submitted_at=1,
        started_at=2,
        finished_at=3,
        result=SimpleNamespace(metrics=[]),
        last_error=None,
    )
    assert _job_to_metric(item).load_duration_s is None


@pytest.mark.asyncio
async def test_webhook_without_token_and_success_response(monkeypatch):
    captured = {}

    class Response:
        status = 204

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

    class Session:
        closed = False

        def post(self, _url, *, json):
            captured["body"] = json
            return Response()

        async def close(self):
            self.closed = True

    session = Session()

    def create_session(**kwargs):
        captured["headers"] = kwargs["headers"]
        return session

    monkeypatch.setattr(
        "huey.banana_brain.notifications.aiohttp.ClientSession", create_session
    )
    backend = WebhookBackend(
        "https://example.invalid/hook",
        token=None,
        min_level=NotificationLevel.INFO,
    )
    await backend.send(note())
    assert "Authorization" not in captured["headers"]
    assert captured["body"]["id"] == "n1"
    await backend.close()


@pytest.mark.asyncio
async def test_ollama_stream_without_done_chunk_exits_naturally():
    adapter = OllamaAdapter({}, vram_manager=None)

    class Content:
        async def __aiter__(self):
            yield b'{"response":"final chunk"}'

    class Response:
        content = Content()

    result = await adapter._consume_stream(
        Response(),
        make_job(adapter="ollama", payload={"model": "qwen", "prompt": "hello"}),
    )
    assert result["response"] == "final chunk"


def test_priority_aging_cap_at_safety_does_not_log():
    manager = PriorityManager(
        {
            "priority_aging_cap": int(Priority.SAFETY),
            "priority_aging_interval_seconds": 60,
        }
    )
    assert manager._aging_cap == int(Priority.SAFETY)


@pytest.mark.asyncio
async def test_scheduler_without_optional_vram_methods(scheduler):
    sched, _adapter, _monitor = scheduler
    sched._adapters["no-estimator"] = object()
    assert (
        await sched._estimate_vram(
            make_job(adapter="no-estimator", estimated_vram_bytes=None)
        )
        == 8 * 1024**3
    )

    sched._vram_manager = SimpleNamespace()
    await sched._run_job(make_job(adapter="fake"))


@pytest.mark.asyncio
async def test_api_inflight_nonzero_and_status_without_optional_modes():
    api = make_api(token="secret")
    api._inflight_count = 1
    request = make_mocked_request("GET", "/status")

    async def handler(_request):
        return api_module.web.Response(text="ok")

    assert (await api._inflight_middleware(request, handler)).status == 200
    assert api._inflight_count == 1

    app = web.Application(
        middlewares=[
            api._error_middleware,
            api._auth_middleware,
            api._inflight_middleware,
        ]
    )
    api._install_routes(app)
    async with TestClient(TestServer(app)) as client:
        response = await client.get(
            "/status", headers={"Authorization": "Bearer secret"}
        )
        assert response.status == 200
        assert "mode" not in await response.json()


@pytest.mark.asyncio
async def test_cli_health_and_vram_without_optional_fields(capsys):
    class Client:
        async def request(self, _method, _path):
            return 200, []

        async def request_ok(self, _method, _path, _body=None):
            return {
                "gpu_state_known": True,
                "total_vram_bytes": 1,
                "free_vram_bytes": 1,
                "reservations": [],
            }

    client = Client()
    assert (
        await cli._cmd_health(argparse.Namespace(json=False), client) == cli.ExitCode.OK
    )
    assert (
        await cli._cmd_vram(argparse.Namespace(json=False), client) == cli.ExitCode.OK
    )
    assert "status:" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_watchdog_safety_clear_branch_with_unknown_temperature():
    watchdog = make_watchdog(status=SimpleNamespace(temperature_c=None, health=None))
    watchdog._halt_triggered_for.add("temperature_ceiling:85")
    watchdog._temperature_cleared_at = time.monotonic()
    assert await watchdog._check_temperature() == []
