"""
banana_brain.audio_adapter — audio workload adapter.

Responsibilities (from the Banana Brain design doc, §1 row 12):
  * Coordinate Whisper transcription, speech synthesis and other audio AI.
  * Submit requests to the configured STT and TTS backends.
  * Report a per-task VRAM estimate so the scheduler can admit honestly.
  * Cooperatively unload idle audio models via a configurable command,
    because none of the common backends expose a standard unload API.

Public API (called by the scheduler):

  async start()                                   -> None
  async stop()                                    -> None
  async execute(job)                              -> dict
  async estimate_vram(job)                        -> int
  async unload_idle_models(needed_bytes)          -> int  (bytes freed)
  async request_cancel(job)                       -> bool (best-effort)

Lifecycle:
  async start() / async stop()

Job payload schema (job.payload), common:

  task:  "transcribe" | "synthesize"     required.

Transcription task:

  audio_path:    str    path to a file readable by the STT backend.
  audio_url:     str    alternative to audio_path (multipart upload from
                        local disk still requires audio_path; audio_url is
                        fetched by the adapter and forwarded).
  language:      str    ISO-639-1 code, optional.
  model:         str    backend model name; defaults to audio_stt_default_model.
  response_format: str  "json" | "text" | "srt" | "vtt"; default "json".
  prompt:        str    optional decoder prompt (Whisper supports this).
  temperature:   float  optional.

Synthesis task:

  text:          str    required.
  voice:         str    backend voice id; defaults to audio_tts_default_voice.
  model:         str    backend model; defaults to audio_tts_default_model.
  output_path:   str    where to write audio (WAV/MP3 per backend).
  format:        str    "wav" | "mp3" | "ogg"; default "wav".
  speed:         float  optional speaking rate multiplier.

Result shape (returned by execute and stored as job.result):

  transcribe:
    {"task": "transcribe", "text": "...", "language": "en",
     "segments": [...], "backend": "faster-whisper-server",
     "http_status": 200, "elapsed_s": 4.2}

  synthesize:
    {"task": "synthesize", "output_path": "...", "bytes": 123456,
     "duration_s": 3.1, "backend": "coqui", "http_status": 200,
     "elapsed_s": 2.0}

Configuration fields consumed:

  audio_stt_backend:         "faster-whisper-server" | "whisper-cpp" | "disabled"
  audio_stt_base_url:        e.g. "http://127.0.0.1:8000"
  audio_stt_default_model:   e.g. "large-v3"
  audio_stt_timeout_seconds: default 900

  audio_tts_backend:         "coqui" | "piper" | "disabled"
  audio_tts_base_url:        e.g. "http://127.0.0.1:5002"
  audio_tts_default_model:   e.g. "xtts_v2"
  audio_tts_default_voice:   e.g. "Claribel Dervla"
  audio_tts_timeout_seconds: default 300

  audio_unload_command:      optional shell command to evict models,
                             e.g. "systemctl restart faster-whisper-server"
  audio_unload_wait_seconds: how long to wait after unload for VRAM to drop
  audio_model_vram_gib:      overrides for the built-in VRAM table

Dependency:
  aiohttp
"""

from __future__ import annotations

import asyncio
import logging
import shlex
import time
from pathlib import Path
from typing import Any, Optional

import aiohttp

from .job_models import Job, JobResult

__all__ = ["AudioAdapter"]

LOG = logging.getLogger("banana_brain.audio_adapter")

GIB = 1024 ** 3

#: VRAM estimates by backend and model, in GiB.
#:
#: faster-whisper INT8 figures from the project's own model guide:
#: large-v3-turbo ≈ 1.6 GB, large-v3 ≈ 3.0 GB, medium ≈ 1.5 GB,
#: small ≈ 0.5 GB. FP16 roughly doubles the INT8 numbers.
#: Coqui XTTS-v2 is ~3.4 GB at FP16 and ~2 GB at INT8; VITS is ~1.2 GB.
#: Piper's VITS ONNX voices are ~256 MB per the ComfyUI node's VRAM tier.
_STT_VRAM_GIB: dict[str, float] = {
    "large-v3": 3.0,
    "large-v3-turbo": 1.6,
    "turbo": 1.6,
    "medium": 1.5,
    "small": 0.5,
    "base": 0.3,
    "tiny": 0.2,
}
_TTS_VRAM_GIB: dict[str, float] = {
    "xtts_v2": 4.0,
    "xtts": 4.0,
    "vits": 1.2,
    "yourtts": 1.5,
    "tortoise": 5.0,
    "piper": 0.25,
}
_DEFAULT_STT_GIB = 3.0
_DEFAULT_TTS_GIB = 2.0

