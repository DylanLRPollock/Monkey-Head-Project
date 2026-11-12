"""
banana_brain.comfyui_adapter — ComfyUI workload adapter.

Responsibilities (from the Banana Brain design doc):
  * Submit image-generation workflows to a running ComfyUI server.
  * Track execution via /history/{prompt_id} until completion or failure.
  * Cooperatively unload models via /free so the scheduler can make room
    for Ollama or other workloads.
  * Report a pessimistic VRAM estimate per workflow.

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

  workflow:        dict   required. The ComfyUI API-format workflow graph.
  prompt_id:       str    if resuming a previously-submitted prompt, poll
                          this id instead of submitting a new workflow.
  client_id:       str    forwarded to ComfyUI as "client_id"; defaults to
                          a fresh uuid4 per execution.
  extra_data:      dict   forwarded to ComfyUI as "extra_data".
  poll_interval_s: float  overrides the adapter's default poll interval.
  timeout_s:       float  overrides the adapter's default per-job timeout.

Result shape (returned by execute and stored as job.result):

  {
    "prompt_id": "...",
    "status": "success" | "error" | "cancelled",
    "outputs": {...},           # from history outputs
    "status_messages": [...],   # from history status.messages
    "http_status": 200,
    "elapsed_s": 12.34,
  }

Dependency:
  aiohttp (async HTTP client, no extra C deps)
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any

import aiohttp

from .job_models import Job

__all__ = ["ComfyUIAdapter"]

LOG = logging.getLogger("banana_brain.comfyui_adapter")

GIB = 1024**3

#: Default overhead applied on top of checkpoint weights. ComfyUI's own
#: VRAM estimator node documents ~2 GiB for VAE, text encoder and a small
#: activation buffer for SD/SDXL-class models, scaled by resolution.
#: We use 3 GiB as a floor because ComfyUI's execution graph may hold more
#: than one model simultaneously (e.g. SDXL base + refiner + VAE).
DEFAULT_INFERENCE_OVERHEAD_GIB = 3.0

#: Bytes per parameter by typical inference dtype.
_DTYPE_BYTES_PER_PARAM: dict[str, float] = {
    "fp16": 2.0,
    "bf16": 2.0,
    "fp32": 4.0,
    "fp8": 1.0,
}


class ComfyUIAdapter:
    """
    Adapter for one ComfyUI server.

    Thread-safe with respect to the scheduler because the scheduler calls
    all methods from the same event loop. Active prompt ids are tracked in
    a set so cancellation and concurrent-execution guards can consult them.
    """

    DEFAULT_BASE_URL = "http://127.0.0.1:8188"
    DEFAULT_POLL_INTERVAL_S = 0.75
    DEFAULT_JOB_TIMEOUT_S = 900.0  # 15 minutes
    DEFAULT_CONNECT_TIMEOUT_S = 10.0
    UNLOAD_TIMEOUT_S = 20.0
    METADATA_TIMEOUT_S = 5.0

    def __init__(self, config: Any, vram_manager: Any) -> None:
        self._config = config
        self._vram_manager = vram_manager

        self._base_url = str(
            _cfg_str(config, "comfyui_base_url", "comfyui_url") or self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._poll_interval = float(
            _cfg_num(
                config,
                "comfyui_poll_interval_seconds",
                self.DEFAULT_POLL_INTERVAL_S,
            )
        )
        self._job_timeout = float(
            _cfg_num(
                config,
                "comfyui_job_timeout_seconds",
                self.DEFAULT_JOB_TIMEOUT_S,
            )
        )
        self._connect_timeout = float(
            _cfg_num(
                config,
                "comfyui_connect_timeout_seconds",
                self.DEFAULT_CONNECT_TIMEOUT_S,
            )
        )
        self._inference_overhead_bytes = int(
            _cfg_num(
                config,
                "comfyui_inference_overhead_gib",
                DEFAULT_INFERENCE_OVERHEAD_GIB,
            )
            * GIB
        )

        self._session: aiohttp.ClientSession | None = None
        self._active_prompts: set[str] = set()
        self._active_lock = asyncio.Lock()
        self._cancellation_requested: set[str] = set()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._session is not None:
            raise RuntimeError("comfyui_adapter already started")
        timeout = aiohttp.ClientTimeout(
            total=self._job_timeout,
            connect=self._connect_timeout,
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
            "comfyui_adapter ready at %s (poll=%.2fs, overhead=%.1f GiB)",
            self._base_url,
            self._poll_interval,
            self._inference_overhead_bytes / GIB,
        )

    async def stop(self) -> None:
        session = self._session
        self._session = None
        if session is not None:
            await session.close()
        async with self._active_lock:
            self._active_prompts.clear()
        LOG.info("comfyui_adapter stopped")

    # ------------------------------------------------------------------
    # Scheduler-facing API
    # ------------------------------------------------------------------

    async def execute(self, job: Job) -> dict[str, Any]:
        """
        Submit a workflow (or resume a known prompt_id) and poll until the
        prompt reaches a terminal state.

        Returns the summarised history entry. Raises on transport errors,
        HTTP errors, or a history entry that reports an execution error.
        """
        session = self._require_session()
        started = time.monotonic()

        prompt_id = self._payload_str(job, "prompt_id")
        if prompt_id:
            LOG.info("comfyui: resuming prompt_id %s for job %s", prompt_id, job.id)
        else:
            prompt_id = await self._submit_workflow(session, job)

        async with self._active_lock:
            self._active_prompts.add(prompt_id)

        try:
            timeout = float((job.payload or {}).get("timeout_s") or self._job_timeout)
            poll_interval = float(
                (job.payload or {}).get("poll_interval_s") or self._poll_interval
            )
            history_entry = await self._poll_until_done(
                session,
                prompt_id,
                timeout=timeout,
                poll_interval=poll_interval,
                job=job,
            )
            result = self._summarise_history(prompt_id, history_entry)
            result["elapsed_s"] = round(time.monotonic() - started, 3)
            return result
        finally:
            async with self._active_lock:
                self._active_prompts.discard(prompt_id)

    async def estimate_vram(self, job: Job) -> int:
        """
        Estimate peak VRAM for the workflow in `job.payload["workflow"]`.

        ComfyUI has no endpoint that reports the VRAM cost of a workflow,
        so this method:

          1. Extracts checkpoint filenames from the workflow graph.
          2. Queries /object_info or /view_metadata for each checkpoint's
             file size, when available.
          3. Applies the configured inference overhead.

        The estimate is a floor. It does not model batch size, attention
        implementation, LoRA stacks, or ComfyUI's dynamic offloading.
        """
        workflow = (job.payload or {}).get("workflow")
        if not isinstance(workflow, dict):
            LOG.warning(
                "comfyui estimate_vram: no workflow in payload; "
                "using overhead only for job %s",
                job.id,
            )
            return self._inference_overhead_bytes

        checkpoint_names = _extract_checkpoint_names(workflow)
        if not checkpoint_names:
            LOG.warning(
                "comfyui estimate_vram: no checkpoints found in workflow "
                "for job %s; using overhead only",
                job.id,
            )
            return self._inference_overhead_bytes

        total_weights = 0
        for name in checkpoint_names:
            size = await self._checkpoint_size_bytes(name)
            if size:
                total_weights += size
            else:
                LOG.warning(
                    "comfyui estimate_vram: unknown size for checkpoint %r; "
                    "using 7 GiB fallback",
                    name,
                )
                total_weights += int(7 * GIB)

        estimate = total_weights + self._inference_overhead_bytes
        LOG.debug(
            "comfyui estimate_vram(%s): %d checkpoints, weights=%d, "
            "overhead=%d, total=%d",
            job.id,
            len(checkpoint_names),
            total_weights,
            self._inference_overhead_bytes,
            estimate,
        )
        return max(estimate, 1 * GIB)

    async def unload_idle_models(self, needed_bytes: int) -> int:
        """
        Unload ComfyUI's models via POST /free.

        ComfyUI does not report which models are loaded or how much VRAM
        each occupies, so the adapter cannot selectively unload. It calls
        /free unconditionally when no prompt is active, and returns
        `needed_bytes` as an optimistic "likely freed" count so the
        scheduler proceeds to re-read gpu_monitor for the truth.

        If a prompt is currently active, returns 0 without touching
        ComfyUI — unloading mid-execution would corrupt the run.
        """
        session = self._require_session()
        async with self._active_lock:
            if self._active_prompts:
                LOG.info(
                    "comfyui unload_idle_models: %d prompt(s) active; skipping",
                    len(self._active_prompts),
                )
                return 0

        try:
            async with session.post(
                f"{self._base_url}/free",
                json={"unload_models": True, "free_memory": True},
                timeout=aiohttp.ClientTimeout(total=self.UNLOAD_TIMEOUT_S),
            ) as resp:
                if resp.status >= 400:
                    body = await _safe_text(resp)
                    LOG.warning(
                        "comfyui /free returned %d: %s",
                        resp.status,
                        body[:200],
                    )
                    return 0
                await resp.read()
        except Exception:
            LOG.exception("comfyui /free request failed")
            return 0

        LOG.info(
            "comfyui /free requested (unload_models=true, free_memory=true); "
            "claiming up to %d bytes freed",
            needed_bytes,
        )
        return needed_bytes

    async def request_cancel(self, job: Job) -> bool:
        """
        Best-effort cancellation via POST /interrupt.

        ComfyUI's /interrupt stops the currently running workflow, not a
        specific prompt_id. If the job's prompt_id is the one running, the
        interrupt is effective; if the queue is running something else, it
        is not. The adapter verifies via /queue whether this job's prompt
        is running before interrupting, and if the prompt is still pending,
        removes it from the queue instead.

        Returns True if an interrupt or queue removal was issued.
        """
        session = self._require_session()
        prompt_id = self._payload_str(job, "prompt_id")
        if not prompt_id:
            LOG.warning(
                "comfyui request_cancel: job %s has no prompt_id; " "nothing to target",
                job.id,
            )
            return False

        self._cancellation_requested.add(prompt_id)
        try:
            queue = await self._get_queue(session)
            running_ids = _extract_prompt_ids(queue.get("queue_running"))
            pending_ids = _extract_prompt_ids(queue.get("queue_pending"))

            if prompt_id in running_ids:
                LOG.info(
                    "comfyui: interrupting running prompt %s for job %s",
                    prompt_id,
                    job.id,
                )
                async with session.post(
                    f"{self._base_url}/interrupt",
                    json={},
                    timeout=aiohttp.ClientTimeout(total=5.0),
                ) as resp:
                    if resp.status >= 400:
                        LOG.warning("comfyui /interrupt returned %d", resp.status)
                        return False
                    await resp.read()
                return True

            if prompt_id in pending_ids:
                LOG.info(
                    "comfyui: deleting pending prompt %s for job %s",
                    prompt_id,
                    job.id,
                )
                async with session.post(
                    f"{self._base_url}/queue",
                    json={"delete": [prompt_id]},
                    timeout=aiohttp.ClientTimeout(total=5.0),
                ) as resp:
                    if resp.status >= 400:
                        LOG.warning("comfyui /queue delete returned %d", resp.status)
                        return False
                    await resp.read()
                return True

            LOG.info(
                "comfyui: prompt %s not found in queue (already finished?)",
                prompt_id,
            )
            return False
        except Exception:
            LOG.exception("comfyui cancellation failed for job %s", job.id)
            return False
        finally:
            self._cancellation_requested.discard(prompt_id)

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    async def _submit_workflow(self, session: aiohttp.ClientSession, job: Job) -> str:
        payload = job.payload or {}
        workflow = payload.get("workflow")
        if not isinstance(workflow, dict):
            raise ValueError(
                "job.payload['workflow'] must be a dict (ComfyUI API format)"
            )

        body: dict[str, Any] = {
            "prompt": workflow,
            "client_id": self._payload_str(job, "client_id") or str(uuid.uuid4()),
        }
        if isinstance(payload.get("extra_data"), dict):
            body["extra_data"] = dict(payload["extra_data"])

        async with session.post(
            f"{self._base_url}/prompt",
            json=body,
            timeout=aiohttp.ClientTimeout(total=30.0),
        ) as resp:
            if resp.status >= 400:
                text = await _safe_text(resp)
                raise RuntimeError(
                    f"comfyui /prompt returned {resp.status}: {text[:1000]}"
                )
            data = await resp.json(content_type=None)

        if not isinstance(data, dict):
            raise RuntimeError(
                f"comfyui /prompt returned non-object JSON: {type(data)}"
            )
        if data.get("error"):
            node_errors = data.get("node_errors") or {}
            raise RuntimeError(
                f"comfyui workflow validation failed: {data['error']} "
                f"node_errors={json.dumps(node_errors)[:1000]}"
            )
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"comfyui /prompt returned no prompt_id: {data!r}")
        LOG.info(
            "comfyui submitted job %s as prompt_id %s (queue position %s)",
            job.id,
            prompt_id,
            data.get("number"),
        )
        return str(prompt_id)

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    async def _poll_until_done(
        self,
        session: aiohttp.ClientSession,
        prompt_id: str,
        *,
        timeout: float,
        poll_interval: float,
        job: Job,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while True:
            if prompt_id in self._cancellation_requested:
                raise asyncio.CancelledError(
                    f"comfyui prompt {prompt_id} cancelled by operator"
                )
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"comfyui prompt {prompt_id} did not complete within "
                    f"{timeout:.0f}s"
                )

            history_entry = await self._get_history_entry(session, prompt_id)
            if history_entry is not None:
                status = history_entry.get("status") or {}
                if _history_is_terminal(status):
                    return history_entry

            await asyncio.sleep(poll_interval)

    async def _get_history_entry(
        self, session: aiohttp.ClientSession, prompt_id: str
    ) -> dict[str, Any] | None:
        try:
            async with session.get(
                f"{self._base_url}/history/{prompt_id}",
                timeout=aiohttp.ClientTimeout(total=10.0),
            ) as resp:
                if resp.status == 404:
                    return None
                if resp.status >= 400:
                    LOG.warning(
                        "comfyui /history/%s returned %d",
                        prompt_id,
                        resp.status,
                    )
                    return None
                data = await resp.json(content_type=None)
        except Exception:
            LOG.exception("comfyui /history/%s request failed", prompt_id)
            return None
        if not isinstance(data, dict):
            return None
        entry = data.get(prompt_id)
        return entry if isinstance(entry, dict) else None

    async def _get_queue(self, session: aiohttp.ClientSession) -> dict[str, Any]:
        try:
            async with session.get(
                f"{self._base_url}/queue",
                timeout=aiohttp.ClientTimeout(total=5.0),
            ) as resp:
                if resp.status >= 400:
                    return {}
                data = await resp.json(content_type=None)
        except Exception:
            LOG.exception("comfyui /queue request failed")
            return {}
        return data if isinstance(data, dict) else {}

    # ------------------------------------------------------------------
    # Result shaping
    # ------------------------------------------------------------------

    @staticmethod
    def _summarise_history(prompt_id: str, entry: dict[str, Any]) -> dict[str, Any]:
        status = entry.get("status") or {}
        status_str = str(status.get("status_str") or "").lower()
        messages = status.get("messages") or []

        if status_str == "success":
            state = "success"
        elif status_str == "error":
            state = "error"
        else:
            # Any other terminal value: treat as error to be safe.
            state = "error"

        summary = {
            "prompt_id": prompt_id,
            "status": state,
            "outputs": entry.get("outputs") or {},
            "status_messages": messages,
            "http_status": 200,
        }

        if state == "error":
            error_detail = _extract_error_message(messages)
            raise RuntimeError(f"comfyui prompt {prompt_id} failed: {error_detail}")
        return summary

    # ------------------------------------------------------------------
    # VRAM estimation helpers
    # ------------------------------------------------------------------

    async def _checkpoint_size_bytes(self, name: str) -> int | None:
        """
        Ask ComfyUI for a checkpoint's file size.

        /view_metadata/{folder_name} is the canonical route; when it does
        not have the file, fall back to /object_info to see whether any
        node exposes a size for the checkpoint. Returns None if the size
        cannot be determined — the caller applies its own fallback.
        """
        session = self._require_session()
        for folder in ("checkpoints", "unet", "diffusion_models", "loras"):
            try:
                async with session.get(
                    f"{self._base_url}/view_metadata/{folder}",
                    params={"filename": name},
                    timeout=aiohttp.ClientTimeout(total=self.METADATA_TIMEOUT_S),
                ) as resp:
                    if resp.status == 404:
                        continue
                    if resp.status >= 400:
                        continue
                    data = await resp.json(content_type=None)
            except Exception:
                continue
            size = _extract_size_from_metadata(data)
            if size:
                return size
        return None

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    def _require_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("comfyui_adapter session is not open")
        return self._session

    @staticmethod
    def _payload_str(job: Job, key: str) -> str | None:
        value = (job.payload or {}).get(key)
        return str(value) if value else None

    async def _probe(self) -> None:
        session = self._require_session()
        async with session.get(
            f"{self._base_url}/system_stats",
            timeout=aiohttp.ClientTimeout(total=5.0),
        ) as resp:
            if resp.status >= 400:
                raise RuntimeError(
                    f"comfyui /system_stats returned {resp.status}: "
                    f"{(await _safe_text(resp))[:200]}"
                )


# ---------------------------------------------------------------------------
# Workflow and history helpers
# ---------------------------------------------------------------------------


def _extract_checkpoint_names(workflow: dict[str, Any]) -> list[str]:
    """
    Walk the ComfyUI API-format workflow graph and collect checkpoint,
    UNet, diffusion-model and LoRA filenames from node inputs.

    ComfyUI workflows are a dict of node_id -> {"class_type": str,
    "inputs": {...}}. Checkpoint filenames appear as string values under
    keys like "ckpt_name", "unet_name", "lora_name".
    """
    names: list[str] = []
    seen: set[str] = set()
    for node in workflow.values():
        if not isinstance(node, dict):
            continue
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue
        for key in (
            "ckpt_name",
            "unet_name",
            "diffusion_model_name",
            "lora_name",
            "vae_name",
        ):
            value = inputs.get(key)
            if isinstance(value, str) and value and value not in seen:
                seen.add(value)
                names.append(value)
    return names


def _extract_size_from_metadata(data: Any) -> int | None:
    """Best-effort size extraction from varied metadata shapes."""
    if not isinstance(data, dict):
        return None
    for key in ("size", "file_size", "bytes", "size_bytes"):
        value = data.get(key)
        if isinstance(value, (int, float)) and value > 0:
            return int(value)
    # Some ComfyUI versions nest metadata under "metadata".
    nested = data.get("metadata")
    if isinstance(nested, dict):
        return _extract_size_from_metadata(nested)
    return None


def _extract_prompt_ids(entries: Any) -> set[str]:
    """
    ComfyUI's /queue response is a list of [number, prompt_id, prompt,
    extra_data, outputs_to_execute] arrays. Extract the prompt_id.
    """
    if not isinstance(entries, list):
        return set()
    ids: set[str] = set()
    for entry in entries:
        if isinstance(entry, list) and len(entry) >= 2:
            ids.add(str(entry[1]))
    return ids


def _history_is_terminal(status: dict[str, Any]) -> bool:
    status_str = str(status.get("status_str") or "").lower()
    return status_str in {"success", "error"}


def _extract_error_message(messages: Any) -> str:
    if not isinstance(messages, list):
        return "unknown error"
    for msg in messages:
        if isinstance(msg, list) and len(msg) == 2:
            kind, detail = msg
            if kind == "execution_error" and isinstance(detail, dict):
                return str(detail.get("exception_message") or "") or str(
                    detail.get("exception_type") or "execution_error"
                )
    return "execution_error (no detail)"


async def _safe_text(resp: aiohttp.ClientResponse) -> str:
    try:
        return await resp.text()
    except Exception:
        return "<unreadable body>"


# ---------------------------------------------------------------------------
# Config helpers (tolerant of dataclass, mapping, or attribute access)
# ---------------------------------------------------------------------------


def _cfg_get(config: Any, name: str) -> Any:
    if isinstance(config, dict):
        return config.get(name)
    return getattr(config, name, None)


def _cfg_str(config: Any, name: str, *fallback_names: str) -> str | None:
    for candidate in (name, *fallback_names):
        value = _cfg_get(config, candidate)
        if value:
            return str(value)
    return None


def _cfg_num(config: Any, name: str, default: float) -> float:
    value = _cfg_get(config, name)
    return float(value) if isinstance(value, (int, float)) else default
