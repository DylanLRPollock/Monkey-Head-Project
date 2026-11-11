"""
banana_brain.ollama_adapter — Ollama workload adapter.

Responsibilities (from the Banana Brain design doc):
  * Submit generation requests to a running Ollama server.
  * Detect which models are currently loaded via /api/ps.
  * Cooperatively unload idle models via /api/generate with keep_alive=0
    so the scheduler can make room for ComfyUI or other workloads.
  * Report a VRAM estimate per job, preferring measured size_vram from
    /api/ps over a heuristic when the model is already loaded.

Public API (called by the scheduler):

  async start()                                   -> None
  async stop()                                    -> None
  async execute(job)                              -> dict
  async estimate_vram(job)                        -> int
  async unload_idle_models(needed_bytes)          -> int  (bytes freed)
  async request_cancel(job)                       -> bool (best-effort)

Lifecycle:
  async start() / async stop()

Job payload schema (job.payload), all optional unless noted:

  model:       str   required. Ollama model tag, e.g. "qwen2.5:32b".
  prompt:      str   for /api/generate
  messages:    list  for /api/chat (mutually exclusive with prompt)
  system:      str   optional system prompt (generate only)
  template:    str   optional template override (generate only)
  format:      str   "json" to force JSON output
  options:     dict  forwarded to Ollama's "options" (temperature, num_ctx,
                     num_gpu, num_predict, ...)
  keep_alive:  str | int  overrides the adapter's default_keep_alive
  stream:      bool  if True, the adapter consumes the stream internally
                     and returns the aggregated response. Default False.
  timeout_s:   float overrides the per-request timeout.

Result shape (returned by execute and stored as job.result):

  {
    "model": "...",
    "response": "...",          # generate: full text
    "message": {...},           # chat: final message object
    "done": true,
    "done_reason": "...",
    "eval_count": int,
    "eval_duration_ns": int,
    "load_duration_ns": int,
    "total_duration_ns": int,
    "http_status": 200,
  }

Dependency:
  aiohttp (async HTTP client, no extra C deps)
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any, Optional

import aiohttp

from .job_models import Job, JobResult

__all__ = ["OllamaAdapter"]

LOG = logging.getLogger("banana_brain.ollama_adapter")

GIB = 1024 ** 3

#: Rough bytes-per-parameter by quantization level. Deliberately
#: pessimistic: overestimating costs a wait, underestimating costs an OOM.
_QUANT_BYTES_PER_PARAM: dict[str, float] = {
    "Q2_K": 0.36,
    "Q3_K_S": 0.45,
    "Q3_K_M": 0.48,
    "Q4_0": 0.56,
    "Q4_K_S": 0.56,
    "Q4_K_M": 0.60,
    "Q5_K_M": 0.70,
    "Q6_K": 0.82,
    "Q8_0": 1.06,
    "F16": 2.0,
    "FP16": 2.0,
    "F32": 4.0,
}
_DEFAULT_BYTES_PER_PARAM = 0.65  # between Q4_K_M and Q5_K_M

_PARAM_RE = re.compile(
    r"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>[BbMm])\b"
)


class OllamaAdapter:
    """
    Adapter for one Ollama server.

    Thread-safe with respect to the scheduler because the scheduler calls
    all methods from the same event loop; the internal `_active_models`
    set is guarded by an asyncio.Lock for clarity but is never awaited
    across long operations.
    """

    DEFAULT_BASE_URL = "http://127.0.0.1:11434"
    DEFAULT_KEEP_ALIVE = "5m"
    DEFAULT_REQUEST_TIMEOUT_S = 600.0
    DEFAULT_CONNECT_TIMEOUT_S = 10.0
    PS_TIMEOUT_S = 5.0
    UNLOAD_TIMEOUT_S = 15.0

    def __init__(self, config: Any, vram_manager: Any) -> None:
        self._config = config
        self._vram_manager = vram_manager  # accepted per the design's wiring

        self._base_url = str(
            _cfg_str(config, "ollama_base_url", "ollama_url")
            or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._default_keep_alive = _cfg_str(
            config, "ollama_keep_alive"
        ) or self.DEFAULT_KEEP_ALIVE
        self._default_timeout_s = float(
            _cfg_num(
                config, "ollama_request_timeout_seconds",
                self.DEFAULT_REQUEST_TIMEOUT_S,
            )
        )
        self._connect_timeout_s = float(
            _cfg_num(
                config, "ollama_connect_timeout_seconds",
                self.DEFAULT_CONNECT_TIMEOUT_S,
            )
        )
        self._unload_pinned = bool(_cfg_bool(config, "ollama_unload_pinned", False))
        self._unload_lru_first = bool(
            _cfg_bool(config, "ollama_unload_lru_first", True)
        )

        self._session: Optional[aiohttp.ClientSession] = None
        self._active_models: set[str] = set()
        self._active_lock = asyncio.Lock()
        self._cancellation_requested: set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._session is not None:
            raise RuntimeError("ollama_adapter already started")
        timeout = aiohttp.ClientTimeout(
            total=self._default_timeout_s,
            connect=self._connect_timeout_s,
        )
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers={"Accept": "application/json"},
            trust_env=False,
        )
        try:
            await self._probe()
        except Exception:
            await self._session.close()
            self._session = None
            raise
        LOG.info(
            "ollama_adapter ready at %s (keep_alive=%s)",
            self._base_url, self._default_keep_alive,
        )

    async def stop(self) -> None:
        session = self._session
        self._session = None
        if session is not None:
            await session.close()
        async with self._active_lock:
            self._active_models.clear()
        LOG.info("ollama_adapter stopped")

    # ------------------------------------------------------------------
    # Scheduler-facing API
    # ------------------------------------------------------------------

    async def execute(self, job: Job) -> dict[str, Any]:
        """
        Submit a generation or chat request to Ollama and return the result.

        Raises on HTTP / transport / Ollama-error; the scheduler catches
        and marks the job FAILED with the exception text in last_error.
        """
        session = self._require_session()
        model, endpoint, body = self._build_request(job)

        async with self._active_lock:
            self._active_models.add(model)

        started = time.monotonic()
        try:
            timeout = aiohttp.ClientTimeout(
                total=float(job.payload.get("timeout_s") or self._default_timeout_s),
                connect=self._connect_timeout_s,
            )
            async with session.post(
                f"{self._base_url}{endpoint}",
                json=body,
                timeout=timeout,
            ) as resp:
                if resp.status >= 400:
                    text = await _safe_text(resp)
                    raise RuntimeError(
                        f"ollama {endpoint} returned {resp.status}: {text[:500]}"
                    )

                stream = bool(body.get("stream", False))
                result = (
                    await self._consume_stream(resp, job)
                    if stream
                    else await self._consume_single(resp, job)
                )
                result["model"] = model
                result["http_status"] = resp.status
                result["elapsed_s"] = round(time.monotonic() - started, 3)
                return result
        finally:
            async with self._active_lock:
                self._active_models.discard(model)

    async def estimate_vram(self, job: Job) -> int:
        """
        Estimate peak VRAM for `job.payload["model"]`.

        Order of preference:
          1. If the model is loaded, use its measured size_vram.
          2. Otherwise, use parameter_size + quantization_level from the
             /api/show details to estimate pessimistically.
          3. Otherwise, use the adapter's conservative default.

        Always positive. Never returns None: the scheduler relies on a
        concrete value to reserve.
        """
        model = self._payload_str(job, "model")
        if not model:
            raise ValueError("job.payload['model'] is required")

        loaded = await self._list_loaded()
        entry = next((m for m in loaded if _model_matches(m, model)), None)
        if entry is not None:
            vram = int(entry.get("size_vram") or 0)
            if vram > 0:
                LOG.debug("estimate_vram(%s): measured %d", model, vram)
                return vram

        try:
            details = await self._show_details(model)
        except Exception:
            LOG.exception("ollama /api/show failed for %s", model)
            details = {}

        params = _parse_parameter_size(
            str(details.get("parameter_size") or "")
        )
        quant = str(details.get("quantization_level") or "").upper()
        bytes_per_param = _QUANT_BYTES_PER_PARAM.get(
            quant, _DEFAULT_BYTES_PER_PARAM
        )
        if params:
            estimate = int(params * 1_000_000_000 * bytes_per_param)
            # 25% overhead for KV cache, CUDA context, fragmentation.
            estimate = int(estimate * 1.25)
            LOG.debug(
                "estimate_vram(%s): %s params * %.2f B/param * 1.25 = %d",
                model, params, bytes_per_param, estimate,
            )
            return max(estimate, 1 * GIB)

        LOG.warning(
            "estimate_vram(%s): no parameter_size; using %d GiB default",
            model, 8,
        )
        return 8 * GIB

    async def unload_idle_models(self, needed_bytes: int) -> int:
        """
        Unload models that are not serving an active request, oldest
        `expires_at` first (or pinned models last, per config), until
        either `needed_bytes` have been released or no candidates remain.

        Returns the sum of size_vram for models we successfully unloaded.
        Never raises: failures are logged and counted as zero freed bytes.
        """
        session = self._require_session()
        loaded = await self._list_loaded()
        if not loaded:
            return 0

        async with self._active_lock:
            active = set(self._active_models)

        candidates = [m for m in loaded if _model_name(m) not in active]
        if not candidates:
            LOG.info(
                "unload_idle_models: no candidates (loaded=%d, all active)",
                len(loaded),
            )
            return 0

        candidates.sort(
            key=lambda m: _expires_sort_key(m),
            reverse=not self._unload_lru_first,
        )

        freed = 0
        for entry in candidates:
            if freed >= needed_bytes:
                break
            name = _model_name(entry)
            if not name:
                continue
            if _is_pinned(entry) and not self._unload_pinned:
                LOG.debug("unload_idle_models: skipping pinned model %s", name)
                continue
            size_vram = int(entry.get("size_vram") or 0)
            try:
                await self._unload_model(session, name)
                freed += size_vram
                LOG.info(
                    "unloaded model %s (%d bytes, freed total=%d/%d)",
                    name, size_vram, freed, needed_bytes,
                )
            except Exception:
                LOG.exception("failed to unload model %s", name)

        return freed

    async def request_cancel(self, job: Job) -> bool:
        """
        Best-effort cancellation. Ollama has no cancel endpoint for a
        running generation; we record the model in a cancellation set so
        a streaming consume loop can abort on the next chunk.

        Returns True if the request will be aborted at the next safe point.
        """
        model = self._payload_str(job, "model")
        if not model:
            return False
        self._cancellation_requested.add(model)
        LOG.info("cancellation requested for model %s (job %s)", model, job.id)
        return True

    # ------------------------------------------------------------------
    # HTTP internals
    # ------------------------------------------------------------------

    def _require_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("ollama_adapter session is not open")
        return self._session

    async def _probe(self) -> None:
        session = self._require_session()
        async with session.get(
            f"{self._base_url}/api/tags",
            timeout=aiohttp.ClientTimeout(total=self.PS_TIMEOUT_S),
        ) as resp:
            if resp.status >= 400:
                raise RuntimeError(
                    f"ollama /api/tags returned {resp.status}: "
                    f"{(await _safe_text(resp))[:200]}"
                )

    async def _list_loaded(self) -> list[dict[str, Any]]:
        session = self._require_session()
        try:
            async with session.get(
                f"{self._base_url}/api/ps",
                timeout=aiohttp.ClientTimeout(total=self.PS_TIMEOUT_S),
            ) as resp:
                if resp.status >= 400:
                    LOG.warning(
                        "ollama /api/ps returned %d: %s",
                        resp.status, (await _safe_text(resp))[:200],
                    )
                    return []
                data = await resp.json(content_type=None)
        except Exception:
            LOG.exception("ollama /api/ps request failed")
            return []
        models = data.get("models") if isinstance(data, dict) else None
        return models if isinstance(models, list) else []

    async def _show_details(self, model: str) -> dict[str, Any]:
        session = self._require_session()
        async with session.post(
            f"{self._base_url}/api/show",
            json={"model": model},
            timeout=aiohttp.ClientTimeout(total=self.PS_TIMEOUT_S),
        ) as resp:
            if resp.status >= 400:
                return {}
            data = await resp.json(content_type=None)
        details = data.get("details") if isinstance(data, dict) else None
        if isinstance(details, dict):
            return details
        # Some Ollama versions put the fields at the top level.
        return data if isinstance(data, dict) else {}

    async def _unload_model(
        self, session: aiohttp.ClientSession, model: str
    ) -> None:
        # Ollama documents /api/generate with an empty prompt and
        # keep_alive=0 as the unload signal. /api/chat with empty
        # messages and keep_alive=0 is equivalent.
        async with session.post(
            f"{self._base_url}/api/generate",
            json={"model": model, "prompt": "", "keep_alive": 0, "stream": False},
            timeout=aiohttp.ClientTimeout(total=self.UNLOAD_TIMEOUT_S),
        ) as resp:
            if resp.status >= 400:
                raise RuntimeError(
                    f"unload {model}: HTTP {resp.status} "
                    f"{(await _safe_text(resp))[:200]}"
                )
            await resp.read()

    # ------------------------------------------------------------------
    # Request construction
    # ------------------------------------------------------------------

    def _build_request(
        self, job: Job
    ) -> tuple[str, str, dict[str, Any]]:
        payload = job.payload or {}
        model = self._payload_str(job, "model")
        if not model:
            raise ValueError("job.payload['model'] is required")

        has_messages = isinstance(payload.get("messages"), list) and payload[
            "messages"
        ]
        has_prompt = isinstance(payload.get("prompt"), str) and payload["prompt"]

        if has_messages and has_prompt:
            raise ValueError(
                "job.payload must contain either 'messages' or 'prompt', not both"
            )
        if not has_messages and not has_prompt:
            raise ValueError(
                "job.payload must contain 'messages' (chat) or 'prompt' (generate)"
            )

        keep_alive = payload.get("keep_alive", self._default_keep_alive)
        body: dict[str, Any] = {
            "model": model,
            "keep_alive": keep_alive,
            "stream": bool(payload.get("stream", False)),
        }
        if isinstance(payload.get("options"), dict):
            body["options"] = dict(payload["options"])
        if isinstance(payload.get("format"), str):
            body["format"] = payload["format"]

        if has_messages:
            body["messages"] = list(payload["messages"])
            return model, "/api/chat", body

        body["prompt"] = payload["prompt"]
        if isinstance(payload.get("system"), str):
            body["system"] = payload["system"]
        if isinstance(payload.get("template"), str):
            body["template"] = payload["template"]
        return model, "/api/generate", body

    async def _consume_single(
        self, resp: aiohttp.ClientResponse, job: Job
    ) -> dict[str, Any]:
        data = await resp.json(content_type=None)
        if not isinstance(data, dict):
            raise RuntimeError(f"ollama returned non-object JSON: {type(data)}")
        if data.get("error"):
            raise RuntimeError(f"ollama error: {data['error']}")
        return _summarise_nonstream(data)

    async def _consume_stream(
        self, resp: aiohttp.ClientResponse, job: Job
    ) -> dict[str, Any]:
        model = self._payload_str(job, "model") or ""
        text_parts: list[str] = []
        final: dict[str, Any] = {}
        async for line in resp.content:
            if model and model in self._cancellation_requested:
                self._cancellation_requested.discard(model)
                raise asyncio.CancelledError(
                    f"streaming cancelled at next chunk (model {model})"
                )
            if not line:
                continue
            try:
                import json
                chunk = json.loads(line)
            except Exception:
                LOG.warning("ollama stream: dropping non-JSON line %r", line[:120])
                continue
            if isinstance(chunk, dict) and chunk.get("error"):
                raise RuntimeError(f"ollama stream error: {chunk['error']}")
            text_parts.append(str(chunk.get("response") or ""))
            if isinstance(chunk.get("message"), dict):
                text_parts.append(str(chunk["message"].get("content") or ""))
            if chunk.get("done"):
                final = chunk
                break

        result = _summarise_nonstream(final)
        result["response"] = "".join(text_parts)
        return result

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _payload_str(job: Job, key: str) -> Optional[str]:
        value = (job.payload or {}).get(key)
        return str(value) if value else None


# ---------------------------------------------------------------------------
# Result shaping
# ---------------------------------------------------------------------------

def _summarise_nonstream(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "response": str(data.get("response") or ""),
        "message": data.get("message") if isinstance(data.get("message"), dict) else None,
        "done": bool(data.get("done", True)),
        "done_reason": data.get("done_reason"),
        "eval_count": _int_or_none(data.get("eval_count")),
        "eval_duration_ns": _int_or_none(data.get("eval_duration")),
        "load_duration_ns": _int_or_none(data.get("load_duration")),
        "total_duration_ns": _int_or_none(data.get("total_duration")),
    }


def _int_or_none(value: Any) -> Optional[int]:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# /api/ps helpers
# ---------------------------------------------------------------------------

def _model_name(entry: dict[str, Any]) -> str:
    return str(entry.get("name") or entry.get("model") or "")


def _model_matches(entry: dict[str, Any], wanted: str) -> bool:
    names = {_model_name(entry), str(entry.get("model") or "")}
    wanted_norm = wanted.strip()
    if wanted_norm in names:
        return True
    # Ollama tags can be "qwen2.5:32b" or "qwen2.5" (default tag).
    if ":" not in wanted_norm:
        return any(n.split(":", 1)[0] == wanted_norm for n in names if n)
    return False


def _is_pinned(entry: dict[str, Any]) -> bool:
    expires = entry.get("expires_at")
    if not isinstance(expires, str) or not expires:
        return False
    # Ollama reports far-future timestamps for pinned models. Treat any
    # expiry more than one year out as "pinned".
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = (dt - datetime.now(tz=timezone.utc)).total_seconds()
        return delta > 365 * 24 * 3600
    except Exception:
        return False


def _expires_sort_key(entry: dict[str, Any]) -> float:
    """Sort so that soonest-expiring models come first (LRU-first)."""
    expires = entry.get("expires_at")
    if not isinstance(expires, str) or not expires:
        return float("inf")
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return float("inf")


def _parse_parameter_size(text: str) -> Optional[float]:
    if not text:
        return None
    match = _PARAM_RE.search(text)
    if not match:
        return None
    try:
        value = float(match.group("num"))
    except ValueError:
        return None
    unit = match.group("unit").lower()
    return value * (1.0 if unit == "b" else 0.001)


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _cfg_get(config: Any, name: str) -> Any:
    if isinstance(config, dict):
        return config.get(name)
    return getattr(config, name, None)


def _cfg_str(config: Any, name: str, *fallback_names: str) -> Optional[str]:
    for candidate in (name, *fallback_names):
        value = _cfg_get(config, candidate)
        if value:
            return str(value)
    return None


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


async def _safe_text(resp: aiohttp.ClientResponse) -> str:
    try:
        return await resp.text()
    except Exception:
        return "<unreadable body>"