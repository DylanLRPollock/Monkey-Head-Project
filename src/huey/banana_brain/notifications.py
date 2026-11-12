"""
banana_brain.notifications — operator notification dispatcher.

Responsibilities (from the Banana Brain design doc, §1 row 18):
  * Report task completion, overheating, failed jobs, and manual
    intervention requests (stuck jobs, safety halts).
  * Dispatch notifications to any of four backends:
      - log      (always on; structured log record)
      - desktop  (notify-send on Linux; optional)
      - webhook  (HTTP POST to an operator URL; optional)
      - file     (append-only JSONL for postmortem; optional)
  * Deduplicate repeated notifications by (kind, key).
  * Never block the caller: enqueue and return.

Public API:

  async start()                                                   -> None
  async stop()                                                    -> None
  async notify(level, title, message, details=None, *, kind, key)  -> None
  def   get_stats()                                               -> dict

Lifecycle (called by the composition root):
  async start() opens backends and starts the delivery worker.
  async stop()  flushes pending notifications (bounded by grace).

Contract used by callers:

  watchdog calls:
    await notifications.notify(
        level=signal.severity.label().lower(),
        title=signal.name,
        message=signal.message,
        details=signal.details,
    )
    # level: "ok" | "warn" | "error" | "critical"

  scheduler completion path (recommended):
    await notifications.notify(
        level="info" if job.state == COMPLETED else "warn",
        title=f"{job.adapter} job {job.state.value}",
        message=...,
        details={"job_id": job.id, "adapter": job.adapter},
        kind=Kinds.JOB_COMPLETED if ... else Kinds.JOB_FAILED,
        key=f"job:{job.id}",   # dedup on the job id
    )

Configuration fields consumed:

  notifications_enabled:                  bool   default True
  notifications_cooldown_seconds:         float  default 300
  notifications_queue_maxsize:            int    default 512
  notifications_shutdown_grace_seconds:   float  default 5

  notifications_min_level_log:            str    default "info"
  notifications_min_level_desktop:        str    default "warn"
  notifications_min_level_webhook:        str    default "error"
  notifications_min_level_file:           str    default "info"

  notifications_desktop_enabled:          bool   default False
  notifications_desktop_timeout_ms:       int    default 8000

  notifications_webhook_url:              str    default None
  notifications_webhook_token:            str    default None
  notifications_webhook_timeout_seconds:  float  default 5

  notifications_file_path:                Path   default None

Levels:

  Ranked info < warn < error < critical. "ok" is accepted and normalised
  to "info" (the watchdog uses "ok" in its severity enum but never calls
  notify() with it; the normalisation is defensive).

No auto-resume; safety halts are covered by the watchdog's own WARN
signal (temperature_clearable) so that a notification of the halt exists
but no notification of a *resume* fires until the operator clears it.

Dependencies:

  aiohttp   for the webhook backend
  no dependency for the log backend (uses logging)
  no dependency for the desktop backend (uses notify-send via subprocess)
  no dependency for the file backend (uses pathlib and json)
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import shutil
import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, ClassVar, Protocol

import aiohttp

__all__ = [
    "Kinds",
    "Notification",
    "NotificationLevel",
    "Notifier",
]

LOG = logging.getLogger("banana_brain.notifications")


# ---------------------------------------------------------------------------
# Levels and kind constants
# ---------------------------------------------------------------------------


class NotificationLevel(IntEnum):
    INFO = 10
    WARN = 20
    ERROR = 30
    CRITICAL = 40

    def label(self) -> str:
        return self.name.lower()


class Kinds:
    """Well-known kind tags. Free-form; backends may route on them."""

    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"
    THERMAL = "thermal"
    STUCK_JOB = "stuck_job"
    SERVICE_DOWN = "service.down"
    MODE_CHANGE = "mode.change"
    SAFETY_HALT = "safety.halt"
    SAFETY_HALT_CLEARED = "safety.halt_cleared"
    LEASE_EXPIRY = "lease.expiry"
    GPU_UNAVAILABLE = "gpu.unavailable"


_LEVEL_ALIASES = {
    "ok": NotificationLevel.INFO,
    "info": NotificationLevel.INFO,
    "warn": NotificationLevel.WARN,
    "warning": NotificationLevel.WARN,
    "error": NotificationLevel.ERROR,
    "crit": NotificationLevel.CRITICAL,
    "critical": NotificationLevel.CRITICAL,
}


def _parse_level(value: Any) -> NotificationLevel:
    if isinstance(value, NotificationLevel):
        return value
    text = str(value or "info").strip().lower()
    if text in _LEVEL_ALIASES:
        return _LEVEL_ALIASES[text]
    raise ValueError(
        f"unknown notification level {value!r}; "
        f"valid: {', '.join(sorted(_LEVEL_ALIASES))}"
    )


# ---------------------------------------------------------------------------
# Notification record
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Notification:
    id: str
    at: float
    level: NotificationLevel
    title: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    kind: str | None = None
    key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "at": self.at,
            "level": self.level.label(),
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "kind": self.kind,
            "key": self.key,
        }


# ---------------------------------------------------------------------------
# Backend protocol
# ---------------------------------------------------------------------------


class Backend(Protocol):
    name: str
    min_level: NotificationLevel

    async def send(self, notification: Notification) -> None:
        raise NotImplementedError

    async def close(self) -> None:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Log backend (always on)
# ---------------------------------------------------------------------------


class LogBackend:
    name = "log"

    def __init__(self, min_level: NotificationLevel) -> None:
        self.min_level = min_level

    async def send(self, notification: Notification) -> None:
        prefix = f"[{notification.kind or 'notify'}]"
        text = f"{prefix} {notification.title}: {notification.message}"
        details = notification.details
        if notification.level is NotificationLevel.CRITICAL:
            LOG.critical(text, extra={"notification": notification.to_dict()})
        elif notification.level is NotificationLevel.ERROR:
            LOG.error(text, extra={"notification": notification.to_dict()})
        elif notification.level is NotificationLevel.WARN:
            LOG.warning(text, extra={"notification": notification.to_dict()})
        else:
            LOG.info(text, extra={"notification": notification.to_dict()})
        if details:
            LOG.debug("notification details: %s", details)

    async def close(self) -> None:
        return


# ---------------------------------------------------------------------------
# Desktop backend (notify-send)
# ---------------------------------------------------------------------------


class DesktopBackend:
    """
    Sends notifications via ``notify-send`` on Linux.

    Disabled automatically if notify-send is not on PATH. Each invocation
    runs in a subprocess with a bounded timeout. A failed popup (e.g. no
    desktop session) is logged once per run and does not raise.
    """

    name = "desktop"

    _URGENCY: ClassVar[dict[NotificationLevel, str]] = {
        NotificationLevel.INFO: "low",
        NotificationLevel.WARN: "normal",
        NotificationLevel.ERROR: "critical",
        NotificationLevel.CRITICAL: "critical",
    }

    def __init__(
        self,
        min_level: NotificationLevel,
        timeout_ms: int = 8000,
    ) -> None:
        self.min_level = min_level
        self._timeout_ms = int(timeout_ms)
        self._binary = shutil.which("notify-send")
        self._availability_warned = False
        if self._binary is None:
            LOG.info(
                "notifications: desktop backend unavailable "
                "(notify-send not on PATH)"
            )

    async def send(self, notification: Notification) -> None:
        if self._binary is None:
            return
        urgency = self._URGENCY.get(notification.level, "normal")
        body = notification.message
        if notification.details:
            # A single line of key=value detail, kept short.
            detail_line = " ".join(
                f"{k}={v}" for k, v in list(notification.details.items())[:4]
            )
            body = f"{body}\n{detail_line}"[:512]
        argv = [
            self._binary,
            "-u",
            urgency,
            "-a",
            "Banana Brain",
            "-t",
            str(self._timeout_ms),
            notification.title,
            body,
        ]
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        except TimeoutError:
            with contextlib.suppress(Exception):
                proc.kill()
            LOG.debug("desktop notification timed out")
            return
        except FileNotFoundError:
            self._binary = None
            LOG.info("desktop backend disabled: notify-send disappeared")
            return
        except Exception:
            LOG.exception("desktop notification failed to start")
            return

        if proc.returncode != 0 and not self._availability_warned:
            self._availability_warned = True
            LOG.info(
                "desktop notification exited %d; disabling further attempts "
                "for this process: %s",
                proc.returncode,
                (stderr or b"").decode("utf-8", "replace")[:200],
            )
            self._binary = None

    async def close(self) -> None:
        return


# ---------------------------------------------------------------------------
# Webhook backend
# ---------------------------------------------------------------------------


class WebhookBackend:
    """
    POSTs each notification as JSON to an operator-configured URL.

    A token, if provided, is sent as ``Authorization: Bearer <token>``.
    Non-2xx responses are logged at warning once per run and do not raise.
    Each request has an independent timeout so a slow webhook cannot stall
    the delivery worker indefinitely.
    """

    name = "webhook"

    def __init__(
        self,
        url: str,
        *,
        token: str | None,
        min_level: NotificationLevel,
        timeout_s: float = 5.0,
    ) -> None:
        self.min_level = min_level
        self._url = url
        self._token = token
        self._timeout_s = float(timeout_s)
        self._session: aiohttp.ClientSession | None = None
        self._auth_failure_warned = False

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "banana-brain/notifications",
            }
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self._timeout_s),
                trust_env=False,
            )
        return self._session

    async def send(self, notification: Notification) -> None:
        session = await self._ensure_session()
        body = notification.to_dict()
        try:
            async with session.post(self._url, json=body) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    if resp.status in (401, 403) and not self._auth_failure_warned:
                        self._auth_failure_warned = True
                        LOG.warning(
                            "webhook rejected the notification (HTTP %d): "
                            "check notifications_webhook_token; %s",
                            resp.status,
                            text[:200],
                        )
                    else:
                        LOG.warning(
                            "webhook returned HTTP %d for notification %s: %s",
                            resp.status,
                            notification.id,
                            text[:200],
                        )
        except TimeoutError:
            LOG.warning(
                "webhook timed out after %.1fs for notification %s",
                self._timeout_s,
                notification.id,
            )
        except Exception:
            LOG.exception(
                "webhook delivery failed for notification %s",
                notification.id,
            )

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None


# ---------------------------------------------------------------------------
# File backend
# ---------------------------------------------------------------------------


class FileBackend:
    """
    Appends each notification as a JSON line to ``path``.

    The file is opened lazily and closed on stop(). Writes are simple
    appends — one process writes to the file, so no locking is needed.
    Failures are logged once and disable the backend for the rest of the
    process; a broken log file must not spam the log.
    """

    name = "file"

    def __init__(self, path: Path, *, min_level: NotificationLevel) -> None:
        self.min_level = min_level
        self._path = path
        self._handle: Any = None
        self._failed = False

    async def send(self, notification: Notification) -> None:
        if self._failed:
            return
        try:
            if self._handle is None:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                # This handle intentionally stays open until close() so each
                # notification appends through one lifecycle-managed stream.
                self._handle = open(self._path, "a", encoding="utf-8")  # noqa: SIM115
            self._handle.write(
                json.dumps(notification.to_dict(), ensure_ascii=False) + "\n"
            )
            self._handle.flush()
        except Exception:
            self._failed = True
            LOG.exception(
                "file notifications disabled after write failure to %s",
                self._path,
            )

    async def close(self) -> None:
        if self._handle is not None:
            try:
                self._handle.close()
            except Exception:
                LOG.debug("file backend close failed", exc_info=True)
            self._handle = None


# ---------------------------------------------------------------------------
# Notifier
# ---------------------------------------------------------------------------


class Notifier:
    """
    Dispatches notifications to one or more backends.

    Owns the queue, the worker, deduplication, and per-backend filtering.
    All backends are optional except LogBackend, which is always enabled.
    """

    DEFAULT_COOLDOWN_S = 300.0
    DEFAULT_QUEUE_MAXSIZE = 512
    DEFAULT_SHUTDOWN_GRACE_S = 5.0
    DEFAULT_DESKTOP_TIMEOUT_MS = 8000
    DEFAULT_WEBHOOK_TIMEOUT_S = 5.0

    def __init__(self, config: Any) -> None:
        self._config = config
        self._enabled = _cfg_bool(config, "notifications_enabled", True)
        self._cooldown = float(
            _cfg_num(
                config,
                "notifications_cooldown_seconds",
                self.DEFAULT_COOLDOWN_S,
            )
        )
        self._shutdown_grace = float(
            _cfg_num(
                config,
                "notifications_shutdown_grace_seconds",
                self.DEFAULT_SHUTDOWN_GRACE_S,
            )
        )

        self._backends: list[Backend] = []
        self._queue: asyncio.Queue[Notification] | None = None
        self._worker: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()

        # Dedup: last emission time per (kind, key) or (kind, title).
        self._last_emitted: dict[str, float] = {}

        # Stats surfaced via get_stats().
        self._stats = {
            "enqueued": 0,
            "delivered": 0,
            "dropped_overflow": 0,
            "dropped_cooldown": 0,
            "backend_failures": 0,
        }

        if not self._enabled:
            LOG.info("notifications disabled by config")
            return

        self._build_backends(config)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if not self._enabled:
            return
        if self._worker is not None:
            raise RuntimeError("notifications already started")
        maxsize = int(
            _cfg_num(
                self._config,
                "notifications_queue_maxsize",
                self.DEFAULT_QUEUE_MAXSIZE,
            )
        )
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._stop_event.clear()
        self._worker = asyncio.create_task(
            self._delivery_loop(), name="banana-brain-notifications"
        )
        LOG.info(
            "notifications ready (backends=%s, cooldown=%.0fs, queue=%d)",
            ", ".join(b.name for b in self._backends),
            self._cooldown,
            maxsize,
        )

    async def stop(self) -> None:
        self._stop_event.set()
        worker = self._worker
        self._worker = None
        if worker is not None:
            try:
                await asyncio.wait_for(worker, timeout=self._shutdown_grace)
            except TimeoutError:
                worker.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await worker
                LOG.warning(
                    "notifications: delivery worker did not stop within "
                    "%.1fs; pending notifications may be lost",
                    self._shutdown_grace,
                )
        for backend in self._backends:
            try:
                await backend.close()
            except Exception:
                LOG.exception("notifications: backend %s close failed", backend.name)
        self._backends.clear()
        self._queue = None
        LOG.info(
            "notifications stopped (stats=%s)",
            self._stats,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def notify(  # noqa: C901,RUF100
        self,
        level: Any,
        title: str,
        message: str,
        details: dict[str, Any] | None = None,
        *,
        kind: str | None = None,
        key: str | None = None,
    ) -> None:
        """
        Enqueue a notification for delivery. Returns immediately.

        Contract: never raises on a backend failure, never blocks the
        caller on network I/O, and never lets a bad notification break
        the caller's main loop. Delivery happens in a background worker.
        """
        if not self._enabled:
            return
        try:
            parsed_level = _parse_level(level)
        except ValueError:
            LOG.warning("notifications: invalid level %r; dropping", level)
            return

        # Dedup: same (kind, key) or (kind, title) within cooldown.
        cooldown_key = (
            f"{kind or ''}::{(key or title).lower()}" if kind or key else None
        )
        now = time.monotonic()
        if cooldown_key is not None and self._cooldown > 0:
            last = self._last_emitted.get(cooldown_key)
            if last is not None and now - last < self._cooldown:
                self._stats["dropped_cooldown"] += 1
                return
            self._last_emitted[cooldown_key] = now

        notification = Notification(
            id=uuid.uuid4().hex[:16],
            at=time.time(),
            level=parsed_level,
            title=str(title)[:200],
            message=str(message)[:2000],
            details=dict(details or {}),
            kind=kind,
            key=key,
        )

        queue = self._queue
        if queue is None:
            # Notifier stopped or never started; log directly as a fallback.
            await LogBackend(NotificationLevel.INFO).send(notification)
            return

        try:
            queue.put_nowait(notification)
            self._stats["enqueued"] += 1
        except asyncio.QueueFull:
            # Drop the oldest to make room for the new one.
            try:
                queue.get_nowait()
                self._stats["dropped_overflow"] += 1
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(notification)
                self._stats["enqueued"] += 1
            except asyncio.QueueFull:
                self._stats["dropped_overflow"] += 1
                LOG.warning(
                    "notifications: queue full (%d) and could not drop; "
                    "discarding notification %r",
                    queue.maxsize,
                    notification.title,
                )

    def get_stats(self) -> dict[str, Any]:
        return {
            **self._stats,
            "backends": [b.name for b in self._backends],
            "queue_depth": self._queue.qsize() if self._queue else 0,
            "queue_maxsize": self._queue.maxsize if self._queue else 0,
        }

    # ------------------------------------------------------------------
    # Delivery worker
    # ------------------------------------------------------------------

    async def _delivery_loop(self) -> None:
        assert self._queue is not None
        while not self._stop_event.is_set():
            try:
                notification = await asyncio.wait_for(self._queue.get(), timeout=0.5)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                raise
            try:
                await self._deliver(notification)
            except asyncio.CancelledError:
                raise
            except Exception:
                LOG.exception("notifications: delivery failed for %s", notification.id)
            finally:
                with contextlib.suppress(Exception):
                    self._queue.task_done()

    async def _deliver(self, notification: Notification) -> None:
        delivered_anywhere = False
        for backend in self._backends:
            if notification.level < backend.min_level:
                continue
            try:
                await asyncio.wait_for(backend.send(notification), timeout=10.0)
                delivered_anywhere = True
            except TimeoutError:
                self._stats["backend_failures"] += 1
                LOG.warning(
                    "notifications: backend %s timed out for %s",
                    backend.name,
                    notification.id,
                )
            except Exception:
                self._stats["backend_failures"] += 1
                LOG.exception(
                    "notifications: backend %s raised for %s",
                    backend.name,
                    notification.id,
                )
        if delivered_anywhere:
            self._stats["delivered"] += 1

    # ------------------------------------------------------------------
    # Backend construction
    # ------------------------------------------------------------------

    def _build_backends(self, config: Any) -> None:
        # Log backend is always present at the configured level.
        log_level = _parse_level(
            _cfg_str(config, "notifications_min_level_log") or "info"
        )
        self._backends.append(LogBackend(log_level))

        if _cfg_bool(config, "notifications_desktop_enabled", False):
            desktop_min = _parse_level(
                _cfg_str(config, "notifications_min_level_desktop") or "warn"
            )
            desktop_timeout = int(
                _cfg_num(
                    config,
                    "notifications_desktop_timeout_ms",
                    self.DEFAULT_DESKTOP_TIMEOUT_MS,
                )
            )
            self._backends.append(
                DesktopBackend(
                    min_level=desktop_min,
                    timeout_ms=desktop_timeout,
                )
            )

        webhook_url = _cfg_str(config, "notifications_webhook_url")
        if webhook_url:
            webhook_min = _parse_level(
                _cfg_str(config, "notifications_min_level_webhook") or "error"
            )
            webhook_timeout = float(
                _cfg_num(
                    config,
                    "notifications_webhook_timeout_seconds",
                    self.DEFAULT_WEBHOOK_TIMEOUT_S,
                )
            )
            self._backends.append(
                WebhookBackend(
                    url=webhook_url,
                    token=_cfg_str(config, "notifications_webhook_token"),
                    min_level=webhook_min,
                    timeout_s=webhook_timeout,
                )
            )

        file_path = _cfg_str(config, "notifications_file_path")
        if file_path:
            file_min = _parse_level(
                _cfg_str(config, "notifications_min_level_file") or "info"
            )
            self._backends.append(
                FileBackend(Path(file_path).expanduser(), min_level=file_min)
            )


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


def _cfg_bool(config: Any, name: str, default: bool) -> bool:
    value = _cfg_get(config, name)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)
