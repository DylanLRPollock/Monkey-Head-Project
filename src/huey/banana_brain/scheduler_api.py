"""
banana_brain.scheduler_api — local HTTP control API.

Responsibilities (from the Banana Brain design doc, §1 row 15):
  * Expose the scheduler, VRAM manager, priority queue, mode manager,
    watchdog, and job history as JSON over a local transport.
  * Authenticate TCP callers with a bearer token; rely on filesystem
    permissions for Unix-socket callers.
  * Provide a minimal unauthenticated /health probe.
  * Drain in-flight requests on shutdown, bounded by shutdown_grace_seconds.

Public API:

  async start()                           -> None
  async stop()                            -> None
  @property listening_on                  -> str | None
  async handle_request(method, path, ...)  -> (status, body)  # for tests

Lifecycle:
  async start() opens the transport and starts serving.
  async stop()  stops accepting, drains in-flight, closes.

Endpoints:

  GET  /health                       unauthenticated liveness probe
  GET  /status                       overall snapshot (version, mode, gpu,
                                     scheduler, watchdog summary)
  GET  /adapters                     list of registered adapters
  GET  /mode                         current mode + safety overlay state
  POST /mode                         transition to {mode, reason, force?}
  POST /mode/resume                  exit an exclusive mode
  POST /mode/clear-halt              clear the safety overlay
  GET  /jobs                         recent jobs (?limit=N&state=a,b)
  POST /jobs                         submit a job
  GET  /jobs/{id}                    one job
  POST /jobs/{id}/cancel             cancel (?force=true or {"force": true})
  GET  /jobs/{id}/events             event log (?limit=N)
  GET  /queue                        priority-manager snapshot
  GET  /suspended                    jobs suspended by exclusive modes
  POST /suspended/{id}/cancel        cancel a suspended job
  GET  /vram                         VRAM manager snapshot
  GET  /watchdog                     watchdog snapshot
  POST /watchdog/ack                 acknowledge a signal {"key": "..."}

Authentication:

  Unix socket: no token required.
  TCP:         Authorization: Bearer <api_token>  (required)
               X-API-Key: <api_token>             (also accepted)

  /health bypasses authentication in both cases.

Configuration fields consumed:

  api_socket_path:            Path | None
  api_bind:                   str | None          ("host:port")
  api_token:                  str | None          (required for TCP)
  shutdown_grace_seconds:     float

Dependencies:

  scheduler          .submit, .cancel, .status, .current_job,
                     .is_shutting_down, ._adapters
  job_store          .get, .list_recent, .list_events,
                     .find_by_idempotency_key
  priority_manager   .snapshot, .size
  vram_manager       .snapshot
  gpu_monitor        .get_status
  gpu_modes          .get_state, .set_mode, .resume_previous,
                     .clear_safety_halt, .get_suspended,
                     .cancel_suspended
  watchdog           .snapshot, .acknowledge, .run_once
"""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from aiohttp import web

from .job_models import (
    ALL_STATES,
    Job,
    JobState,
    Priority,
)
from .scheduler import (
    JobNotCancellable,
    SchedulerError,
    SchedulerShuttingDown,
)

__all__ = ["APIError", "SchedulerAPI"]

LOG = logging.getLogger("banana_brain.scheduler_api")

API_VERSION = "1"

DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 1000

#: Endpoints that bypass authentication. Only /health.
_PUBLIC_PATHS = frozenset({"/health"})
_REQUEST_ID_KEY = web.RequestKey("banana_brain_request_id", str)


# ---------------------------------------------------------------------------
# Error model
# ---------------------------------------------------------------------------


class APIError(Exception):
    """Raised by handlers to return a structured error response."""

    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


def _error_kind(status: int) -> str:
    if status == 400:
        return "invalid_request_error"
    if status == 401:
        return "authentication_error"
    if status == 403:
        return "permission_error"
    if status == 404:
        return "not_found_error"
    if status == 409:
        return "conflict"
    if status == 422:
        return "unprocessable_entity"
    if status == 429:
        return "rate_limit_error"
    if status == 503:
        return "service_unavailable"
    if status >= 500:
        return "internal_error"
    return "api_error"


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------