#: Extra headroom applied to every estimate for activations, CUDA context
#: and audio buffers. The Whisper guide's own numbers are weights-only.
_ACTIVATION_OVERHEAD_GIB = 0.5


class AudioAdapter:
    """
    Adapter for one STT backend and one TTS backend.

    The scheduler sees a single adapter named "audio"; the payload's
    `task` field selects the backend. Both backends are optional — a
    deployment may configure only transcription, only synthesis, or
    neither (in which case the adapter is a no-op that rejects jobs).
    """

    DEFAULT_STT_TIMEOUT_S = 900.0
    DEFAULT_TTS_TIMEOUT_S = 300.0
    DEFAULT_UNLOAD_WAIT_S = 15.0
    PROBE_TIMEOUT_S = 5.0

    def __init__(self, config: Any, vram_manager: Any) -> None:
        self._config = config
        self._vram_manager = vram_manager

        self._stt_backend = str(
            _cfg_str(config, "audio_stt_backend") or "disabled"
        ).lower()
        self._stt_url = (_cfg_str(config, "audio_stt_base_url") or "").rstrip("/")
        self._stt_default_model = _cfg_str(
            config, "audio_stt_default_model"
        ) or "large-v3"
        self._stt_timeout = float(
            _cfg_num(
                config, "audio_stt_timeout_seconds",
                self.DEFAULT_STT_TIMEOUT_S,
            )
        )

        self._tts_backend = str(
            _cfg_str(config, "audio_tts_backend") or "disabled"
        ).lower()
        self._tts_url = (_cfg_str(config, "audio_tts_base_url") or "").rstrip("/")
        self._tts_default_model = _cfg_str(
            config, "audio_tts_default_model"
        ) or "xtts_v2"
        self._tts_default_voice = _cfg_str(config, "audio_tts_default_voice")
        self._tts_timeout = float(
            _cfg_num(
                config, "audio_tts_timeout_seconds",
                self.DEFAULT_TTS_TIMEOUT_S,
            )
        )

        self._unload_command = _cfg_str(config, "audio_unload_command")
        self._unload_wait = float(
            _cfg_num(
                config, "audio_unload_wait_seconds", self.DEFAULT_UNLOAD_WAIT_S
            )
        )
        self._vram_overrides = _cfg_dict(config, "audio_model_vram_gib") or {}

        self._session: Optional[aiohttp.ClientSession] = None
        self._busy = 0
        self._busy_lock = asyncio.Lock()
        self._cancellation_requested: set[str] = set()

        if self._stt_backend != "disabled" and not self._stt_url:
            raise ValueError(
                "audio_stt_backend is set but audio_stt_base_url is missing"
            )
        if self._tts_backend != "disabled" and not self._tts_url:
            raise ValueError(
                "audio_tts_backend is set but audio_tts_base_url is missing"
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._session is not None:
            raise RuntimeError("audio_adapter already started")
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(
                total=max(self._stt_timeout, self._tts_timeout),
                connect=10.0,
            ),
            trust_env=False,
        )
        try:
            if self._stt_backend != "disabled":
                await self._probe_stt()
            if self._tts_backend != "disabled":
                await self._probe_tts()
        except Exception:
            await self._session.close()
            self._session = None
            raise
        LOG.info(
            "audio_adapter ready (stt=%s @ %s, tts=%s @ %s, unload=%s)",
            self._stt_backend, self._stt_url or "-",
            self._tts_backend, self._tts_url or "-",
            "configured" if self._unload_command else "none",
        )

    async def stop(self) -> None:
        session = self._session
        self._session = None
        if session is not None:
            await session.close()
        LOG.info("audio_adapter stopped")

    # ------------------------------------------------------------------
    # Scheduler-facing API
    # ------------------------------------------------------------------

    async def execute(self, job: Job) -> dict[str, Any]:
        task = self._payload_str(job, "task")
        if task == "transcribe":
            return await self._execute_transcribe(job)
        if task == "synthesize":
            return await self._execute_synthesize(job)
        raise ValueError(
            f"job.payload['task'] must be 'transcribe' or 'synthesize', "
            f"got {task!r}"
        )

    async def estimate_vram(self, job: Job) -> int:
        task = self._payload_str(job, "task")
        if task == "transcribe":
            if self._stt_backend == "disabled":
                raise RuntimeError("transcription is not configured")
            model = (
                self._payload_str(job, "model") or self._stt_default_model
            )
            gib = self._lookup_vram("stt", model, _DEFAULT_STT_GIB)
        elif task == "synthesize":
            if self._tts_backend == "disabled":
                raise RuntimeError("speech synthesis is not configured")
            model = (
                self._payload_str(job, "model") or self._tts_default_model
            )
            # Piper's ONNX voices are the "piper" entry regardless of voice.
            key = "piper" if self._tts_backend == "piper" else model
            gib = self._lookup_vram("tts", key, _DEFAULT_TTS_GIB)
        else:
            raise ValueError(f"unknown audio task {task!r}")

        estimate = int((gib + _ACTIVATION_OVERHEAD_GIB) * GIB)
        LOG.debug(
            "audio estimate_vram(%s): task=%s model=%s gib=%.2f -> %d bytes",
            job.id, task, model, gib, estimate,
        )
        return estimate

    async def unload_idle_models(self, needed_bytes: int) -> int:
        """
        Run the operator-configured unload command if the adapter is idle.

        None of the common audio backends expose a documented unload
        endpoint, so this is necessarily a shell command rather than an
        HTTP call. The command is executed without a shell (shlex-split)
        so the operator cannot accidentally interpolate untrusted input;
        it is expected to be a fixed restart/evict invocation.

        Returns `needed_bytes` optimistically on success; the scheduler's
        gpu_monitor refresh after this call is what actually confirms the
        release, exactly as with the Ollama and ComfyUI adapters.
        """
        async with self._busy_lock:
            if self._busy > 0:
                LOG.info(
                    "audio unload_idle_models: %d request(s) in flight; skipping",
                    self._busy,
                )
                return 0

        if not self._unload_command:
            LOG.info(
                "audio unload_idle_models: no audio_unload_command configured; "
                "cannot free %d bytes", needed_bytes,
            )
            return 0

        argv = shlex.split(self._unload_command)
        if not argv:
            LOG.warning("audio_unload_command is empty after shlex splitting")
            return 0

        LOG.info("audio: running unload command: %s", argv)
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self._unload_wait
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                LOG.warning(
                    "audio unload command timed out after %.0fs; killed",
                    self._unload_wait,
                )
                return 0
        except Exception:
            LOG.exception("audio unload command failed to start")
            return 0

        if proc.returncode != 0:
            LOG.warning(
                "audio unload command exited %d: %s",
                proc.returncode,
                (stderr or b"").decode("utf-8", "replace")[:500],
            )
            return 0

        LOG.info(
            "audio unload command succeeded; claiming up to %d bytes freed "
            "(scheduler will confirm via gpu_monitor)", needed_bytes,
        )
        return needed_bytes

    async def request_cancel(self, job: Job) -> bool:
        """
        Best-effort cancellation.

        Neither faster-whisper-server nor Coqui expose a cancel endpoint
        for an in-flight request. The adapter can only refuse to start
        future work; the currently running HTTP request will complete and
        the scheduler will treat the result as the job's outcome. This
        matches the design doc's "non-preemptible jobs wait for a safe
        completion point" rule.
        """
        self._cancellation_requested.add(job.id)
        LOG.info(
            "audio cancellation requested for job %s; "
            "the in-flight request cannot be interrupted", job.id,
        )
        return False

    # ------------------------------------------------------------------
    # Transcription
    # ------------------------------------------------------------------

    async def _execute_transcribe(self, job: Job) -> dict[str, Any]:
        if self._stt_backend == "disabled":
            raise RuntimeError("transcription is not configured")

        session = self._require_session()
        model = self._payload_str(job, "model") or self._stt_default_model
        audio_path = self._payload_str(job, "audio_path")
        audio_url = self._payload_str(job, "audio_url")

        if not audio_path and not audio_url:
            raise ValueError(
                "transcription requires job.payload['audio_path'] or ['audio_url']"
            )

        if audio_path:
            path = Path(audio_path)
            if not path.is_file():
                raise FileNotFoundError(f"audio file not found: {path}")

        async with self._busy_lock:
            self._busy += 1
        started = time.monotonic()
        try:
            if self._stt_backend == "faster-whisper-server":
                return await self._transcribe_faster_whisper(
                    session, job, model, audio_path, audio_url, started,
                )
            if self._stt_backend == "whisper-cpp":
                return await self._transcribe_whisper_cpp(
                    session, job, model, audio_path, audio_url, started,
                )
            raise RuntimeError(
                f"unsupported audio_stt_backend: {self._stt_backend!r}"
            )
        finally:
            async with self._busy_lock:
                self._busy -= 1
            self._cancellation_requested.discard(job.id)

    async def _transcribe_faster_whisper(
        self,
        session: aiohttp.ClientSession,
        job: Job,
        model: str,
        audio_path: Optional[str],
        audio_url: Optional[str],
        started: float,
    ) -> dict[str, Any]:
        # faster-whisper-server accepts OpenAI-compatible multipart:
        # POST /v1/audio/transcriptions with file, model, response_format.
        form = aiohttp.FormData()
        form.add_field("model", model)
        form.add_field(
            "response_format",
            self._payload_str(job, "response_format") or "json",
        )
        if lang := self._payload_str(job, "language"):
            form.add_field("language", lang)
        if prompt := self._payload_str(job, "prompt"):
            form.add_field("prompt", prompt)
        if (temp := _payload_num(job, "temperature")) is not None:
            form.add_field("temperature", str(temp))

        if audio_path:
            form.add_field(
                "file",
                Path(audio_path).read_bytes(),
                filename=Path(audio_path).name,
                content_type="application/octet-stream",
            )
        else:
            audio_bytes, filename = await self._fetch_audio(audio_url or "")
            form.add_field(
                "file", audio_bytes,
                filename=filename,
                content_type="application/octet-stream",
            )

        async with session.post(
            f"{self._stt_url}/v1/audio/transcriptions",
            data=form,
            timeout=aiohttp.ClientTimeout(total=self._stt_timeout),
        ) as resp:
            if resp.status >= 400:
                text = await _safe_text(resp)
                raise RuntimeError(
                    f"faster-whisper-server returned {resp.status}: {text[:500]}"
                )
            fmt = self._payload_str(job, "response_format") or "json"
            if fmt in ("text", "srt", "vtt"):
                body = await resp.text()
                result = {
                    "task": "transcribe",
                    "text": body if fmt == "text" else "",
                    "format": fmt,
                    "raw": body if fmt != "text" else None,
                }
            else:
                data = await resp.json(content_type=None)
                result = {
                    "task": "transcribe",
                    "text": str(data.get("text") or ""),
                    "language": data.get("language"),
                    "segments": data.get("segments") or [],
                }
            result["backend"] = "faster-whisper-server"
            result["http_status"] = resp.status
            result["elapsed_s"] = round(time.monotonic() - started, 3)
            return result

    async def _transcribe_whisper_cpp(
        self,
        session: aiohttp.ClientSession,
        job: Job,
        model: str,
        audio_path: Optional[str],
        audio_url: Optional[str],
        started: float,
    ) -> dict[str, Any]:
        # whisper.cpp server exposes /inference with a multipart upload.
        form = aiohttp.FormData()
        form.add_field("response_format", "json")
        form.add_field("temperature", "0.0")
        if lang := self._payload_str(job, "language"):
            form.add_field("language", lang)

        if audio_path:
            form.add_field(
                "file",
                Path(audio_path).read_bytes(),
                filename=Path(audio_path).name,
                content_type="application/octet-stream",
            )
        else:
            audio_bytes, filename = await self._fetch_audio(audio_url or "")
            form.add_field(
                "file", audio_bytes, filename=filename,
                content_type="application/octet-stream",
            )

        async with session.post(
            f"{self._stt_url}/inference",
            data=form,
            timeout=aiohttp.ClientTimeout(total=self._stt_timeout),
        ) as resp:
            if resp.status >= 400:
                text = await _safe_text(resp)
                raise RuntimeError(
                    f"whisper.cpp /inference returned {resp.status}: {text[:500]}"
                )
            data = await resp.json(content_type=None)
        return {
            "task": "transcribe",
            "text": str((data or {}).get("text") or "").strip(),
            "language": (data or {}).get("language"),
            "segments": (data or {}).get("segments") or [],
            "backend": "whisper-cpp",
            "http_status": 200,
            "elapsed_s": round(time.monotonic() - started, 3),
        }

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    async def _execute_synthesize(self, job: Job) -> dict[str, Any]:
        if self._tts_backend == "disabled":
            raise RuntimeError("speech synthesis is not configured")

        session = self._require_session()
        text = self._payload_str(job, "text")
        if not text:
            raise ValueError("synthesis requires job.payload['text']")

        model = self._payload_str(job, "model") or self._tts_default_model
        voice = (
            self._payload_str(job, "voice") or self._tts_default_voice
        )
        output_path = self._payload_str(job, "output_path")
        fmt = self._payload_str(job, "format") or "wav"
        speed = _payload_num(job, "speed")

        async with self._busy_lock:
            self._busy += 1
        started = time.monotonic()
        try:
            if self._tts_backend == "coqui":
                return await self._synthesize_coqui(
                    session, job, text, voice, model,
                    output_path, fmt, speed, started,
                )
            if self._tts_backend == "piper":
                return await self._synthesize_piper(
                    session, job, text, voice, output_path, fmt, speed, started,
                )
            raise RuntimeError(
                f"unsupported audio_tts_backend: {self._tts_backend!r}"
            )
        finally:
            async with self._busy_lock:
                self._busy -= 1
            self._cancellation_requested.discard(job.id)

    async def _synthesize_coqui(
        self,
        session: aiohttp.ClientSession,
        job: Job,
        text: str,
        voice: Optional[str],
        model: str,
        output_path: Optional[str],
        fmt: str,
        speed: Optional[float],
        started: float,
    ) -> dict[str, Any]:
        # Coqui's TTS server exposes POST /tts_to_audio with JSON body.
        body: dict[str, Any] = {"text": text, "speaker_wav": None}
        if voice:
            body["speaker"] = voice
        if speed is not None:
            body["speed"] = speed
        if model:
            body["model_name"] = model

        async with session.post(
            f"{self._tts_url}/tts_to_audio/",
            json=body,
            timeout=aiohttp.ClientTimeout(total=self._tts_timeout),
        ) as resp:
            if resp.status >= 400:
                detail = await _safe_text(resp)
                raise RuntimeError(
                    f"coqui TTS returned {resp.status}: {detail[:500]}"
                )
            audio_bytes = await resp.read()

        written = self._write_output(audio_bytes, output_path, fmt)
        return {
            "task": "synthesize",
            "output_path": str(written) if written else None,
            "bytes": len(audio_bytes),
            "format": fmt,
            "backend": "coqui",
            "http_status": 200,
            "elapsed_s": round(time.monotonic() - started, 3),
        }

    async def _synthesize_piper(
        self,
        session: aiohttp.ClientSession,
        job: Job,
        text: str,
        voice: Optional[str],
        output_path: Optional[str],
        fmt: str,
        speed: Optional[float],
        started: float,
    ) -> dict[str, Any]:
        # Piper's HTTP server accepts POST with form fields: text, voice,
        # and optional length_scale (inverse of speed).
        form = aiohttp.FormData()
        form.add_field("text", text)
        if voice:
            form.add_field("voice", voice)
        if speed is not None and speed > 0:
            form.add_field("length_scale", str(1.0 / speed))

        async with session.post(
            f"{self._tts_url}/",
            data=form,
            timeout=aiohttp.ClientTimeout(total=self._tts_timeout),
        ) as resp:
            if resp.status >= 400:
                detail = await _safe_text(resp)
                raise RuntimeError(
                    f"piper returned {resp.status}: {detail[:500]}"
                )
            audio_bytes = await resp.read()

        written = self._write_output(audio_bytes, output_path, fmt)
        return {
            "task": "synthesize",
            "output_path": str(written) if written else None,
            "bytes": len(audio_bytes),
            "format": fmt,
            "backend": "piper",
            "http_status": 200,
            "elapsed_s": round(time.monotonic() - started, 3),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_output(
        self, audio_bytes: bytes, output_path: Optional[str], fmt: str
    ) -> Optional[Path]:
        if not output_path:
            return None
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Coqui and Piper both emit WAV by default; the format field is
        # advisory. If the backend returns MP3/OGG, the bytes are still
        # written verbatim — the caller is responsible for matching the
        # backend's actual output format to the path extension.
        path.write_bytes(audio_bytes)
        LOG.info(
            "audio synthesis wrote %d bytes to %s (format=%s)",
            len(audio_bytes), path, fmt,
        )
        return path

    async def _fetch_audio(self, url: str) -> tuple[bytes, str]:
        """Fetch remote audio for upload to the STT backend."""
        if not url:
            raise ValueError("empty audio_url")
        session = self._require_session()
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=60.0)
        ) as resp:
            if resp.status >= 400:
                raise RuntimeError(
                    f"failed to fetch audio_url {url!r}: HTTP {resp.status}"
                )
            data = await resp.read()
        filename = Path(url.split("?", 1)[0]).name or "audio.bin"
        return data, filename

    def _lookup_vram(self, kind: str, key: str, default: float) -> float:
        # Overrides take precedence: operator-supplied numbers are always
        # more accurate than the built-in table for their specific setup.
        override = self._vram_overrides.get(f"{kind}:{key}")
        if override is None:
            override = self._vram_overrides.get(key)
        if isinstance(override, (int, float)):
            return float(override)
        table = _STT_VRAM_GIB if kind == "stt" else _TTS_VRAM_GIB
        for candidate in (key, key.lower()):
            if candidate in table:
                return table[candidate]
        return default

    def _require_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("audio_adapter session is not open")
        return self._session

    @staticmethod
    def _payload_str(job: Job, key: str) -> Optional[str]:
        value = (job.payload or {}).get(key)
        return str(value) if value else None

    async def _probe_stt(self) -> None:
        session = self._require_session()
        # faster-whisper-server exposes /health; whisper.cpp exposes
        # /health as well in recent versions. Fall back to a bare GET.
        for path in ("/health", "/v1/models"):
            try:
                async with session.get(
                    f"{self._stt_url}{path}",
                    timeout=aiohttp.ClientTimeout(total=self.PROBE_TIMEOUT_S),
                ) as resp:
                    if resp.status < 500:
                        return
            except Exception:
                continue
        LOG.warning(
            "audio STT probe: %s did not respond to /health or /v1/models; "
            "transcription may fail at first use", self._stt_url,
        )

    async def _probe_tts(self) -> None:
        session = self._require_session()
        try:
            async with session.get(
                f"{self._tts_url}/",
                timeout=aiohttp.ClientTimeout(total=self.PROBE_TIMEOUT_S),
            ) as resp:
                if resp.status >= 500:
                    raise RuntimeError(f"TTS probe returned {resp.status}")
        except aiohttp.ClientConnectorError as exc:
            raise RuntimeError(
                f"cannot reach audio_tts_base_url {self._tts_url}: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _payload_num(job: Job, key: str) -> Optional[float]:
    value = (job.payload or {}).get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def _cfg_str(config: Any, name: str) -> Optional[str]:
    value = _cfg_get(config, name)
    return str(value) if value else None


def _cfg_num(config: Any, name: str, default: float) -> float:
    value = _cfg_get(config, name)
    return float(value) if isinstance(value, (int, float)) else default


def _cfg_dict(config: Any, name: str) -> Optional[dict[str, Any]]:
    value = _cfg_get(config, name)
    return dict(value) if isinstance(value, dict) else None