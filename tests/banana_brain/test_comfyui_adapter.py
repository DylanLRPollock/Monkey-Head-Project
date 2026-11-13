"""Tests for huey.banana_brain.comfyui_adapter."""

from __future__ import annotations

import asyncio

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from huey.banana_brain.comfyui_adapter import (
    ComfyUIAdapter,
    _cfg_num,
    _cfg_str,
    _extract_checkpoint_names,
    _extract_error_message,
    _extract_prompt_ids,
    _extract_size_from_metadata,
    _history_is_terminal,
)
from huey.banana_brain.config import BananaBrainConfig

from .conftest import make_job, wait_until

# ---------------------------------------------------------------------------
# Fake ComfyUI
# ---------------------------------------------------------------------------


class FakeComfy:
    def __init__(self):
        self.prompts: dict[str, dict] = {}
        self.history: dict[str, dict] = {}
        self.queue_running: list[list] = []
        self.queue_pending: list[list] = []
        self.submit_errors: list[dict] = []
        self.interrupt_calls = 0
        self.free_calls = 0
        self.deleted_prompts: list[str] = []
        self.auto_complete = True
        self.metadata_size = 8 * 1024**3  # 8 GiB checkpoint
        self.system_stats_status = 200
        self.free_status = 200
        self.metadata_status = 200
        self.interrupt_status = 200
        self.queue_delete_status = 200
        self.submit_response_override = None
        self.history_response_override = None
        self.history_status = 200

    def make_app(self) -> web.Application:
        app = web.Application()
        app.router.add_get("/system_stats", self._system_stats)
        app.router.add_post("/prompt", self._submit)
        app.router.add_get("/queue", self._queue)
        app.router.add_post("/queue", self._queue_delete)
        app.router.add_get("/history/{prompt_id}", self._history)
        app.router.add_post("/interrupt", self._interrupt)
        app.router.add_post("/free", self._free)
        app.router.add_get("/view_metadata/{folder}", self._metadata)
        return app

    async def _system_stats(self, request):
        return web.json_response({}, status=self.system_stats_status)

    async def _submit(self, request):
        if self.submit_errors:
            return web.json_response(self.submit_errors.pop(0), status=400)
        body = await request.json()
        if self.submit_response_override is not None:
            return web.json_response(self.submit_response_override)
        pid = f"prompt-{len(self.prompts) + 1}"
        self.prompts[pid] = body
        if self.auto_complete:
            self.history[pid] = {
                "status": {"status_str": "success", "messages": []},
                "outputs": {"images": [{"filename": f"{pid}.png"}]},
            }
        else:
            self.queue_pending.append([1, pid, {}, {}, []])
        return web.json_response({"prompt_id": pid, "number": 1})

    async def _queue(self, request):
        return web.json_response(
            {
                "queue_running": self.queue_running,
                "queue_pending": self.queue_pending,
            }
        )

    async def _queue_delete(self, request):
        body = await request.json()
        if self.queue_delete_status >= 400:
            return web.json_response({}, status=self.queue_delete_status)
        for pid in body.get("delete") or []:
            self.deleted_prompts.append(pid)
            self.queue_pending = [e for e in self.queue_pending if e[1] != pid]
            self.history[pid] = {
                "status": {"status_str": "error", "messages": []},
            }
        return web.json_response({})

    async def _history(self, request):
        if self.history_status >= 400:
            return web.json_response({}, status=self.history_status)
        if self.history_response_override is not None:
            return web.json_response(self.history_response_override)
        pid = request.match_info["prompt_id"]
        if pid not in self.history:
            return web.json_response({})
        return web.json_response({pid: self.history[pid]})

    async def _interrupt(self, request):
        self.interrupt_calls += 1
        if self.interrupt_status >= 400:
            return web.json_response({}, status=self.interrupt_status)
        for entry in self.queue_running:
            pid = entry[1]
            self.history[pid] = {
                "status": {"status_str": "error", "messages": []},
            }
        self.queue_running = []
        return web.json_response({})

    async def _free(self, request):
        self.free_calls += 1
        return web.json_response({}, status=self.free_status)

    async def _metadata(self, request):
        return web.json_response(
            {"size": self.metadata_size}, status=self.metadata_status
        )


@pytest.fixture
async def fake_comfy():
    server = FakeComfy()
    ts = TestServer(server.make_app())
    await ts.start_server()
    try:
        yield ts, server
    finally:
        await ts.close()


