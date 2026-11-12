"""Tests for the PyGPT HTTP bridge and Ollama adapter translation."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import ClassVar

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from huey.banana_brain import pygpt_adapter as module
from huey.banana_brain.job_models import Job, JobResult, JobState


class Ollama:
    def __init__(self, models=None):
        self.models = models or []
        self.calls = []

    async def _list_loaded(self):
        return self.models

    async def execute(self, job):
        self.calls.append(("execute", job))
        return {"response": "ok"}

    async def estimate_vram(self, job):
        self.calls.append(("estimate", job))
        return 123

    async def unload_idle_models(self, needed):
        return needed

    async def request_cancel(self, job):
        self.calls.append(("cancel", job))
        return True


class Scheduler:
    def __init__(self, state=JobState.COMPLETED, result=None):
        self.state = state
        self.result = result or {"message": {"content": "answer"}}
        self.jobs = {}
        self.cancelled = []

    async def submit(self, job):
        job.state = self.state
        job.result = self.result
        self.jobs[job.id] = job

    async def cancel(self, job_id, *, force=False):
        self.cancelled.append((job_id, force))


class Store:
    def __init__(self, scheduler):
        self.scheduler = scheduler

    async def get(self, job_id):
        return self.scheduler.jobs.get(job_id)


def make_adapter(config=None, *, models=None, state=JobState.COMPLETED, result=None):
    scheduler = Scheduler(state, result)
    ollama = Ollama(models)
    instance = module.PyGPTAdapter(
        config or {},
        scheduler=scheduler,
        job_store=Store(scheduler),
        ollama_adapter=ollama,
    )
    return instance, scheduler, ollama


def test_helpers_response_shapes_options_and_binding():
    assert module._extract_text({"message": {"content": "chat"}}) == "chat"
    assert (
        module._extract_text({"message": {"content": None}, "response": "fallback"})
        == "fallback"
    )
    assert module._extract_text({"response": "completion"}) == "completion"
    assert module._extract_text({}) == ""
    response = module._openai_chat_response(
        request_id="id",
        model="m",
        result={
            "message": {"content": "hello"},
            "tool_calls": [{"id": "t"}],
            "done_reason": "stop",
            "eval_count": "3",
            "prompt_eval_count": 2,
        },
    )
    assert response["choices"][0]["message"]["tool_calls"] == [{"id": "t"}]
    assert response["usage"] == {
        "prompt_tokens": 2,
        "completion_tokens": 3,
        "total_tokens": 5,
    }
    assert (
        module._usage_from_result({"eval_count": "bad", "prompt_eval_count": None})[
            "total_tokens"
        ]
        == 0
    )
    assert module._openai_body_to_ollama_options(
        {
            "temperature": 0,
            "max_tokens": 5,
            "max_completion_tokens": 6,
            "seed": 7,
            "ignored": 1,
        }
    ) == {
        "temperature": 0,
        "num_predict": 6,
        "seed": 7,
    }
    for status, kind in [
        (400, "invalid_request_error"),
        (401, "authentication_error"),
        (404, "not_found_error"),
        (429, "rate_limit_error"),
        (499, "cancelled"),
        (503, "server_error"),
        (302, "api_error"),
    ]:
        assert module._error_type_for(status) == kind
    error = module._openai_error(400, "bad")
    assert error.status == 400
    assert module._split_bind(":8080") == ("127.0.0.1", 8080)
    assert module._split_bind("localhost:8081") == ("localhost", 8081)


@pytest.mark.asyncio
async def test_model_resolution_alias_exact_single_default_and_errors():
    item, _, ollama = make_adapter(
        {"pygpt_model_aliases": {"chat": "qwen:latest"}},
        models=[{"name": "qwen:latest"}, {"model": "llama:8b"}],
    )
    assert await item._resolve_model("chat") == "qwen:latest"
    assert await item._resolve_model("llama") == "llama:8b"
    single, _, _ = make_adapter(models=[{"model": "only"}])
    assert await single._resolve_model(None) == "only"
    default, _, _ = make_adapter(
        {"pygpt_default_model": "fallback"}, models=[{"name": "a"}, {"name": "b"}]
    )
    assert await default._resolve_model("missing") == "fallback"
    empty, _, _ = make_adapter()
    with pytest.raises(ValueError, match="no Ollama model available"):
        await empty._resolve_model("missing")

    async def unavailable():
        raise RuntimeError("offline")

    ollama._list_loaded = unavailable
    assert await item._resolve_model("chat") == "qwen:latest"


@pytest.mark.asyncio
async def test_adapter_mode_translates_payload_and_forwards_calls():
    item, _, ollama = make_adapter(models=[{"name": "qwen:latest"}])
    source = Job(
        adapter="pygpt",
        payload={"model": "qwen", "prompt": "hi"},
        id="job",
        priority=42,
        owner="owner",
        idempotency_key="key",
    )
    assert await item.execute(source) == {"response": "ok"}
    synthetic = ollama.calls[-1][1]
    assert synthetic.adapter == "ollama" and synthetic.id == "job-ollama"
    assert synthetic.payload["model"] == "qwen:latest"
    assert await item.estimate_vram(source) == 123
    assert ollama.calls[-1][1].id == "job-estimate"
    assert await item.unload_idle_models(99) == 99
    assert await item.request_cancel(source) is True
    assert ollama.calls[-1][1].id == "job-cancel"
    await item.start()
    await item.stop()
    assert item._stopping is True


@pytest.mark.asyncio
async def test_build_job_validation_and_openai_option_mapping():
    item, _, _ = make_adapter()
    with pytest.raises(ValueError, match="non-empty messages"):
        item._build_job({}, model="m", kind="chat")
    with pytest.raises(ValueError, match="prompt string"):
        item._build_job({"prompt": 1}, model="m", kind="completion")
    chat = item._build_job(
        {
            "messages": [{"role": "user", "content": "x"}],
            "temperature": 0.5,
            "top_p": 0.9,
            "stop": ["!"],
            "tools": [{"type": "function"}],
        },
        model="m",
        kind="chat",
    )
    assert chat.payload["options"]["temperature"] == 0.5
    assert chat.payload["options"]["stop"] == ["!"]
    assert chat.payload["tools"]
    completion = item._build_job({"prompt": ["a", "b"]}, model="m", kind="completion")
    assert completion.payload["prompt"] == "a\nb"
    assert completion.payload["stream"] is False
    plain_text = item._build_job(
        {"prompt": "single prompt"}, model="m", kind="completion"
    )
    assert plain_text.payload["prompt"] == "single prompt"


@pytest.mark.asyncio
async def test_submit_completion_state_result_shapes_and_streaming():
    item, scheduler, _ = make_adapter()
    job = Job(adapter="ollama", payload={"model": "m"}, id="j")
    response = await item._submit_and_await(job, request_id="r", stream=False)
    assert response.status == 200
    assert json.loads(response.text)["choices"][0]["message"]["content"] == "answer"
    stream = await item._submit_and_await(job, request_id="r", stream=True)
    assert "[DONE]" in stream.text

    async def no_submit(_job):
        return None

    item._scheduler.submit = no_submit
    for state, result, expected in [
        (JobState.CANCELLED, {}, 499),
        (JobState.FAILED, {}, 502),
        (JobState.COMPLETED, "bad", 502),
        (JobState.COMPLETED, JobResult(ok=True, data={"response": "ok"}), 200),
    ]:
        scheduler.jobs[job.id] = job
        job.state, job.result = state, result
        response = await item._submit_and_await(job, request_id="r", stream=False)
        assert response.status == expected

    class UnexpectedState:
        is_terminal = True
        value = "unexpected"

    class UnexpectedJob:
        state = UnexpectedState()
        last_error = None
        result: ClassVar[dict[str, object]] = {}

    class UnexpectedStore:
        async def get(self, _job_id):
            return UnexpectedJob()

    item._job_store = UnexpectedStore()
    response = await item._submit_and_await(job, request_id="r", stream=False)
    assert response.status == 502


@pytest.mark.asyncio
async def test_http_routes_reject_invalid_input_and_advertise_models():
    item, _, ollama = make_adapter(
        {
            "pygpt_model_aliases": {"alias": "qwen", "loaded": "duplicate"},
            "pygpt_default_model": "fallback",
        }
    )
    ollama.models = [{"name": "loaded"}, {"model": "loaded"}, {"name": ""}]
    app = web.Application()
    app.router.add_post("/v1/chat/completions", item._handle_chat_completions)
    app.router.add_post("/v1/completions", item._handle_completions)
    app.router.add_get("/v1/models", item._handle_models)
    app.router.add_get("/health", item._handle_health)
    async with TestClient(TestServer(app)) as client:
        assert (await client.post("/v1/chat/completions", data="bad")).status == 400
        assert (await client.post("/v1/chat/completions", json=[])).status == 400
        assert (await client.post("/v1/completions", json={})).status == 400
        models = await (await client.get("/v1/models")).json()
        assert [entry["id"] for entry in models["data"]] == ["loaded", "alias"]
        health = await (await client.get("/health")).json()
        assert health["adapter"] == "pygpt"

        ollama._list_loaded = lambda: asyncio.sleep(0, result=[{"name": "model"}])
        success = await client.post(
            "/v1/chat/completions",
            json={
                "model": "model",
                "messages": [{"role": "user", "content": "hello"}],
                "temperature": 0.4,
            },
        )
        assert success.status == 200
        assert (await success.json())["choices"][0]["message"]["content"] == "answer"
        stream = await client.post(
            "/v1/completions",
            json={
                "model": "model",
                "prompt": ["one", "two"],
                "stream": True,
            },
        )
        assert stream.status == 200
        assert "[DONE]" in await stream.text()

        # Model resolution and job construction errors are OpenAI-shaped 400s.
        ollama._list_loaded = lambda: asyncio.sleep(0, result=[])
        no_model, _, _ = make_adapter()
        app2 = web.Application()
        app2.router.add_post("/v1/chat/completions", no_model._handle_chat_completions)
        async with TestClient(TestServer(app2)) as client2:
            assert (
                await client2.post("/v1/chat/completions", json={"messages": []})
            ).status == 400


@pytest.mark.asyncio
async def test_models_empty_fallback_and_inflight_timeout_cancel(monkeypatch):
    item, scheduler, ollama = make_adapter({"pygpt_default_model": "default"})

    async def fail_models():
        raise RuntimeError("offline")

    ollama._list_loaded = fail_models
    result = await item._handle_models(None)
    assert json.loads(result.text)["data"][0]["id"] == "default"
    item._stopping = True
    rejected = await item._serve_completion(None, {}, kind="chat")
    assert rejected.status == 503
    item._stopping = False
    item._request_timeout = 0.001
    item._scheduler.submit = lambda _job: asyncio.sleep(1)
    body = {"model": "default", "messages": [{"role": "user", "content": "x"}]}
    response = await item._serve_completion(None, body, kind="chat")
    assert response.status == 504
    await asyncio.sleep(0)
    assert scheduler.cancelled


@pytest.mark.asyncio
async def test_proxy_startup_and_shutdown_for_tcp_and_unix(monkeypatch, tmp_path):
    sites = []

    class Site:
        def __init__(self, runner, *args, **kwargs):
            self.runner = runner
            self.args = args
            self.kwargs = kwargs
            sites.append(self)

        async def start(self):
            pass

    monkeypatch.setattr(module.web, "TCPSite", Site)
    tcp, _, _ = make_adapter(
        {"pygpt_proxy_enabled": True, "pygpt_proxy_bind": "127.0.0.1:8081"}
    )
    await tcp.start()
    assert tcp._runner is not None
    assert {route.resource.canonical for route in tcp._app.router.routes()} >= {
        "/v1/chat/completions",
        "/v1/completions",
        "/v1/models",
        "/health",
    }
    assert sites[-1].kwargs == {
        "host": "127.0.0.1",
        "port": 8081,
        "shutdown_timeout": 0.1,
    }
    await tcp.stop()
    await tcp.stop()
    assert tcp._runner is None

    unix_path = tmp_path / "custom" / "pygpt.sock"
    unix_path.parent.mkdir(parents=True)
    unix_path.write_text("stale socket placeholder")
    monkeypatch.setattr(module.web, "UnixSite", Site)
    unix, _, _ = make_adapter(
        {"pygpt_proxy_enabled": True, "pygpt_proxy_socket_path": str(unix_path)}
    )
    await unix.start()
    assert Path(unix._proxy_socket) == unix_path
    assert sites[-1].kwargs["shutdown_timeout"] == 0.1
    await unix.stop()

    fallback, _, _ = make_adapter(
        {"pygpt_proxy_enabled": True, "api_socket_path": str(tmp_path / "bb.sock")}
    )
    await fallback.start()
    assert fallback._proxy_socket.endswith("bb-pygpt.sock")
    await fallback.stop()


@pytest.mark.asyncio
async def test_drain_inflight_waits_and_cancels_after_grace():
    item, _, _ = make_adapter()
    completed = asyncio.create_task(asyncio.sleep(0.01))
    completed.add_done_callback(item._forget_inflight)
    item._inflight.add(completed)
    await item._drain_inflight(0.5)
    await asyncio.sleep(0)
    assert completed.done()
    assert not item._inflight

    async def blocked():
        await asyncio.sleep(10)

    pending = asyncio.create_task(blocked())
    item._inflight.add(pending)
    await item._drain_inflight(0)
    with pytest.raises(asyncio.CancelledError):
        await pending


def test_socket_path_and_config_helpers():
    item, _, _ = make_adapter({"api_socket_path": "/run/banana.sock"})
    assert item._default_socket_path().name == "banana-pygpt.sock"
    fallback, _, _ = make_adapter()
    assert str(fallback._default_socket_path()) == "data/banana-brain-pygpt.sock"
    assert module._cfg_get({"value": 0}, "value") == 0
    assert module._cfg_get(object(), "missing") is None
    assert module._cfg_str({"value": " text "}, "value") == " text "
    assert module._cfg_str({"value": ""}, "value") is None
    assert module._cfg_num({"value": 2}, "value", 1.0) == 2.0
    assert module._cfg_num({"value": "2"}, "value", 1.0) == 1.0
    assert module._cfg_bool({"value": None}, "value", True) is True
    assert module._cfg_bool({"value": False}, "value", True) is False
    assert module._cfg_bool({"value": "yes"}, "value", False) is True
    assert module._cfg_bool({"value": 0}, "value", True) is False
    assert module._cfg_dict({"value": {"a": 1}}, "value") == {"a": 1}
    assert module._cfg_dict({"value": []}, "value") is None


@pytest.mark.asyncio
async def test_await_completion_reports_vanished_and_timed_out_jobs():
    item, scheduler, _ = make_adapter(state=JobState.PENDING)
    item._request_timeout = -1
    scheduler.jobs["pending"] = Job(
        adapter="ollama", payload={}, id="pending", state=JobState.PENDING
    )
    with pytest.raises(TimeoutError, match="did not finish"):
        await item._await_completion("pending")

    class MissingStore:
        async def get(self, _job_id):
            return None

    item._job_store = MissingStore()
    with pytest.raises(RuntimeError, match="vanished"):
        await item._await_completion("missing")