class SchedulerAPI:
    """Local HTTP control API for Banana Brain."""

    def __init__(
        self,
        config: Any,
        *,
        scheduler: Any,
        job_store: Any,
        priority_manager: Any,
        vram_manager: Any,
        gpu_monitor: Any,
        gpu_modes: Any = None,
        watchdog: Any = None,
    ) -> None:
        self._config = config
        self._scheduler = scheduler
        self._job_store = job_store
        self._priority_manager = priority_manager
        self._vram_manager = vram_manager
        self._gpu_monitor = gpu_monitor
        self._gpu_modes = gpu_modes
        self._watchdog = watchdog

        self._socket_path = _cfg_str(config, "api_socket_path")
        self._bind = _cfg_str(config, "api_bind")
        self._token = _cfg_str(config, "api_token")
        self._shutdown_grace = float(_cfg_num(config, "shutdown_grace_seconds", 30.0))

        self._runner: web.AppRunner | None = None
        self._site: web.BaseSite | None = None
        self._app: web.Application | None = None

        # In-flight request tracking for graceful drain.
        self._inflight_count = 0
        self._inflight_idle = asyncio.Event()
        self._inflight_idle.set()

        self._started_at: float | None = None
        self._listening_on: str | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._runner is not None:
            raise RuntimeError("scheduler_api already started")

        self._app = web.Application(
            middlewares=[
                self._error_middleware,
                self._auth_middleware,
                self._inflight_middleware,
            ],
            client_max_size=16 * 1024 * 1024,  # 16 MiB; prompts can be large
        )
        self._install_routes(self._app)

        self._runner = web.AppRunner(self._app, access_log=LOG, shutdown_timeout=0.1)
        await self._runner.setup()

        try:
            if self._socket_path:
                await self._start_unix()
            elif self._bind:
                await self._start_tcp()
            else:
                raise RuntimeError("neither api_socket_path nor api_bind is configured")
        except Exception:
            await self._runner.cleanup()
            self._runner = None
            self._app = None
            raise

        self._started_at = time.time()
        LOG.info(
            "scheduler_api listening on %s (auth=%s)",
            self._listening_on,
            (
                "unix-socket"
                if self._socket_path
                else ("bearer" if self._token else "none")
            ),
        )

    async def stop(self) -> None:
        if self._runner is None:
            return

        LOG.info("scheduler_api: draining in-flight requests")
        try:
            await asyncio.wait_for(
                self._inflight_idle.wait(), timeout=self._shutdown_grace
            )
        except TimeoutError:
            LOG.warning(
                "scheduler_api: %d request(s) still in flight after %.0fs; "
                "closing anyway",
                self._inflight_count,
                self._shutdown_grace,
            )

        await self._runner.cleanup()
        self._runner = None
        self._site = None
        self._app = None
        self._listening_on = None
        LOG.info("scheduler_api stopped")

    @property
    def listening_on(self) -> str | None:
        return self._listening_on

    # ------------------------------------------------------------------
    # Transport setup
    # ------------------------------------------------------------------

    async def _start_unix(self) -> None:
        assert self._runner is not None
        assert self._socket_path is not None
        socket_path = Path(self._socket_path)
        socket_path.parent.mkdir(parents=True, exist_ok=True)
        if socket_path.exists():
            socket_path.unlink()
        self._site = web.UnixSite(self._runner, str(socket_path))
        await self._site.start()
        try:
            socket_path.chmod(0o660)
        except OSError:
            LOG.debug(
                "could not chmod API socket to 0660; relying on umask",
                exc_info=True,
            )
        self._listening_on = f"unix:{socket_path}"

    async def _start_tcp(self) -> None:
        assert self._runner is not None
        assert self._bind is not None
        if not self._token:
            raise RuntimeError(
                "api_bind is set but api_token is missing; TCP exposure "
                "requires authentication"
            )
        host, _, port_str = self._bind.rpartition(":")
        if not host:
            raise RuntimeError(f"invalid api_bind {self._bind!r}")
        port = int(port_str)
        self._site = web.TCPSite(self._runner, host=host, port=port)
        await self._site.start()
        self._listening_on = f"http://{host}:{port}"

    # ------------------------------------------------------------------
    # Middleware
    # ------------------------------------------------------------------

    @web.middleware
    async def _error_middleware(
        self, request: web.Request, handler: Callable
    ) -> web.StreamResponse:
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:16]
        request[_REQUEST_ID_KEY] = request_id
        try:
            response = await handler(request)
        except APIError as exc:
            response = _error_response(exc.status, exc.message, request_id)
        except web.HTTPException as exc:
            # Preserve aiohttp's own status/headers but make the body JSON.
            response = _error_response(
                exc.status, exc.reason or _error_kind(exc.status), request_id
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            LOG.exception(
                "unhandled error in %s %s (request_id=%s)",
                request.method,
                request.path,
                request_id,
            )
            response = _error_response(500, f"{type(exc).__name__}: {exc}", request_id)
        response.headers["X-Request-Id"] = request_id
        return response

    @web.middleware
    async def _auth_middleware(
        self, request: web.Request, handler: Callable
    ) -> web.StreamResponse:
        if request.path in _PUBLIC_PATHS:
            return await handler(request)

        # Unix socket callers are already authenticated by filesystem
        # permissions on the socket. TCP callers must present a token.
        if not self._bind:
            return await handler(request)

        if not self._token:
            # Config validation should have prevented this, but be defensive.
            return _error_response(
                503,
                "TCP API is exposed without an api_token; refusing all requests",
                request.get(_REQUEST_ID_KEY, ""),
            )

        presented = _extract_token(request)
        if not presented:
            response = _error_response(
                401,
                "missing Authorization header (expected: Bearer <token>)",
                request.get(_REQUEST_ID_KEY, ""),
            )
            response.headers["WWW-Authenticate"] = "Bearer"
            return response
        if not hmac.compare_digest(presented.encode(), self._token.encode()):
            return _error_response(
                401,
                "invalid API token",
                request.get(_REQUEST_ID_KEY, ""),
            )
        return await handler(request)

    @web.middleware
    async def _inflight_middleware(
        self, request: web.Request, handler: Callable
    ) -> web.StreamResponse:
        if self._inflight_count == 0:
            self._inflight_idle.clear()
        self._inflight_count += 1
        try:
            return await handler(request)
        finally:
            self._inflight_count -= 1
            if self._inflight_count == 0:
                self._inflight_idle.set()

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------

    def _install_routes(self, app: web.Application) -> None:
        app.router.add_get("/health", self._handle_health)
        app.router.add_get("/status", self._handle_status)
        app.router.add_get("/adapters", self._handle_adapters)

        app.router.add_get("/mode", self._handle_get_mode)
        app.router.add_post("/mode", self._handle_set_mode)
        app.router.add_post("/mode/resume", self._handle_resume_mode)
        app.router.add_post("/mode/clear-halt", self._handle_clear_halt)

        app.router.add_get("/jobs", self._handle_list_jobs)
        app.router.add_post("/jobs", self._handle_submit_job)
        app.router.add_get("/jobs/{job_id}", self._handle_get_job)
        app.router.add_post("/jobs/{job_id}/cancel", self._handle_cancel_job)
        app.router.add_get("/jobs/{job_id}/events", self._handle_job_events)

        app.router.add_get("/queue", self._handle_queue)
        app.router.add_get("/suspended", self._handle_list_suspended)
        app.router.add_post("/suspended/{job_id}/cancel", self._handle_cancel_suspended)

        app.router.add_get("/vram", self._handle_vram)
        app.router.add_get("/watchdog", self._handle_watchdog)
        app.router.add_post("/watchdog/ack", self._handle_watchdog_ack)

    # ------------------------------------------------------------------
    # Handlers: health and status
    # ------------------------------------------------------------------

    async def _handle_health(self, request: web.Request) -> web.Response:
        """
        Unauthenticated liveness probe.

        Deliberately minimal: exposes enough for a health checker to know
        whether the process is alive and willing to accept work, without
        leaking job data, prompts, or VRAM figures.
        """
        shutting_down = bool(getattr(self._scheduler, "is_shutting_down", False))
        mode = None
        severity = "ok"
        if self._gpu_modes is not None:
            try:
                state = await self._gpu_modes.get_state()
                mode = state.get("mode")
                if state.get("safety_halted"):
                    severity = "critical"
            except Exception:
                LOG.exception("health: gpu_modes.get_state() raised")
                severity = "error"

        if self._watchdog is not None:
            try:
                wd = await self._watchdog.snapshot()
                for signal in wd.get("signals") or []:
                    sig_sev = str(signal.get("severity") or "ok").lower()
                    if _severity_rank(sig_sev) > _severity_rank(severity):
                        severity = sig_sev
            except Exception:
                LOG.exception("health: watchdog.snapshot() raised")
                severity = "error"

        status = 503 if shutting_down or severity == "critical" else 200
        return web.json_response(
            {
                "ok": status == 200,
                "shutting_down": shutting_down,
                "mode": mode,
                "watchdog_severity": severity,
                "api_version": API_VERSION,
            },
            status=status,
        )

    async def _handle_status(self, request: web.Request) -> web.Response:
        body: dict[str, Any] = {
            "api_version": API_VERSION,
            "started_at": self._started_at,
            "uptime_seconds": (
                round(time.time() - self._started_at, 1)
                if self._started_at is not None
                else None
            ),
            "scheduler": await _safe_call(self._scheduler, "status"),
            "adapters": sorted(getattr(self._scheduler, "_adapters", {}).keys()),
        }
        if self._gpu_modes is not None:
            body["mode"] = await _safe_call(self._gpu_modes, "get_state")
        if self._watchdog is not None:
            body["watchdog"] = await _safe_call(self._watchdog, "snapshot")

        status = await self._gpu_monitor.get_status()
        body["gpu"] = _serialise_gpu_status(status)

        return web.json_response(body)

    async def _handle_adapters(self, request: web.Request) -> web.Response:
        adapters = sorted(getattr(self._scheduler, "_adapters", {}).keys())
        return web.json_response({"adapters": adapters})

    # ------------------------------------------------------------------
    # Handlers: mode
    # ------------------------------------------------------------------

    async def _handle_get_mode(self, request: web.Request) -> web.Response:
        self._require_gpu_modes()
        state = await self._gpu_modes.get_state()
        return web.json_response(state)

    async def _handle_set_mode(self, request: web.Request) -> web.Response:
        self._require_gpu_modes()
        body = await _read_json(request)
        mode = body.get("mode")
        if not mode:
            raise APIError(400, "body.mode is required")
        reason = str(body.get("reason") or "api request")
        requested_by = _maybe_str(body.get("requested_by")) or "api"
        force = bool(body.get("force", False))

        try:
            result = await self._gpu_modes.set_mode(
                mode,
                reason=reason,
                requested_by=requested_by,
                force=force,
            )
        except Exception as exc:
            LOG.exception("mode transition raised")
            raise APIError(400, f"{type(exc).__name__}: {exc}") from exc

        status = 200 if result.success else 202
        return web.json_response(
            {
                "success": result.success,
                "from_mode": result.from_mode.value,
                "to_mode": result.to_mode.value,
                "elapsed_s": result.elapsed_s,
                "suspended_count": result.suspended_count,
                "interrupted_job_id": result.interrupted_job_id,
                "error": result.error,
            },
            status=status,
        )

    async def _handle_resume_mode(self, request: web.Request) -> web.Response:
        self._require_gpu_modes()
        body = await _read_json(request, optional=True)
        reason = str(body.get("reason") or "api resume")
        requested_by = _maybe_str(body.get("requested_by")) or "api"
        result = await self._gpu_modes.resume_previous(
            reason=reason, requested_by=requested_by
        )
        return web.json_response(
            {
                "success": result.success,
                "from_mode": result.from_mode.value,
                "to_mode": result.to_mode.value,
                "elapsed_s": result.elapsed_s,
            }
        )

    async def _handle_clear_halt(self, request: web.Request) -> web.Response:
        self._require_gpu_modes()
        body = await _read_json(request)
        reason = str(body.get("reason") or "operator cleared via API")
        cleared_by = _maybe_str(body.get("cleared_by")) or "api"
        await self._gpu_modes.clear_safety_halt(reason=reason, cleared_by=cleared_by)
        state = await self._gpu_modes.get_state()
        return web.json_response(
            {"ok": True, "safety_halted": state.get("safety_halted")}
        )

    # ------------------------------------------------------------------
    # Handlers: jobs
    # ------------------------------------------------------------------

    async def _handle_list_jobs(self, request: web.Request) -> web.Response:
        limit = _parse_limit(request.query.get("limit"), DEFAULT_LIST_LIMIT)
        states = _parse_states(request.query.get("state"))
        jobs = await self._job_store.list_recent(limit=limit, states=states)
        return web.json_response(
            {
                "count": len(jobs),
                "jobs": [job.to_dict() for job in jobs],
            }
        )

    async def _handle_submit_job(self, request: web.Request) -> web.Response:
        body = await _read_json(request)
        if not isinstance(body, dict):
            raise APIError(400, "body must be a JSON object")

        try:
            job = _job_from_body(body)
            job.validate()
        except ValueError as exc:
            raise APIError(400, str(exc)) from exc

        if job.idempotency_key:
            try:
                existing = await self._job_store.find_by_idempotency_key(
                    job.idempotency_key, job.adapter
                )
            except Exception:
                LOG.exception(
                    "idempotency lookup failed for key %r", job.idempotency_key
                )
                existing = None
            if existing is not None:
                LOG.info(
                    "submission idempotency hit: key=%r adapter=%s -> job %s",
                    job.idempotency_key,
                    job.adapter,
                    existing.id,
                )
                return web.json_response(
                    existing.to_dict(),
                    status=200,
                    headers={"Location": f"/jobs/{existing.id}"},
                )

        try:
            submitted = await self._scheduler.submit(job)
        except SchedulerShuttingDown as exc:
            raise APIError(503, str(exc)) from exc
        except SchedulerError as exc:
            raise APIError(400, str(exc)) from exc
        except Exception as exc:
            LOG.exception("scheduler.submit raised")
            raise APIError(500, f"{type(exc).__name__}: {exc}") from exc

        return web.json_response(
            submitted.to_dict(),
            status=201,
            headers={"Location": f"/jobs/{submitted.id}"},
        )

    async def _handle_get_job(self, request: web.Request) -> web.Response:
        job_id = request.match_info["job_id"]
        job = await self._job_store.get(job_id)
        if job is None:
            raise APIError(404, f"job {job_id} not found")
        return web.json_response(job.to_dict())

    async def _handle_cancel_job(self, request: web.Request) -> web.Response:
        job_id = request.match_info["job_id"]
        body = await _read_json(request, optional=True)
        force = bool(body.get("force", False))
        if "force" in request.query:
            force = request.query.get("force", "").lower() in {"1", "true", "yes"}

        # A job that is in the scheduler's queue is cancelled through
        # scheduler.cancel; a suspended job lives in gpu_modes, not in the
        # priority queue, so scheduler.cancel returns False for it. Fall
        # through to gpu_modes.cancel_suspended in that case.
        try:
            cancelled = await self._scheduler.cancel(job_id, force=force)
        except JobNotCancellable as exc:
            raise APIError(409, str(exc)) from exc
        except Exception as exc:
            LOG.exception("scheduler.cancel raised for job %s", job_id)
            raise APIError(500, f"{type(exc).__name__}: {exc}") from exc

        if not cancelled and self._gpu_modes is not None:
            try:
                cancelled = await self._gpu_modes.cancel_suspended(job_id)
            except Exception:
                LOG.exception("gpu_modes.cancel_suspended raised for job %s", job_id)

        if not cancelled:
            # Distinguish "unknown job" from "job finished already".
            job = await self._job_store.get(job_id)
            if job is None:
                raise APIError(404, f"job {job_id} not found")
            if job.state.is_terminal:
                raise APIError(
                    409,
                    f"job {job_id} is already {job.state.value}",
                )
            raise APIError(
                409,
                f"job {job_id} could not be cancelled (state={job.state.value})",
            )

        job = await self._job_store.get(job_id)
        return web.json_response(
            {
                "ok": True,
                "job_id": job_id,
                "state": job.state.value if job else None,
                "force": force,
            }
        )

    async def _handle_job_events(self, request: web.Request) -> web.Response:
        job_id = request.match_info["job_id"]
        limit = _parse_limit(request.query.get("limit"), 100)
        events = await self._job_store.list_events(job_id, limit=limit)
        return web.json_response({"job_id": job_id, "events": events})

    # ------------------------------------------------------------------
    # Handlers: queue, suspended, vram
    # ------------------------------------------------------------------

    async def _handle_queue(self, request: web.Request) -> web.Response:
        limit = _parse_limit(request.query.get("limit"), None)
        snapshot = await self._priority_manager.snapshot(limit=limit)
        return web.json_response(snapshot)

    async def _handle_list_suspended(self, request: web.Request) -> web.Response:
        self._require_gpu_modes()
        suspended = await self._gpu_modes.get_suspended()
        return web.json_response({"count": len(suspended), "jobs": suspended})

    async def _handle_cancel_suspended(self, request: web.Request) -> web.Response:
        self._require_gpu_modes()
        job_id = request.match_info["job_id"]
        cancelled = await self._gpu_modes.cancel_suspended(job_id)
        if not cancelled:
            raise APIError(404, f"suspended job {job_id} not found")
        return web.json_response({"ok": True, "job_id": job_id})

    async def _handle_vram(self, request: web.Request) -> web.Response:
        snapshot = await self._vram_manager.snapshot()
        return web.json_response(snapshot)

    # ------------------------------------------------------------------
    # Handlers: watchdog
    # ------------------------------------------------------------------

    async def _handle_watchdog(self, request: web.Request) -> web.Response:
        if self._watchdog is None:
            raise APIError(503, "watchdog is not configured")
        snapshot = await self._watchdog.snapshot()
        return web.json_response(snapshot)

    async def _handle_watchdog_ack(self, request: web.Request) -> web.Response:
        if self._watchdog is None:
            raise APIError(503, "watchdog is not configured")
        body = await _read_json(request)
        key = body.get("key")
        if not key:
            raise APIError(400, "body.key is required")
        await self._watchdog.acknowledge(str(key))
        return web.json_response({"ok": True, "key": str(key)})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _require_gpu_modes(self) -> None:
        if self._gpu_modes is None:
            raise APIError(503, "gpu_modes is not configured")


# ---------------------------------------------------------------------------
# Request parsing
# ---------------------------------------------------------------------------


async def _read_json(request: web.Request, *, optional: bool = False) -> dict[str, Any]:
    text = await request.text()
    if not text.strip():
        if optional:
            return {}
        raise APIError(400, "request body is required")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise APIError(400, f"invalid JSON body: {exc}") from exc
    if not isinstance(data, dict):
        raise APIError(400, "request body must be a JSON object")
    return data


def _job_from_body(body: dict[str, Any]) -> Job:
    """
    Build a Job from an API submission body.

    Accepts the same field names as Job.to_dict(), except that id,
    state, submitted_at, started_at, finished_at, attempts, last_error,
    and result are all forbidden — those are scheduler-assigned.
    """
    forbidden = {
        "id",
        "state",
        "submitted_at",
        "started_at",
        "finished_at",
        "attempts",
        "last_error",
        "result",
        "version",
    }
    present = forbidden & set(body)
    if present:
        raise ValueError(
            f"fields are assigned by the scheduler and may not be set by "
            f"clients: {', '.join(sorted(present))}"
        )

    adapter = body.get("adapter")
    if not isinstance(adapter, str) or not adapter:
        raise ValueError("field 'adapter' is required and must be a string")

    payload = body.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("field 'payload' is required and must be an object")

    priority_raw = body.get("priority")
    if priority_raw is None:
        priority = int(Priority.BACKGROUND)
    elif isinstance(priority_raw, bool):
        raise ValueError("priority must be an int, got bool")
    elif isinstance(priority_raw, (int, float)):
        priority = int(priority_raw)
    elif isinstance(priority_raw, str) and priority_raw.upper() in Priority.__members__:
        priority = int(Priority[priority_raw.upper()])
    else:
        raise ValueError(
            f"priority must be an int or Priority name, got {priority_raw!r}"
        )

    deadline = body.get("deadline")
    if deadline is not None:
        try:
            deadline = float(deadline)
        except (TypeError, ValueError):
            raise ValueError("deadline must be a unix timestamp or null") from None

    est = body.get("estimated_vram_bytes")
    if est is not None and (
        not isinstance(est, int) or isinstance(est, bool) or est <= 0
    ):
        raise ValueError("estimated_vram_bytes must be a positive int")

    tags = body.get("tags") or {}
    if not isinstance(tags, dict):
        raise ValueError("tags must be an object")

    owner = body.get("owner")
    if owner is not None and not isinstance(owner, str):
        raise ValueError("owner must be a string or null")

    idem = body.get("idempotency_key")
    if idem is not None and not isinstance(idem, str):
        raise ValueError("idempotency_key must be a string or null")

    max_attempts = body.get("max_attempts", 1)
    if (
        not isinstance(max_attempts, int)
        or isinstance(max_attempts, bool)
        or max_attempts < 1
    ):
        raise ValueError("max_attempts must be an int >= 1")

    return Job(
        adapter=adapter,
        payload=payload,
        priority=priority,
        exclusive=bool(body.get("exclusive", False)),
        deadline=deadline,
        estimated_vram_bytes=est,
        owner=owner,
        tags={str(k): str(v) for k, v in tags.items()},
        idempotency_key=idem,
        max_attempts=max_attempts,
    )


def _parse_limit(value: str | None, default: int | None) -> int | None:
    if value is None or value == "":
        return default
    try:
        n = int(value)
    except ValueError:
        raise APIError(400, f"limit must be an int, got {value!r}") from None
    if n < 0:
        raise APIError(400, "limit must be >= 0")
    return min(n, MAX_LIST_LIMIT)


def _parse_states(value: str | None) -> set[JobState] | None:
    if not value:
        return None
    parts = [p.strip().lower() for p in value.split(",") if p.strip()]
    if not parts:
        return None
    result: set[JobState] = set()
    for part in parts:
        try:
            result.add(JobState(part))
        except ValueError:
            valid = ", ".join(s.value for s in ALL_STATES)
            raise APIError(
                400, f"unknown state {part!r}; valid states: {valid}"
            ) from None
    return result


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def _extract_token(request: web.Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key.strip() or None
    return None


def _error_response(status: int, message: str, request_id: str) -> web.Response:
    return web.json_response(
        {
            "error": {
                "message": message,
                "type": _error_kind(status),
                "code": status,
                "request_id": request_id,
            }
        },
        status=status,
    )


def _severity_rank(severity: str) -> int:
    return {
        "ok": 0,
        "warn": 1,
        "error": 2,
        "critical": 3,
    }.get(severity.lower(), 0)


async def _safe_call(obj: Any, method: str) -> Any:
    fn = getattr(obj, method, None)
    if not callable(fn):
        return None
    try:
        result = fn()
        if asyncio.iscoroutine(result):
            return await result
        return result
    except Exception:
        LOG.exception("api: call %s.%s raised", type(obj).__name__, method)
        return {"error": "call failed"}


def _serialise_gpu_status(status: Any) -> dict[str, Any] | None:
    if status is None:
        return None
    try:
        identity = getattr(status, "identity", None)
        health = getattr(status, "health", None)
        return {
            "identity": (
                {
                    "index": getattr(identity, "index", None),
                    "name": getattr(identity, "name", None),
                    "uuid": getattr(identity, "uuid", None),
                    "pci_bus_id": getattr(identity, "pci_bus_id", None),
                }
                if identity is not None
                else None
            ),
            "timestamp": getattr(status, "timestamp", None),
            "total_vram_bytes": getattr(status, "total_vram_bytes", None),
            "free_vram_bytes": getattr(status, "free_vram_bytes", None),
            "used_vram_bytes": getattr(status, "used_vram_bytes", None),
            "reserved_vram_bytes": getattr(status, "reserved_vram_bytes", None),
            "gpu_utilization_percent": getattr(status, "gpu_utilization_percent", None),
            "memory_utilization_percent": getattr(
                status, "memory_utilization_percent", None
            ),
            "temperature_c": getattr(status, "temperature_c", None),
            "power_watts": getattr(status, "power_watts", None),
            "process_count": len(getattr(status, "processes", ()) or ()),
            "health": (
                {
                    "thermal_slowdown": getattr(health, "thermal_slowdown", False),
                    "power_brake": getattr(health, "power_brake", False),
                    "device_lost": getattr(health, "device_lost", False),
                    "shutdown_threshold_c": getattr(
                        health, "shutdown_threshold_c", None
                    ),
                    "slowdown_threshold_c": getattr(
                        health, "slowdown_threshold_c", None
                    ),
                    "power_limit_watts": getattr(health, "power_limit_watts", None),
                }
                if health is not None
                else None
            ),
        }
    except Exception:
        LOG.exception("api: failed to serialise GPUStatus")
        return None


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def _cfg_get(config: Any, name: str) -> Any:
    if isinstance(config, dict):
        return config.get(name)
    return getattr(config, name, None)


def _cfg_str(config: Any, name: str) -> str | None:
    value = _cfg_get(config, name)
    return str(value) if value else None


def _cfg_num(config: Any, name: str, default: float) -> float:
    value = _cfg_get(config, name)
    return float(value) if isinstance(value, (int, float)) else default


def _maybe_str(value: Any) -> str | None:
    """Return non-empty string values, ignoring other optional inputs."""
    return value.strip() if isinstance(value, str) and value.strip() else None
