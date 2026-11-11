"""
banana_brain.pygpt_adapter — PyGPT workload adapter.

Two integration modes, both routing through the scheduler:

  (A) HTTP front door (recommended for PyGPT desktop):
      An aiohttp server exposing /v1/chat/completions and
      /v1/completions. PyGPT is configured as an OpenAI-compatible
      custom provider with this endpoint as its API base. Each request
      becomes a Job (adapter="ollama") submitted via scheduler.submit(),
      awaited by polling job_store, and returned in OpenAI response
      format. Streaming requests are served as a single SSE chunk;
      true token-by-token streaming requires scheduler support for
      streaming jobs (P2).

  (B) Adapter-mode execute(job):
      Jobs submitted with adapter="pygpt" are translated to Ollama
      format and delegated to the configured OllamaAdapter. Useful for
      CLI submissions and tests that want to exercise the PyGPT path
      without starting the HTTP server.

Public API (called by the scheduler and composition root):

  async start()                                   -> None
  async stop()                                    -> None
  async execute(job)                              -> dict   (mode B)
  async estimate_vram(job)                        -> int    (mode B)
  async unload_idle_models(needed_bytes)          -> int    (mode B)
  async request_cancel(job)                       -> bool   (mode B)

Lifecycle:
  async start() opens the Ollama adapter session (if not shared), starts
  the HTTP server if pygpt_proxy_enabled is true, and registers the
  available models for /v1/models. async stop() drains in-flight HTTP
  requests (bounded by shutdown_grace_seconds), then stops the server.

Job payload schema (adapter="pygpt", mode B):

  model:       str   optional; resolved against loaded Ollama models.
  messages:    list  chat-format messages (mutually exclusive with prompt).
  prompt:      str   completion-format prompt.
  options:     dict  forwarded to Ollama's options.
  keep_alive:  str | int
  stream:      bool  if True, the adapter aggregates internally.

HTTP request schema (mode A), subset of OpenAI ChatCompletions:

  model: str, messages: [...], stream: bool, temperature: float,
  top_p: float, max_tokens: int, stop: str | [str], tools, ...

  Tool calling is passed through to Ollama when the model supports it
  (Ollama's "tools" field), but the result shape is best-effort.

Configuration fields consumed:

  pygpt_proxy_enabled: bool                (default False)
  pygpt_proxy_bind: str | None             (e.g. "127.0.0.1:8081")
  pygpt_proxy_socket_path: Path | None     (Unix socket alternative)
  pygpt_default_model: str | None          (fallback model name)
  pygpt_model_aliases: dict[str, str]      (PyGPT name -> Ollama name)
  pygpt_request_timeout_seconds: float     (default 600)
  pygpt_poll_interval_seconds: float       (default 0.35)
  ollama_base_url: str                     (delegated to OllamaAdapter)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import aiohttp
from aiohttp import web

from .job_models import Job, JobResult, JobState, Priority

__all__ = ["PyGPTAdapter"]

LOG = logging.getLogger("banana_brain.pygpt_adapter")

GIB = 1024 ** 3


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------

class PyGPTAdapter:
    """
    PyGPT front door and adapter-mode translator.

    The HTTP server runs in the same event loop as the scheduler; every
    incoming request submits a job and polls job_store for completion.
    In-flight requests are tracked so stop() can drain them cleanly.
    """

    DEFAULT_REQUEST_TIMEOUT_S = 600.0
    DEFAULT_POLL_INTERVAL_S = 0.35
    DEFAULT_PROXY_BIND = None  # Unix socket by default, per config default

    def __init__(
        self,
        config: Any,
        *,
        scheduler: Any,
        job_store: Any,
        ollama_adapter: Any,
    ) -> None:
        self._config = config
        self._scheduler = scheduler
        self._job_store = job_store
        self._ollama = ollama_adapter

        self._proxy_enabled = _cfg_bool(config, "pygpt_proxy_enabled", False)
        self._proxy_bind = _cfg_str(config, "pygpt_proxy_bind")
        self._proxy_socket = _cfg_str(config, "pygpt_proxy_socket_path")
        self._default_model = _cfg_str(config, "pygpt_default_model")
        self._model_aliases = _cfg_dict(config, "pygpt_model_aliases") or {}
        self._request_timeout = float(
            _cfg_num(
                config, "pygpt_request_timeout_seconds",
                self.DEFAULT_REQUEST_TIMEOUT_S,
            )
        )
        self._poll_interval = float(
            _cfg_num(
                config, "pygpt_poll_interval_seconds",
                self.DEFAULT_POLL_INTERVAL_S,
            )
        )

        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.BaseSite] = None
        self._app: Optional[web.Application] = None
        self._inflight: set[asyncio.Task[Any]] = set()
        self._inflight_lock = asyncio.Lock()
        self._stopping = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._proxy_enabled:
            await self._start_proxy()
        else:
            LOG.info(
                "pygpt_adapter ready in adapter mode only (pygpt_proxy_enabled=false)"
            )

    async def stop(self) -> None:
        self._stopping = True
        if self._runner is not None:
            # Drain in-flight HTTP tasks for a bounded time before closing
            # the listener, so PyGPT's in-progress generations are not
            # abruptly truncated.
            grace = float(
                _cfg_num(
                    self._config, "shutdown_grace_seconds", 30.0
                )
            )
            await self._drain_inflight(grace)
            await self._runner.cleanup()
            self._runner = None
            self._site = None
            self._app = None
        LOG.info("pygpt_adapter stopped")

    async def _start_proxy(self) -> None:
        if self._proxy_bind is None and self._proxy_socket is None:
            LOG.warning(
                "pygpt_proxy_enabled=true but neither pygpt_proxy_bind nor "
                "pygpt_proxy_socket_path is set; defaulting to %s",
                self._default_socket_path(),
            )
            self._proxy_socket = str(self._default_socket_path())

        self._app = web.Application()
        self._app.router.add_post(
            "/v1/chat/completions", self._handle_chat_completions
        )
        self._app.router.add_post("/v1/completions", self._handle_completions)
        self._app.router.add_get("/v1/models", self._handle_models)
        self._app.router.add_get("/health", self._handle_health)

        self._runner = web.AppRunner(self._app, access_log=LOG)
        await self._runner.setup()

        if self._proxy_socket:
            socket_path = Path(self._proxy_socket)
            socket_path.parent.mkdir(parents=True, exist_ok=True)
            if socket_path.exists():
                socket_path.unlink()
            self._site = web.UnixSite(
                self._runner, str(socket_path), shutdown_timeout=0.1
            )
            await self._site.start()
            try:
                socket_path.chmod(0o660)
            except OSError:
                LOG.debug("could not chmod pygpt proxy socket", exc_info=True)
            LOG.info("pygpt_adapter proxy listening on unix:%s", socket_path)
        else:
            host, port = _split_bind(self._proxy_bind)
            self._site = web.TCPSite(
                self._runner, host=host, port=port, shutdown_timeout=0.1
            )
            await self._site.start()
            LOG.info("pygpt_adapter proxy listening on http://%s:%d", host, port)

    async def _drain_inflight(self, grace: float) -> None:
        async with self._inflight_lock:
            tasks = list(self._inflight)
        if not tasks:
            return
        LOG.info("pygpt_adapter draining %d in-flight request(s)", len(tasks))
        done, pending = await asyncio.wait(tasks, timeout=grace)
        for task in pending:
            task.cancel()
        if pending:
            LOG.warning(
                "pygpt_adapter cancelled %d request(s) after %.0fs",
                len(pending), grace,
            )

    def _default_socket_path(self) -> Path:
        configured = _cfg_str(self._config, "api_socket_path")
        if configured:
            path = Path(configured)
            return path.with_name(path.name.replace(".sock", "-pygpt.sock"))
        return Path("data/banana-brain-pygpt.sock")

    # ------------------------------------------------------------------
    # Adapter-mode API (jobs submitted with adapter="pygpt")
    # ------------------------------------------------------------------

    async def execute(self, job: Job) -> dict[str, Any]:
        """
        Translate a pygpt job payload to Ollama format and delegate.

        This path is used when a caller submits a job with
        adapter="pygpt" directly to the scheduler. The HTTP front door
        does NOT use this method; it submits adapter="ollama" jobs so
        that PyGPT traffic is indistinguishable from any other Ollama
        traffic in the scheduler's queue.
        """
        model = await self._resolve_model(self._payload_str(job, "model"))
        payload = dict(job.payload or {})

        # The Ollama adapter expects either messages (chat) or prompt
        # (generate) at the top level of job.payload; PyGPT payloads
        # already use that shape, so we just stamp the resolved model.
        payload["model"] = model

        # A synthetic job carries the translated payload through the
        # Ollama adapter's own code path, avoiding a second copy of the
        # HTTP / validation / stream logic.
        synthetic = Job(
            adapter="ollama",
            payload=payload,
            id=f"{job.id}-ollama",
            priority=int(job.priority),
            owner=job.owner,
            idempotency_key=job.idempotency_key,
        )
        return await self._ollama.execute(synthetic)

    async def estimate_vram(self, job: Job) -> int:
        model = await self._resolve_model(self._payload_str(job, "model"))
        synthetic = Job(
            adapter="ollama",
            payload={"model": model},
            id=f"{job.id}-estimate",
        )
        return await self._ollama.estimate_vram(synthetic)

    async def unload_idle_models(self, needed_bytes: int) -> int:
        return await self._ollama.unload_idle_models(needed_bytes)

    async def request_cancel(self, job: Job) -> bool:
        synthetic = Job(
            adapter="ollama",
            payload={"model": self._payload_str(job, "model") or ""},
            id=f"{job.id}-cancel",
        )
        return await self._ollama.request_cancel(synthetic)

    # ------------------------------------------------------------------
    # HTTP handlers (mode A)
    # ------------------------------------------------------------------

    async def _handle_chat_completions(
        self, request: web.Request
    ) -> web.StreamResponse:
        try:
            body = await request.json()
        except Exception as exc:
            return _openai_error(400, f"invalid JSON body: {exc}")
        if not isinstance(body, dict):
            return _openai_error(400, "body must be a JSON object")

        return await self._serve_completion(
            request, body, kind="chat"
        )

    async def _handle_completions(
        self, request: web.Request
    ) -> web.StreamResponse:
        try:
            body = await request.json()
        except Exception as exc:
            return _openai_error(400, f"invalid JSON body: {exc}")
        if not isinstance(body, dict):
            return _openai_error(400, "body must be a JSON object")
        return await self._serve_completion(request, body, kind="completion")

    async def _handle_models(
        self, request: web.Request
    ) -> web.Response:
        """
        Advertise the models PyGPT may request.

        We prefer the currently loaded Ollama models because they are the
        ones we can serve without a cold load, and include any configured
        aliases so PyGPT's UI shows the names it expects.
        """
        loaded = []
        try:
            loaded = await self._ollama._list_loaded()  # noqa: SLF001
        except Exception:
            LOG.debug("could not list loaded models for /v1/models", exc_info=True)

        seen: set[str] = set()
        data: list[dict[str, Any]] = []
        for entry in loaded:
            name = str(entry.get("name") or entry.get("model") or "")
            if not name or name in seen:
                continue
            seen.add(name)
            data.append(
                {
                    "id": name,
                    "object": "model",
                    "created": 0,
                    "owned_by": "ollama",
                }
            )
        for alias in self._model_aliases:
            if alias not in seen:
                seen.add(alias)
                data.append(
                    {
                        "id": alias,
                        "object": "model",
                        "created": 0,
                        "owned_by": "ollama",
                    }
                )
        if not data and self._default_model:
            data.append(
                {
                    "id": self._default_model,
                    "object": "model",
                    "created": 0,
                    "owned_by": "ollama",
                }
            )
        return web.json_response({"object": "list", "data": data})

    async def _handle_health(self, request: web.Request) -> web.Response:
        return web.json_response(
            {"ok": True, "adapter": "pygpt", "shutting_down": self._stopping}
        )

    # ------------------------------------------------------------------
    # HTTP request -> job -> response
    # ------------------------------------------------------------------

    async def _serve_completion(
        self,
        request: web.Request,
        body: dict[str, Any],
        *,
        kind: str,
    ) -> web.StreamResponse:
        if self._stopping:
            return _openai_error(503, "Banana Brain is shutting down")

        try:
            model = await self._resolve_model(body.get("model"))
        except Exception as exc:
            return _openai_error(400, str(exc))

        stream = bool(body.get("stream", False))
        request_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"

        try:
            job = self._build_job(body, model=model, kind=kind)
        except ValueError as exc:
            return _openai_error(400, str(exc))

        task = asyncio.create_task(
            self._submit_and_await(job, request_id=request_id, stream=stream),
            name=f"pygpt-{request_id}",
        )
        async with self._inflight_lock:
            self._inflight.add(task)
        task.add_done_callback(self._forget_inflight)

        try:
            return await asyncio.wait_for(task, timeout=self._request_timeout)
        except asyncio.TimeoutError:
            LOG.warning(
                "pygpt request %s timed out after %.0fs (job %s)",
                request_id, self._request_timeout, job.id,
            )
            await self._best_effort_cancel(job.id)
            return _openai_error(504, "request timed out")
        except Exception as exc:
            LOG.exception("pygpt request %s failed", request_id)
            return _openai_error(500, f"{type(exc).__name__}: {exc}")

    def _forget_inflight(self, task: asyncio.Task[Any]) -> None:
        # Callback runs in the event loop; schedule removal as a task to
        # avoid awaiting inside the callback.
        async def _remove() -> None:
            async with self._inflight_lock:
                self._inflight.discard(task)

        asyncio.create_task(_remove())

    async def _submit_and_await(
        self,
        job: Job,
        *,
        request_id: str,
        stream: bool,
    ) -> web.StreamResponse:
        await self._scheduler.submit(job)
        result = await self._await_completion(job.id)

        if result.state is JobState.CANCELLED:
            return _openai_error(499, "request cancelled by operator")
        if result.state is JobState.FAILED:
            return _openai_error(
                502, result.last_error or "job failed in scheduler"
            )
        if result.state is not JobState.COMPLETED:
            return _openai_error(
                502, f"job ended in unexpected state {result.state.value}"
            )

        result_data = result.result
        if isinstance(result_data, JobResult):
            result_data = result_data.data
        if not isinstance(result_data, dict):
            return _openai_error(
                502,
                f"adapter returned unexpected result type: "
                f"{type(result_data).__name__}",
            )

        if stream:
            return _sse_single_chunk_response(
                request_id=request_id,
                model=job.payload.get("model", ""),
                result=result_data,
            )
        return web.json_response(
            _openai_chat_response(
                request_id=request_id,
                model=job.payload.get("model", ""),
                result=result_data,
            )
        )

    async def _await_completion(self, job_id: str) -> Job:
        deadline = time.monotonic() + self._request_timeout
        while True:
            job = await self._job_store.get(job_id)
            if job is None:
                raise RuntimeError(f"job {job_id} vanished from job_store")
            if job.state.is_terminal:
                return job
            if time.monotonic() > deadline:
                raise TimeoutError(f"job {job_id} did not finish in time")
            await asyncio.sleep(self._poll_interval)

    async def _best_effort_cancel(self, job_id: str) -> None:
        try:
            await self._scheduler.cancel(job_id, force=True)
        except Exception:
            LOG.exception("failed to cancel timed-out pygpt job %s", job_id)

    # ------------------------------------------------------------------
    # Request translation
    # ------------------------------------------------------------------

    def _build_job(
        self, body: dict[str, Any], *, model: str, kind: str
    ) -> Job:
        if kind == "chat":
            messages = body.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError("chat requests require a non-empty messages list")
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "stream": False,
            }
        else:
            prompt = body.get("prompt")
            if not isinstance(prompt, (str, list)):
                raise ValueError("completion requests require a prompt string")
            if isinstance(prompt, list):
                prompt = "\n".join(str(p) for p in prompt)
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
            }

        options = _openai_body_to_ollama_options(body)
        if options:
            payload["options"] = options
        if "stop" in body:
            payload.setdefault("options", {})["stop"] = body["stop"]
        if "tools" in body and body["tools"]:
            payload["tools"] = body["tools"]

        return Job(
            adapter="ollama",
            payload=payload,
            priority=int(Priority.INTERACTIVE),
            owner="pygpt",
            tags={"source": "pygpt", "kind": kind},
        )

    async def _resolve_model(self, requested: Any) -> str:
        """
        Map PyGPT's requested model to a loaded or configured Ollama model.

        Order of preference, matching the design doc's "preferably
        reusing Ollama's existing model":
          1. Explicit alias in pygpt_model_aliases.
          2. Exact match against a loaded model.
          3. The only loaded model, if exactly one is loaded.
          4. pygpt_default_model.
          5. Raise a clear error.
        """
        requested_str = str(requested).strip() if requested else ""

        if requested_str:
            alias_target = self._model_aliases.get(requested_str)
            if alias_target:
                return alias_target

        loaded = []
        try:
            loaded = await self._ollama._list_loaded()  # noqa: SLF001
        except Exception:
            LOG.exception("could not list loaded models during resolution")

        loaded_names = [
            str(entry.get("name") or entry.get("model") or "")
            for entry in loaded
        ]
        loaded_names = [n for n in loaded_names if n]

        if requested_str:
            for name in loaded_names:
                if name == requested_str or name.split(":", 1)[0] == requested_str:
                    return name

        if len(loaded_names) == 1:
            LOG.info(
                "pygpt model %r not loaded; reusing the only loaded model %r",
                requested_str or "<none>", loaded_names[0],
            )
            return loaded_names[0]

        if self._default_model:
            LOG.info(
                "pygpt model %r not loaded; using pygpt_default_model %r",
                requested_str or "<none>", self._default_model,
            )
            return self._default_model

        raise ValueError(
            f"no Ollama model available for PyGPT request "
            f"(requested={requested_str!r}, loaded={loaded_names!r}); "
            f"set pygpt_default_model or pygpt_model_aliases in config"
        )

    @staticmethod
    def _payload_str(job: Job, key: str) -> Optional[str]:
        value = (job.payload or {}).get(key)
        return str(value) if value else None


# ---------------------------------------------------------------------------
# OpenAI-compatible response shaping
# ---------------------------------------------------------------------------

def _openai_chat_response(
    *, request_id: str, model: str, result: dict[str, Any]
) -> dict[str, Any]:
    content = _extract_text(result)
    message: dict[str, Any] = {"role": "assistant", "content": content}
    tool_calls = result.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        message["tool_calls"] = tool_calls
    return {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model or result.get("model", ""),
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": result.get("done_reason") or "stop",
            }
        ],
        "usage": _usage_from_result(result),
    }


def _sse_single_chunk_response(
    *, request_id: str, model: str, result: dict[str, Any]
) -> web.StreamResponse:
    """
    Emit one SSE event containing the full content, then [DONE].

    True per-token streaming requires scheduler support for streaming
    jobs; the scheduler's execute() is terminal, so token-level delivery
    is not possible without a contract change. This shape keeps PyGPT's
    OpenAI SDK happy when it asks for stream=true.
    """
    content = _extract_text(result)
    chunk = {
        "id": request_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model or result.get("model", ""),
        "choices": [
            {
                "index": 0,
                "delta": {"role": "assistant", "content": content},
                "finish_reason": result.get("done_reason") or "stop",
            }
        ],
    }
    body = (
        f"data: {json.dumps(chunk)}\n\n"
        f"data: [DONE]\n\n"
    )
    return web.Response(
        body=body,
        content_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _extract_text(result: dict[str, Any]) -> str:
    if isinstance(result.get("message"), dict):
        content = result["message"].get("content")
        if isinstance(content, str):
            return content
    if isinstance(result.get("response"), str):
        return result["response"]
    return ""


def _usage_from_result(result: dict[str, Any]) -> dict[str, int]:
    eval_count = result.get("eval_count")
    prompt_eval = result.get("prompt_eval_count")
    try:
        completion_tokens = int(eval_count) if eval_count is not None else 0
    except (TypeError, ValueError):
        completion_tokens = 0
    try:
        prompt_tokens = int(prompt_eval) if prompt_eval is not None else 0
    except (TypeError, ValueError):
        prompt_tokens = 0
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def _openai_body_to_ollama_options(body: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "temperature": "temperature",
        "top_p": "top_p",
        "max_tokens": "num_predict",
        "max_completion_tokens": "num_predict",
        "frequency_penalty": "frequency_penalty",
        "presence_penalty": "presence_penalty",
        "seed": "seed",
    }
    options: dict[str, Any] = {}
    for openai_key, ollama_key in mapping.items():
        if openai_key in body and body[openai_key] is not None:
            options[ollama_key] = body[openai_key]
    return options


def _openai_error(status: int, message: str) -> web.Response:
    return web.json_response(
        {
            "error": {
                "message": message,
                "type": _error_type_for(status),
                "code": status,
            }
        },
        status=status,
    )


def _error_type_for(status: int) -> str:
    if status == 400:
        return "invalid_request_error"
    if status == 401:
        return "authentication_error"
    if status == 404:
        return "not_found_error"
    if status == 429:
        return "rate_limit_error"
    if status == 499:
        return "cancelled"
    if status >= 500:
        return "server_error"
    return "api_error"


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _split_bind(bind: str) -> tuple[str, int]:
    host, _, port = bind.rpartition(":")
    return host or "127.0.0.1", int(port)


# ---------------------------------------------------------------------------
# Config helpers (tolerant of dataclass, mapping, or attribute access)
# ---------------------------------------------------------------------------

def _cfg_get(config: Any, name: str) -> Any:
    if isinstance(config, dict):
        return config.get(name)
    return getattr(config, name, None)


def _cfg_str(config: Any, name: str) -> Optional[str]:
    value = _cfg_get(config, name)
    return str(value) if value else None


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


def _cfg_dict(config: Any, name: str) -> Optional[dict[str, Any]]:
    value = _cfg_get(config, name)
    return dict(value) if isinstance(value, dict) else None