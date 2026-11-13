"""Tests for huey.banana_brain.ollama_adapter."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from huey.banana_brain.config import BananaBrainConfig
from huey.banana_brain.ollama_adapter import (
    OllamaAdapter,
    _cfg_bool,
    _cfg_num,
    _cfg_str,
    _expires_sort_key,
    _is_pinned,
    _model_matches,
    _parse_parameter_size,
)

from .conftest import make_job

# ---------------------------------------------------------------------------
# Helper: an in-process fake Ollama
# ---------------------------------------------------------------------------


class FakeOllama:
    """A minimal Ollama-shaped HTTP server."""

    def __init__(self):
        self.tags = [{"name": "qwen2.5:32b"}]
        self.loaded: list[dict] = []
        self.show_details: dict = {
            "parameter_size": "32B",
            "quantization_level": "Q4_K_M",
        }
        self.generate_responses: list[dict] = []
        self.chat_responses: list[dict] = []
        self.unload_calls: list[str] = []
        self.generate_calls: list[dict] = []
        self.chat_calls: list[dict] = []
        self.stream_body: bytes | None = None
        self.generate_http_error: int | None = None
        self.tags_status = 200
        self.ps_status = 200
        self.show_status = 200
        self.show_response = None
        self.generate_response_override = None

    def make_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/api/tags", self._tags)
        app.router.add_get("/api/ps", self._ps)
        app.router.add_post("/api/show", self._show)
        app.router.add_post("/api/generate", self._generate)
        app.router.add_post("/api/chat", self._chat)
        return app

    async def _tags(self, request):
        return web.json_response({"models": self.tags}, status=self.tags_status)

    async def _ps(self, request):
        return web.json_response({"models": self.loaded}, status=self.ps_status)

    async def _show(self, request):
        body = self.show_response or {"details": self.show_details}
        return web.json_response(body, status=self.show_status)

    async def _generate(self, request):
        body = await request.json()
        self.generate_calls.append(body)
        if self.generate_http_error is not None:
            return web.Response(status=self.generate_http_error, text="boom")
        if body.get("keep_alive") == 0:
            self.unload_calls.append(body["model"])
            return web.json_response({"done": True})
        if self.stream_body is not None:
            return web.Response(
                body=self.stream_body, content_type="application/x-ndjson"
            )
        if self.generate_response_override is not None:
            return web.json_response(self.generate_response_override)
        if self.generate_responses:
            return web.json_response(self.generate_responses.pop(0))
        return web.json_response({"response": "hello", "done": True, "eval_count": 5})

    async def _chat(self, request):
        body = await request.json()
        self.chat_calls.append(body)
        if self.chat_responses:
            return web.json_response(self.chat_responses.pop(0))
        return web.json_response(
            {
                "message": {"role": "assistant", "content": "hi"},
                "done": True,
                "eval_count": 2,
            }
        )


@pytest.fixture
async def fake_ollama():
    server = FakeOllama()
    test_server = TestServer(server.make_app())
    await test_server.start_server()
    try:
        yield test_server, server
    finally:
        await test_server.close()


@pytest.fixture
async def adapter(test_config, fake_ollama):
    server, _ = fake_ollama
    cfg = BananaBrainConfig(
        ollama_base_url=str(server.make_url("")).rstrip("/"),
        ollama_connect_timeout_seconds=2,
        ollama_request_timeout_seconds=5,
        database_path=test_config.database_path,
    )
    a = OllamaAdapter(cfg, vram_manager=None)
    await a.start()
    try:
        yield a
    finally:
        await a.stop()


# ---------------------------------------------------------------------------
# Model matching (pure helper)
# ---------------------------------------------------------------------------


def test_model_matches_exact():
    entry = {"name": "qwen2.5:32b"}
    assert _model_matches(entry, "qwen2.5:32b")


def test_model_matches_default_tag():
    entry = {"name": "qwen2.5:latest"}
    assert _model_matches(entry, "qwen2.5")


def test_model_matches_misses():
    entry = {"name": "llama3:8b"}
    assert not _model_matches(entry, "qwen2.5:32b")


def test_parse_parameter_size():
    assert _parse_parameter_size("32B") == 32.0
    assert _parse_parameter_size("7b") == 7.0
    assert _parse_parameter_size("1.5B") == 1.5
    assert _parse_parameter_size("500M") == 0.5
    assert _parse_parameter_size("") is None
    assert _parse_parameter_size("unknown") is None


def test_expiry_and_config_helper_fallbacks():
    assert not _is_pinned({"expires_at": ""})
    assert not _is_pinned({"expires_at": "not-a-date"})
    assert _expires_sort_key({}) == float("inf")
    assert _expires_sort_key({"expires_at": "not-a-date"}) == float("inf")
    assert _cfg_str({"first": "", "second": 4}, "first", "second") == "4"
    assert _cfg_str({}, "missing") is None
    assert _cfg_num({"count": "3"}, "count", 1.5) == 1.5
    assert _cfg_bool({}, "enabled", True) is True
    assert _cfg_bool({"enabled": " YES "}, "enabled", False) is True
    assert _cfg_bool({"enabled": "no"}, "enabled", True) is False
    assert _cfg_bool({"enabled": 0}, "enabled", True) is False


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


async def test_start_probes_tags(adapter, fake_ollama):
    _, server = fake_ollama
    assert server.tags == [{"name": "qwen2.5:32b"}]
    # adapter.start() succeeded — the probe would have raised otherwise.


async def test_start_probe_failure_closes_session(fake_ollama, test_config):
    server, fake = fake_ollama
    fake.tags_status = 503
    cfg = BananaBrainConfig(
        ollama_base_url=str(server.make_url("")).rstrip("/"),
        database_path=test_config.database_path,
    )
    instance = OllamaAdapter(cfg, vram_manager=None)
    with pytest.raises(RuntimeError, match="tags returned 503"):
        await instance.start()
    assert instance._session is None


async def test_duplicate_start_and_unstarted_stop(adapter, test_config):
    with pytest.raises(RuntimeError, match="already started"):
        await adapter.start()
    fresh = OllamaAdapter(test_config, vram_manager=None)
    await fresh.stop()
    assert fresh._session is None


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


async def test_execute_generate(adapter, fake_ollama):
    _, server = fake_ollama
    server.generate_responses = [
        {
            "response": "Paris is the capital.",
            "done": True,
            "eval_count": 5,
            "load_duration": 1_500_000_000,
        }
    ]
    job = make_job(
        adapter="ollama",
        payload={
            "model": "qwen2.5:32b",
            "prompt": "What is the capital of France?",
        },
    )
    result = await adapter.execute(job)
    assert result["response"].startswith("Paris")
    assert result["load_duration_ns"] == 1_500_000_000
    assert server.generate_calls[-1]["model"] == "qwen2.5:32b"
    assert server.generate_calls[-1]["keep_alive"] != 0


async def test_execute_chat(adapter, fake_ollama):
    _, server = fake_ollama
    server.chat_responses = [
        {
            "message": {"role": "assistant", "content": "Hello!"},
            "done": True,
        }
    ]
    job = make_job(
        adapter="ollama",
        payload={
            "model": "qwen2.5:32b",
            "messages": [{"role": "user", "content": "hi"}],
        },
    )
    result = await adapter.execute(job)
    assert result["message"]["content"] == "Hello!"
    assert server.chat_calls[-1]["messages"][0]["content"] == "hi"


async def test_execute_requires_model(adapter):
    job = make_job(adapter="ollama", payload={"prompt": "hi"})
    with pytest.raises(ValueError, match="model"):
        await adapter.execute(job)


async def test_execute_requires_messages_or_prompt(adapter):
    job = make_job(adapter="ollama", payload={"model": "qwen2.5:32b"})
    with pytest.raises(ValueError, match=r"messages.*prompt"):
        await adapter.execute(job)


async def test_execute_rejects_both(adapter):
    job = make_job(
        adapter="ollama",
        payload={
            "model": "qwen2.5:32b",
            "prompt": "hi",
            "messages": [{"role": "user", "content": "hi"}],
        },
    )
    with pytest.raises(ValueError, match="not both"):
        await adapter.execute(job)


async def test_execute_passes_options(adapter, fake_ollama):
    _, server = fake_ollama
    job = make_job(
        adapter="ollama",
        payload={
            "model": "qwen2.5:32b",
            "prompt": "hi",
            "options": {"temperature": 0.1, "num_predict": 50},
            "format": "json",
        },
    )
    await adapter.execute(job)
    body = server.generate_calls[-1]
    assert body["options"]["temperature"] == 0.1
    assert body["format"] == "json"


async def test_execute_stream_concatenates_chunks(adapter, fake_ollama):
    _, server = fake_ollama
    server.stream_body = (
        b'{"response":"Hello "}\n'
        b"not-json\n"
        b'{"response":"world","done":true,"eval_count":2}\n'
    )
    job = make_job(
        adapter="ollama",
        payload={"model": "qwen2.5:32b", "prompt": "hi", "stream": True},
    )
    result = await adapter.execute(job)
    assert result["response"] == "Hello world"
    assert result["eval_count"] == 2


async def test_execute_stream_raises_ollama_error(adapter, fake_ollama):
    _, server = fake_ollama
    server.stream_body = b'{"error":"model failed"}\n'
    job = make_job(
        adapter="ollama",
        payload={"model": "qwen2.5:32b", "prompt": "hi", "stream": True},
    )
    with pytest.raises(RuntimeError, match="stream error: model failed"):
        await adapter.execute(job)


async def test_execute_stream_observes_cancel_request(adapter, fake_ollama):
    _, server = fake_ollama
    server.stream_body = b'{"response":"first"}\n'
    job = make_job(
        adapter="ollama",
        payload={"model": "qwen2.5:32b", "prompt": "hi", "stream": True},
    )
    assert await adapter.request_cancel(job)
    with pytest.raises(asyncio.CancelledError):
        await adapter.execute(job)


async def test_execute_http_error_raises(adapter, fake_ollama):
    _, server = fake_ollama
    server.generate_http_error = 500
    job = make_job(
        adapter="ollama",
        payload={
            "model": "qwen2.5:32b",
            "prompt": "hi",
        },
    )
    with pytest.raises(RuntimeError, match="ollama"):
        await adapter.execute(job)


async def test_execute_rejects_non_object_response(adapter, fake_ollama):
    _, server = fake_ollama
    server.generate_response_override = ["not", "an", "object"]
    job = make_job(adapter="ollama", payload={"model": "qwen2.5:32b", "prompt": "hi"})
    with pytest.raises(RuntimeError, match="non-object JSON"):
        await adapter.execute(job)
    assert "qwen2.5:32b" not in adapter._active_models


# ---------------------------------------------------------------------------
# estimate_vram
# ---------------------------------------------------------------------------


async def test_estimate_uses_measured_size_when_loaded(adapter, fake_ollama):
    _, server = fake_ollama
    server.loaded = [
        {
            "name": "qwen2.5:32b",
            "size_vram": 22 * 1024**3,
        }
    ]
    job = make_job(adapter="ollama", payload={"model": "qwen2.5:32b"})
    estimate = await adapter.estimate_vram(job)
    assert estimate == 22 * 1024**3


async def test_estimate_uses_details_when_not_loaded(adapter, fake_ollama):
    _, server = fake_ollama
    server.loaded = []
    server.show_details = {
        "parameter_size": "32B",
        "quantization_level": "Q4_K_M",
    }
    job = make_job(adapter="ollama", payload={"model": "qwen2.5:32b"})
    estimate = await adapter.estimate_vram(job)
    # 32e9 * 0.60 * 1.25 = ~24 GiB.
    assert 20 * 1024**3 < estimate < 28 * 1024**3


async def test_estimate_falls_back_to_default(adapter, fake_ollama):
    _, server = fake_ollama
    server.show_details = {}  # no parameter_size
    job = make_job(adapter="ollama", payload={"model": "mystery:latest"})
    estimate = await adapter.estimate_vram(job)
    assert estimate == 8 * 1024**3


async def test_estimate_uses_top_level_show_fields_and_unknown_quant(
    adapter, fake_ollama
):
    _, server = fake_ollama
    server.loaded = [{"name": "m:latest", "size_vram": 0}]
    server.show_response = {
        "parameter_size": "7B",
        "quantization_level": "unknown_quant",
    }
    estimate = await adapter.estimate_vram(
        make_job(adapter="ollama", payload={"model": "m"})
    )
    assert estimate > 5 * 1024**3


async def test_estimate_defaults_when_show_endpoint_errors(adapter, fake_ollama):
    _, server = fake_ollama
    server.show_status = 500
    estimate = await adapter.estimate_vram(
        make_job(adapter="ollama", payload={"model": "missing"})
    )
    assert estimate == 8 * 1024**3


async def test_estimate_requires_model(adapter):
    job = make_job(adapter="ollama", payload={})
    with pytest.raises(ValueError, match="model"):
        await adapter.estimate_vram(job)


# ---------------------------------------------------------------------------
# unload_idle_models
# ---------------------------------------------------------------------------


async def test_unload_skips_active_models(adapter, fake_ollama):
    _, server = fake_ollama
    server.loaded = [{"name": "qwen2.5:32b", "size_vram": 22 * 1024**3}]
    # Simulate an active request on that model.
    adapter._active_models.add("qwen2.5:32b")
    freed = await adapter.unload_idle_models(1 * 1024**3)
    assert freed == 0
    assert server.unload_calls == []


async def test_unload_removes_idle_models(adapter, fake_ollama):
    _, server = fake_ollama
    server.loaded = [
        {
            "name": "qwen2.5:32b",
            "size_vram": 22 * 1024**3,
            "expires_at": "2024-01-01T00:00:00Z",
        }
    ]
    freed = await adapter.unload_idle_models(10 * 1024**3)
    assert freed == 22 * 1024**3
    assert server.unload_calls == ["qwen2.5:32b"]


async def test_unload_stops_when_enough_freed(adapter, fake_ollama):
    _, server = fake_ollama
    server.loaded = [
        {"name": "a", "size_vram": 5 * 1024**3, "expires_at": "2024-01-01T00:00:00Z"},
        {"name": "b", "size_vram": 5 * 1024**3, "expires_at": "2024-01-02T00:00:00Z"},
    ]
    freed = await adapter.unload_idle_models(5 * 1024**3)
    assert freed == 5 * 1024**3
    assert len(server.unload_calls) == 1


async def test_unload_handles_empty_and_http_error_model_lists(adapter, fake_ollama):
    _, server = fake_ollama
    assert await adapter.unload_idle_models(1) == 0
    server.ps_status = 500
    server.loaded = [{"name": "m", "size_vram": 10}]
    assert await adapter.unload_idle_models(1) == 0


async def test_unload_skips_pinned_and_unnamed_models(adapter, fake_ollama):
    _, server = fake_ollama
    server.loaded = [
        {"name": "pinned", "size_vram": 10, "expires_at": "2999-01-01T00:00:00Z"},
        {"size_vram": 20},
    ]
    assert await adapter.unload_idle_models(1) == 0
    assert server.unload_calls == []


async def test_cancel_without_model_returns_false(adapter):
    assert (
        await adapter.request_cancel(
            make_job(adapter="ollama", payload={"prompt": "hi"})
        )
        is False
    )


@pytest.mark.asyncio
async def test_remaining_ollama_response_and_helper_branches(
    adapter, fake_ollama, test_config, monkeypatch
):
    import huey.banana_brain.ollama_adapter as ollama_module
    from huey.banana_brain.ollama_adapter import _int_or_none, _safe_text

    _, server_state = fake_ollama
    job = make_job(
        adapter="ollama",
        payload={
            "model": "qwen2.5:32b",
            "prompt": "hello",
            "system": "be concise",
            "template": "{{ .Prompt }}",
        },
    )
    await adapter.execute(job)
    assert server_state.generate_calls[-1]["system"] == "be concise"
    assert server_state.generate_calls[-1]["template"] == "{{ .Prompt }}"

    server_state.generate_response_override = {"error": "generation failed"}
    with pytest.raises(RuntimeError, match="ollama error: generation failed"):
        await adapter.execute(
            make_job(adapter="ollama", payload={"model": "qwen2.5:32b", "prompt": "x"})
        )
    server_state.generate_response_override = None

    server_state.stream_body = (
        b'{"message":{"role":"assistant","content":"reply"},"done":true}\n'
    )
    result = await adapter.execute(
        make_job(
            adapter="ollama",
            payload={
                "model": "qwen2.5:32b",
                "prompt": "x",
                "stream": True,
            },
        )
    )
    assert result["response"] == "reply"
    server_state.stream_body = None

    async def fail_show(_model):
        raise OSError("show unavailable")

    monkeypatch.setattr(adapter, "_show_details", fail_show)
    assert await adapter.estimate_vram(
        make_job(adapter="ollama", payload={"model": "missing"})
    ) == 8 * 1024**3

    server_state.loaded = [
        {
            "name": "idle",
            "size_vram": 1024,
            "expires_at": "2024-01-01T00:00:00Z",
        }
    ]

    async def fail_unload(_session, _model):
        raise OSError("unload unavailable")

    monkeypatch.setattr(adapter, "_unload_model", fail_unload)
    assert await adapter.unload_idle_models(2048) == 0
    monkeypatch.undo()

    class BrokenSession:
        closed = False

        def get(self, *_args, **_kwargs):
            raise OSError("request failed")

        async def close(self):
            self.closed = True

    old_session = adapter._session
    adapter._session = BrokenSession()
    assert await adapter._list_loaded() == []
    await adapter._session.close()
    adapter._session = old_session

    server_state.loaded = [{"name": "idle", "size_vram": 1024}]
    server_state.generate_http_error = 500
    assert await adapter.unload_idle_models(2048) == 0
    server_state.generate_http_error = None

    with pytest.raises(RuntimeError, match="session is not open"):
        OllamaAdapter(test_config, vram_manager=None)._require_session()

    class Match:
        def group(self, name):
            return "not-a-number" if name == "num" else "b"

    class Regex:
        def search(self, _text):
            return Match()

    monkeypatch.setattr(ollama_module, "_PARAM_RE", Regex())
    assert _parse_parameter_size("custom") is None
    assert _int_or_none("invalid") is None
    assert _is_pinned({"expires_at": "2999-01-01T00:00:00"}) is True
    assert _expires_sort_key({"expires_at": "2024-01-01T00:00:00"}) > 0

    class UnreadableResponse:
        async def text(self):
            raise RuntimeError("unreadable")

    assert await _safe_text(UnreadableResponse()) == "<unreadable body>"
