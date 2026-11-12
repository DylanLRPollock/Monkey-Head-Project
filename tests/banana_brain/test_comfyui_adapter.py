"""Tests for huey.banana_brain.comfyui_adapter."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from huey.banana_brain.comfyui_adapter import (
    ComfyUIAdapter,
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
        return web.json_response({})

    async def _submit(self, request):
        if self.submit_errors:
            return web.json_response(self.submit_errors.pop(0), status=400)
        body = await request.json()
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
        for pid in body.get("delete") or []:
            self.deleted_prompts.append(pid)
            self.queue_pending = [e for e in self.queue_pending if e[1] != pid]
            self.history[pid] = {
                "status": {"status_str": "error", "messages": []},
            }
        return web.json_response({})

    async def _history(self, request):
        pid = request.match_info["prompt_id"]
        if pid not in self.history:
            return web.json_response({})
        return web.json_response({pid: self.history[pid]})

    async def _interrupt(self, request):
        self.interrupt_calls += 1
        for entry in self.queue_running:
            pid = entry[1]
            self.history[pid] = {
                "status": {"status_str": "error", "messages": []},
            }
        self.queue_running = []
        return web.json_response({})

    async def _free(self, request):
        self.free_calls += 1
        return web.json_response({})

    async def _metadata(self, request):
        return web.json_response({"size": self.metadata_size})


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


def test_extract_prompt_ids():
    queue = [[1, "pid-a", {}, {}, []], [2, "pid-b", {}, {}, []]]
    assert _extract_prompt_ids(queue) == {"pid-a", "pid-b"}


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