@pytest.fixture
async def adapter(test_config, fake_comfy):
    ts, _ = fake_comfy
    cfg = BananaBrainConfig(
        comfyui_base_url=str(ts.make_url("")).rstrip("/"),
        comfyui_poll_interval_seconds=0.05,
        comfyui_job_timeout_seconds=2.0,
        comfyui_connect_timeout_seconds=1.0,
        database_path=test_config.database_path,
    )
    a = ComfyUIAdapter(cfg, vram_manager=None)
    await a.start()
    try:
        yield a
    finally:
        await a.stop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wf(**inputs):
    """Build a minimal ComfyUI workflow with checkpoint inputs."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": inputs,
        }
    }


def test_extract_checkpoint_names():
    wf = {
        "1": {"class_type": "X", "inputs": {"ckpt_name": "sd_xl_base.safetensors"}},
        "2": {"class_type": "Y", "inputs": {"lora_name": "detail_adder.safetensors"}},
        "3": {"class_type": "Z", "inputs": {"other": "not-a-checkpoint"}},
    }
    names = _extract_checkpoint_names(wf)
    assert "sd_xl_base.safetensors" in names
    assert "detail_adder.safetensors" in names
    assert "not-a-checkpoint" not in names


def test_extract_checkpoint_names_deduplicates_and_ignores_invalid_nodes():
    workflow = {
        "1": {"inputs": {"ckpt_name": "same.safetensors"}},
        "2": {"class_type": "X", "inputs": {"ckpt_name": "same.safetensors"}},
        "3": None,
        "4": {"inputs": ["invalid"]},
    }
    assert _extract_checkpoint_names(workflow) == ["same.safetensors"]


def test_metadata_size_and_history_error_helpers_cover_fallback_shapes():
    assert _extract_size_from_metadata({"metadata": {"file_size": 42.9}}) == 42
    assert _extract_size_from_metadata({"size": 0}) is None
    assert _extract_size_from_metadata([]) is None
    assert _history_is_terminal({"status_str": "SUCCESS"})
    assert _history_is_terminal({"status_str": "error"})
    assert not _history_is_terminal({"status_str": "running"})
    assert (
        _extract_error_message([["execution_error", {"exception_type": "OOM"}]])
        == "OOM"
    )
    assert _extract_error_message([]) == "execution_error (no detail)"
    assert _extract_error_message(None) == "unknown error"
    assert _extract_error_message(["malformed", ["other", {}]]) == (
        "execution_error (no detail)"
    )
    assert _cfg_str({"first": "", "second": 5}, "first", "second") == "5"
    assert _cfg_str({}, "missing") is None
    assert _cfg_num({"number": "bad"}, "number", 2.5) == 2.5


def test_extract_prompt_ids():
    queue = [[1, "pid-a", {}, {}, []], [2, "pid-b", {}, {}, []]]
    assert _extract_prompt_ids(queue) == {"pid-a", "pid-b"}


def test_extract_prompt_ids_ignores_malformed_entries():
    assert _extract_prompt_ids(None) == set()
    assert _extract_prompt_ids([None, [], [1], [2, "pid"], (3, "tuple")]) == {"pid"}


# ---------------------------------------------------------------------------
# Submission and polling
# ---------------------------------------------------------------------------


async def test_execute_completes(adapter, fake_comfy):
    job = make_job(
        adapter="comfyui", payload={"workflow": _wf(ckpt_name="a.safetensors")}
    )
    result = await adapter.execute(job)
    assert result["status"] == "success"
    assert result["prompt_id"] == "prompt-1"


async def test_execute_polls_until_terminal(adapter, fake_comfy):
    _, server = fake_comfy
    server.auto_complete = False
    job = make_job(
        adapter="comfyui", payload={"workflow": _wf(ckpt_name="a.safetensors")}
    )

    async def complete():
        # After a short delay, populate history to make the job finish.
        await wait_until(lambda: "prompt-1" in server.prompts)
        server.history["prompt-1"] = {
            "status": {"status_str": "success", "messages": []},
            "outputs": {},
        }
        server.queue_pending = []

    import asyncio as _asyncio

    waiter = _asyncio.create_task(complete())
    try:
        result = await adapter.execute(job)
    finally:
        waiter.cancel()
    assert result["status"] == "success"


async def test_execute_resumes_with_prompt_id(adapter, fake_comfy):
    _, server = fake_comfy
    # Pre-populate history as if the prompt was submitted before restart.
    server.history["prior-prompt"] = {
        "status": {"status_str": "success", "messages": []},
        "outputs": {},
    }
    job = make_job(
        adapter="comfyui",
        payload={
            "workflow": _wf(ckpt_name="a.safetensors"),
            "prompt_id": "prior-prompt",
        },
    )
    result = await adapter.execute(job)
    assert result["prompt_id"] == "prior-prompt"
    # No new submission occurred.
    assert len(server.prompts) == 0


async def test_execute_raises_on_execution_error(adapter, fake_comfy):
    _, server = fake_comfy
    server.auto_complete = False
    server.history["prompt-1"] = {
        "status": {
            "status_str": "error",
            "messages": [["execution_error", {"exception_message": "OOM"}]],
        },
    }
    server.queue_pending = []
    job = make_job(
        adapter="comfyui", payload={"workflow": _wf(ckpt_name="a.safetensors")}
    )
    with pytest.raises(RuntimeError, match="OOM"):
        await adapter.execute(job)


async def test_execute_validation_error(adapter, fake_comfy):
    _, server = fake_comfy
    server.submit_errors = [
        {
            "error": "invalid prompt",
            "node_errors": {"1": "bad"},
        }
    ]
    job = make_job(
        adapter="comfyui", payload={"workflow": _wf(ckpt_name="a.safetensors")}
    )
    with pytest.raises(RuntimeError, match="invalid prompt"):
        await adapter.execute(job)


async def test_execute_times_out_when_server_never_finishes(adapter, fake_comfy):
    _, server = fake_comfy
    server.auto_complete = False
    job = make_job(
        adapter="comfyui",
        payload={
            "workflow": _wf(ckpt_name="a.safetensors"),
            "timeout_s": 0.001,
            "poll_interval_s": 0.001,
        },
    )
    with pytest.raises(TimeoutError, match="did not complete"):
        await adapter.execute(job)
    assert not adapter._active_prompts


async def test_adapter_lifecycle_rejects_duplicate_start(adapter, test_config):
    with pytest.raises(RuntimeError, match="already started"):
        await adapter.start()
    fresh = ComfyUIAdapter(test_config, vram_manager=None)
    await fresh.stop()
    assert fresh._session is None


async def test_execute_rejects_workflow_missing_from_payload(adapter):
    job = make_job(adapter="comfyui", payload={})
    with pytest.raises(ValueError, match=r"workflow.*must be a dict"):
        await adapter.execute(job)
    assert not adapter._active_prompts


async def test_execute_rejects_non_object_submission_response(adapter, fake_comfy):
    _, server = fake_comfy
    # An empty error payload is not a validation error, but it lacks the id
    # required to track a submitted prompt.
    server.submit_response_override = {"number": 1}
    job = make_job(
        adapter="comfyui", payload={"workflow": _wf(ckpt_name="a.safetensors")}
    )
    with pytest.raises(RuntimeError, match="no prompt_id"):
        await adapter.execute(job)


async def test_submit_forwards_extra_data_and_rejects_non_object_json(
    adapter, fake_comfy
):
    _, server = fake_comfy
    job = make_job(
        adapter="comfyui",
        payload={"workflow": _wf(), "extra_data": {"source": "test"}},
    )
    await adapter.execute(job)
    assert server.prompts["prompt-1"]["extra_data"] == {"source": "test"}

    server.submit_response_override = ["not", "an", "object"]
    with pytest.raises(RuntimeError, match="non-object JSON"):
        await adapter.execute(make_job(adapter="comfyui", payload={"workflow": _wf()}))


async def test_poll_observes_cancellation_and_history_failures(adapter, fake_comfy):
    _, server = fake_comfy
    adapter._cancellation_requested.add("cancelled-prompt")
    with pytest.raises(asyncio.CancelledError):
        await adapter._poll_until_done(
            adapter._session,
            "cancelled-prompt",
            timeout=1,
            poll_interval=0,
            job=make_job(adapter="comfyui", payload={}),
        )

    server.history_status = 500
    assert await adapter._get_history_entry(adapter._session, "p") is None
    server.history_status = 200
    server.history_response_override = []
    assert await adapter._get_history_entry(adapter._session, "p") is None


def test_unexpected_terminal_status_fails_with_safe_default_message():
    with pytest.raises(RuntimeError, match=r"execution_error \(no detail\)"):
        ComfyUIAdapter._summarise_history(
            "p", {"status": {"status_str": "unknown", "messages": []}}
        )


# ---------------------------------------------------------------------------
# estimate_vram
# ---------------------------------------------------------------------------


async def test_estimate_uses_checkpoint_size(adapter, fake_comfy):
    _, server = fake_comfy
    server.metadata_size = 8 * 1024**3
    job = make_job(
        adapter="comfyui",
        payload={
            "workflow": _wf(ckpt_name="sd_xl_base.safetensors"),
        },
    )
    estimate = await adapter.estimate_vram(job)
    # 8 GiB checkpoint + 3 GiB overhead = ~11 GiB.
    assert 10 * 1024**3 < estimate < 13 * 1024**3


async def test_estimate_uses_fallback_for_unknown_checkpoint(adapter):
    job = make_job(
        adapter="comfyui",
        payload={
            "workflow": _wf(ckpt_name="nonexistent.safetensors"),
        },
    )
    estimate = await adapter.estimate_vram(job)
    # 7 GiB fallback + 3 GiB overhead = 10 GiB.
    assert estimate >= 10 * 1024**3


async def test_estimate_without_workflow_uses_overhead(adapter):
    job = make_job(adapter="comfyui", payload={})
    assert await adapter.estimate_vram(job) == adapter._inference_overhead_bytes


async def test_estimate_without_checkpoint_uses_overhead(adapter):
    job = make_job(adapter="comfyui", payload={"workflow": {"1": {"inputs": {}}}})
    assert await adapter.estimate_vram(job) == adapter._inference_overhead_bytes


async def test_estimate_skips_http_error_metadata_entries(adapter, fake_comfy):
    _, server = fake_comfy
    server.metadata_status = 500
    job = make_job(
        adapter="comfyui", payload={"workflow": _wf(ckpt_name="unknown.safetensors")}
    )
    assert await adapter.estimate_vram(job) == 10 * 1024**3


async def test_estimate_uses_overhead_for_non_dict_workflow(adapter):
    job = make_job(adapter="comfyui", payload={"workflow": []})
    assert await adapter.estimate_vram(job) == adapter._inference_overhead_bytes


async def test_estimate_uses_fallback_when_metadata_size_is_invalid(
    adapter, fake_comfy
):
    _, server = fake_comfy
    server.metadata_size = 0
    job = make_job(
        adapter="comfyui",
        payload={"workflow": _wf(ckpt_name="missing-size.safetensors")},
    )
    estimate = await adapter.estimate_vram(job)
    assert estimate == 10 * 1024**3


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------


async def test_cancel_running_interrupts(adapter, fake_comfy):
    _, server = fake_comfy
    server.auto_complete = False
    job = make_job(adapter="comfyui", payload={"workflow": _wf(ckpt_name="x")})
    # Submit (async), then cancel the running prompt.

    import asyncio as _asyncio

    exec_task = _asyncio.create_task(adapter.execute(job))
    await wait_until(lambda: "prompt-1" in server.prompts)
    server.queue_running = [[1, "prompt-1", {}, {}, []]]
    server.queue_pending = []

    await adapter.request_cancel(
        make_job(adapter="comfyui", payload={"prompt_id": "prompt-1"})
    )
    assert server.interrupt_calls == 1
    with pytest.raises(RuntimeError):
        await exec_task


async def test_cancel_pending_deletes(adapter, fake_comfy):
    _, server = fake_comfy
    server.queue_pending = [[1, "prompt-9", {}, {}, []]]
    await adapter.request_cancel(
        make_job(adapter="comfyui", payload={"prompt_id": "prompt-9"})
    )
    assert "prompt-9" in server.deleted_prompts
    assert server.interrupt_calls == 0


async def test_cancel_returns_false_for_http_errors(adapter, fake_comfy):
    _, server = fake_comfy
    server.queue_running = [[1, "running", {}, {}, []]]
    server.interrupt_status = 503
    assert (
        await adapter.request_cancel(
            make_job(adapter="comfyui", payload={"prompt_id": "running"})
        )
        is False
    )
    server.queue_running = []
    server.queue_pending = [[1, "pending", {}, {}, []]]
    server.queue_delete_status = 503
    assert (
        await adapter.request_cancel(
            make_job(adapter="comfyui", payload={"prompt_id": "pending"})
        )
        is False
    )
    assert not adapter._cancellation_requested


async def test_cancel_queue_request_failure_is_best_effort(adapter, monkeypatch):
    async def fail(_session):
        raise OSError("queue unavailable")

    monkeypatch.setattr(adapter, "_get_queue", fail)
    assert (
        await adapter.request_cancel(
            make_job(adapter="comfyui", payload={"prompt_id": "p"})
        )
        is False
    )
    assert not adapter._cancellation_requested


async def test_cancel_without_prompt_id_is_noop(adapter, fake_comfy):
    assert (
        await adapter.request_cancel(make_job(adapter="comfyui", payload={})) is False
    )
    _, server = fake_comfy
    assert server.interrupt_calls == 0
    assert server.deleted_prompts == []


async def test_cancel_unknown_prompt_is_noop(adapter):
    assert (
        await adapter.request_cancel(
            make_job(adapter="comfyui", payload={"prompt_id": "not-queued"})
        )
        is False
    )


async def test_unload_http_error_returns_zero(adapter, fake_comfy):
    _, server = fake_comfy
    server.free_status = 503
    assert await adapter.unload_idle_models(1024) == 0
    assert server.free_calls == 1


async def test_start_probe_failure_closes_session(fake_comfy, test_config):
    ts, server = fake_comfy
    server.system_stats_status = 503
    cfg = BananaBrainConfig(
        comfyui_base_url=str(ts.make_url("")).rstrip("/"),
        database_path=test_config.database_path,
    )
    instance = ComfyUIAdapter(cfg, vram_manager=None)
    with pytest.raises(RuntimeError, match="system_stats returned 503"):
        await instance.start()
    assert instance._session is None


async def test_stop_is_safe_before_start(test_config):
    instance = ComfyUIAdapter(test_config, vram_manager=None)
    await instance.stop()
    assert instance._session is None


# ---------------------------------------------------------------------------
# unload_idle_models
# ---------------------------------------------------------------------------


async def test_unload_calls_free_when_idle(adapter, fake_comfy):
    _, server = fake_comfy
    freed = await adapter.unload_idle_models(5 * 1024**3)
    assert freed == 5 * 1024**3
    assert server.free_calls == 1


async def test_unload_skipped_when_busy(adapter, fake_comfy):
    _, server = fake_comfy
    adapter._active_prompts.add("prompt-x")
    freed = await adapter.unload_idle_models(5 * 1024**3)
    assert freed == 0
    assert server.free_calls == 0


@pytest.mark.asyncio
async def test_remaining_comfyui_adapter_error_paths(  # noqa: C901,RUF100
    adapter, fake_comfy, test_config, monkeypatch
):
    import aiohttp

    from huey.banana_brain.comfyui_adapter import _safe_text

    _, server = fake_comfy
    server.submit_response_override = {
        "error": "invalid graph",
        "node_errors": {"4": {"errors": ["missing input"]}},
    }
    with pytest.raises(RuntimeError, match="invalid graph"):
        await adapter.execute(
            make_job(
                adapter="comfyui", payload={"workflow": {"4": {"class_type": "x"}}}
            )
        )

    def fail_post(*_args, **_kwargs):
        raise OSError("offline")

    monkeypatch.setattr(aiohttp.ClientSession, "post", fail_post)
    assert await adapter.unload_idle_models(1024) == 0
    monkeypatch.undo()

    class Response:
        def __init__(self, status=200, data=None, fail_text=False):
            self.status = status
            self.data = data
            self.fail_text = fail_text

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def json(self, **_kwargs):
            return self.data

        async def text(self):
            if self.fail_text:
                raise RuntimeError("unreadable")
            return "body"

    class Session:
        closed = False

        def __init__(self, status=200, data=None, error=None):
            self.status = status
            self.data = data
            self.error = error
            self.calls = []

        def get(self, url, **_kwargs):
            self.calls.append(url)
            if self.error:
                raise self.error
            return Response(self.status, self.data)

        def post(self, *_args, **_kwargs):
            if self.error:
                raise self.error
            return Response(self.status, self.data)

        async def close(self):
            self.closed = True

    await adapter._session.close()
    adapter._session = Session(status=404)
    assert await adapter._get_history_entry(adapter._session, "missing") is None
    assert await adapter._checkpoint_size_bytes("model.safetensors") is None
    assert len(adapter._session.calls) == 5
    assert await adapter._get_queue(adapter._session) == {}

    adapter._session = Session(status=500)
    assert await adapter._get_history_entry(adapter._session, "failed") is None
    assert await adapter._get_queue(adapter._session) == {}

    adapter._session = Session(error=OSError("offline"))
    assert await adapter._get_history_entry(adapter._session, "offline") is None
    assert await adapter._get_queue(adapter._session) == {}
    assert await adapter._checkpoint_size_bytes("model.safetensors") is None

    with pytest.raises(RuntimeError, match="session is not open"):
        ComfyUIAdapter(test_config, vram_manager=None)._require_session()
    assert await _safe_text(Response(fail_text=True)) == "<unreadable body>"
