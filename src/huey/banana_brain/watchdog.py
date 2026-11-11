"""
banana_brain.watchdog — GPU health monitoring and safety escalation.

Responsibilities (from the Banana Brain design doc, §1 row 14):
  * Detect stuck jobs and request cancellation at the adapter.
  * Detect lost services (Ollama, ComfyUI, audio) and log persistent
    failures without halting the whole system.
  * Detect lease expirations: VRAM reservations held past a reasonable
    lifetime without a corresponding running job.
  * Detect abnormal temperatures and GPU-monitor visibility loss, and
    escalate to force_safety_halt() via gpu_modes.

Public API:

  async start()                                    -> None
  async stop()                                     -> None
  async run_once()                                 -> list[HealthSignal]
  async snapshot()                                 -> dict
  async acknowledge(signal_key)                    -> None  (CLI/API)

Lifecycle:
  async start()/async stop()

Severity model:

  OK        nothing to report.
  WARN      watch this; no action taken. Deduplicated by key with a
            cooldown so a persistent condition does not flood the log.
  ERROR     action taken (job cancellation requested, service marked down).
            Logged once per event.
  CRITICAL  requires operator intervention. The watchdog engages the
            safety overlay via mode_manager.force_safety_halt(). It will
            NOT clear it — see "no auto-resume" below.

No auto-resume:

  Once the watchdog escalates to force_safety_halt(), the operator must
  call mode_manager.clear_safety_halt() explicitly. The watchdog logs a
  WARN when the underlying condition has cleared, pointing the operator
  at the command to run, but never clears the halt itself. Thermal events
  do not heal in five seconds, and a scheduler that resumes work the
  moment the sensor drops below the threshold would flap.

Configuration fields consumed:

  watchdog_check_interval_seconds:     default 15
  watchdog_temperature_warn_c:         default 80
  watchdog_temperature_ceiling_c:      default 85
  watchdog_gpu_unavailable_warn_s:     default 15
  watchdog_gpu_unavailable_critical_s: default 120
  watchdog_stuck_job_seconds:          default 1800
  watchdog_cancel_grace_seconds:       default 60
  watchdog_service_failure_threshold:  default 3
  watchdog_lease_expiry_seconds:       default 120
  watchdog_signal_cooldown_seconds:    default 600

Dependencies:
  gpu_monitor    .get_status() -> GPUStatus | None, .refresh() -> GPUStatus | None
  scheduler      .current_job, .cancel(job_id, force=True)
  vram_manager   .snapshot() -> dict
  job_store      .get(job_id) -> Job | None     (optional; used to reload)
  adapters       .probe() -> None               (optional; falls back to a
                                                 private _probe if present)
  mode_manager   .force_safety_halt(reason)     (optional; escalates CRITICAL)
  notifications  .notify(level, title, message, details) (optional)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional

__all__ = [
    "Watchdog",
    "HealthSignal",
    "Severity",
]

LOG = logging.getLogger("banana_brain.watchdog")

GIB = 1024 ** 3


# ---------------------------------------------------------------------------
# Signal model
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    OK = 0
    WARN = 1
    ERROR = 2
    CRITICAL = 3

    def label(self) -> str:
        return self.name


@dataclass(frozen=True)
class HealthSignal:
    """
    One result of one check. `key` is stable across ticks so the watchdog
    can deduplicate warnings; `name` is the human-readable check name.
    """

    name: str
    severity: Severity
    message: str
    key: str
    details: dict[str, Any] = field(default_factory=dict)
    action: Optional[str] = None


# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------

class Watchdog:
    """
    Periodic health monitor with safety escalation.

    Runs a single background task. All external calls are awaited inside
    that task; failures in individual checks do not abort the loop.
    """

    DEFAULT_CHECK_INTERVAL_S = 15.0
    DEFAULT_TEMP_WARN_C = 80.0
    DEFAULT_TEMP_CEILING_C = 85.0
    DEFAULT_UNAVAILABLE_WARN_S = 15.0
    DEFAULT_UNAVAILABLE_CRITICAL_S = 120.0
    DEFAULT_STUCK_JOB_S = 1800.0
    DEFAULT_CANCEL_GRACE_S = 60.0
    DEFAULT_SERVICE_FAILURE_THRESHOLD = 3
    DEFAULT_LEASE_EXPIRY_S = 120.0
    DEFAULT_SIGNAL_COOLDOWN_S = 600.0

    def __init__(
        self,
        config: Any,
        *,
        scheduler: Any,
        gpu_monitor: Any,
        vram_manager: Any,
        job_store: Any,
        adapters: dict[str, Any],
        mode_manager: Any = None,
        notifications: Any = None,
    ) -> None:
        self._config = config
        self._scheduler = scheduler
        self._gpu_monitor = gpu_monitor
        self._vram_manager = vram_manager
        self._job_store = job_store
        self._adapters = dict(adapters or {})
        self._mode_manager = mode_manager
        self._notifications = notifications

        self._check_interval = float(
            _cfg_num(
                config, "watchdog_check_interval_seconds",
                self.DEFAULT_CHECK_INTERVAL_S,
            )
        )
        self._temp_warn_c = float(
            _cfg_num(
                config, "watchdog_temperature_warn_c",
                self.DEFAULT_TEMP_WARN_C,
            )
        )
        self._temp_ceiling_c = float(
            _cfg_num(
                config, "watchdog_temperature_ceiling_c",
                self.DEFAULT_TEMP_CEILING_C,
            )
        )
        self._unavailable_warn_s = float(
            _cfg_num(
                config, "watchdog_gpu_unavailable_warn_s",
                self.DEFAULT_UNAVAILABLE_WARN_S,
            )
        )
        self._unavailable_critical_s = float(
            _cfg_num(
                config, "watchdog_gpu_unavailable_critical_s",
                self.DEFAULT_UNAVAILABLE_CRITICAL_S,
            )
        )
        self._stuck_job_s = float(
            _cfg_num(
                config, "watchdog_stuck_job_seconds",
                self.DEFAULT_STUCK_JOB_S,
            )
        )
        self._cancel_grace_s = float(
            _cfg_num(
                config, "watchdog_cancel_grace_seconds",
                self.DEFAULT_CANCEL_GRACE_S,
            )
        )
        self._service_failure_threshold = int(
            _cfg_num(
                config, "watchdog_service_failure_threshold",
                self.DEFAULT_SERVICE_FAILURE_THRESHOLD,
            )
        )
        self._lease_expiry_s = float(
            _cfg_num(
                config, "watchdog_lease_expiry_seconds",
                self.DEFAULT_LEASE_EXPIRY_S,
            )
        )
        self._signal_cooldown_s = float(
            _cfg_num(
                config, "watchdog_signal_cooldown_seconds",
                self.DEFAULT_SIGNAL_COOLDOWN_S,
            )
        )

        # Per-check runtime state (recreated by start()).
        self._loop_task: Optional[asyncio.Task[None]] = None
        self._stop_event = asyncio.Event()

        self._gpu_unavailable_since: Optional[float] = None
        self._cancel_requested: dict[str, float] = {}
        self._service_failures: dict[str, int] = {}
        self._lease_reported: set[str] = set()  # job_ids already reported
        self._signal_last_logged: dict[str, float] = {}
        self._halt_triggered_for: set[str] = set()  # halt reasons already acted on
        self._temperature_warn_active: bool = False
        self._temperature_cleared_at: Optional[float] = None

        self._last_signals: list[HealthSignal] = []
        self._last_run_at: Optional[float] = None
        self._run_count: int = 0

        if self._temp_warn_c >= self._temp_ceiling_c:
            LOG.warning(
                "watchdog_temperature_warn_c (%.1f) >= ceiling (%.1f); "
                "warn-level temperature alerts will not fire",
                self._temp_warn_c, self._temp_ceiling_c,
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        if self._loop_task is not None:
            raise RuntimeError("watchdog already started")
        self._stop_event.clear()
        self._loop_task = asyncio.create_task(
            self._loop(), name="banana-brain-watchdog"
        )
        LOG.info(
            "watchdog ready (interval=%.0fs, temp warn=%.0f°C ceiling=%.0f°C, "
            "stuck_job=%.0fs, lease_expiry=%.0fs)",
            self._check_interval, self._temp_warn_c, self._temp_ceiling_c,
            self._stuck_job_s, self._lease_expiry_s,
        )

    async def stop(self) -> None:
        self._stop_event.set()
        task = self._loop_task
        self._loop_task = None
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        LOG.info(
            "watchdog stopped after %d check(s); last run %.1fs ago",
            self._run_count,
            (
                round(time.time() - self._last_run_at, 1)
                if self._last_run_at is not None
                else 0.0
            ),
        )

    # ------------------------------------------------------------------
    # Public test/diagnostic API
    # ------------------------------------------------------------------

    async def run_once(self) -> list[HealthSignal]:
        """
        Run every check once and return the signals.

        Public so tests and the CLI's ``watchdog check`` can invoke the
        watchdog synchronously without starting the loop.
        """
        signals: list[HealthSignal] = []
        for check in (
            self._check_gpu_visibility,
            self._check_temperature,
            self._check_stuck_job,
            self._check_services,
            self._check_reservations,
        ):
            try:
                produced = await check()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOG.exception("watchdog check %s raised", check.__name__)
                produced = [
                    HealthSignal(
                        name=check.__name__,
                        severity=Severity.ERROR,
                        message="check raised an unexpected exception",
                        key=f"check_error:{check.__name__}",
                    )
                ]
            signals.extend(produced)

        await self._handle_signals(signals)
        self._last_signals = signals
        self._last_run_at = time.time()
        self._run_count += 1
        return signals

    async def snapshot(self) -> dict[str, Any]:
        """Diagnostic view for the API's /health endpoint."""
        return {
            "running": self._loop_task is not None,
            "last_run_at": self._last_run_at,
            "run_count": self._run_count,
            "check_interval_s": self._check_interval,
            "signals": [
                {
                    "name": s.name,
                    "severity": s.severity.label(),
                    "message": s.message,
                    "key": s.key,
                    "details": s.details,
                    "action": s.action,
                }
                for s in self._last_signals
            ],
            "gpu_unavailable_since": self._gpu_unavailable_since,
            "cancel_requested": sorted(self._cancel_requested.keys()),
            "service_failures": dict(self._service_failures),
            "halt_triggered_for": sorted(self._halt_triggered_for),
        }

    async def acknowledge(self, signal_key: str) -> None:
        """
        Suppress a specific signal for one cooldown period.

        Used by the CLI (``watchdog ack <key>``) to silence a known,
        operator-accepted warning without clearing its underlying cause.
        """
        self._signal_last_logged[signal_key] = time.monotonic()
        LOG.info("watchdog: signal %r acknowledged by operator", signal_key)

    # ------------------------------------------------------------------
    # Loop
    # ------------------------------------------------------------------

    async def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await self.run_once()
            except asyncio.CancelledError:
                raise
            except Exception:
                LOG.exception("watchdog iteration failed; continuing")

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=self._check_interval
                )
            except asyncio.TimeoutError:
                pass

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    async def _check_gpu_visibility(self) -> list[HealthSignal]:
        """
        Detect GPU-monitor staleness.

        A None GPUStatus is already "fail closed" for admission; the
        watchdog's job here is to escalate if the staleness persists past
        the critical threshold and trigger the safety overlay, because
        nothing can be safely admitted without memory visibility.
        """
        status = await self._gpu_monitor.get_status()
        now = time.monotonic()

        if status is not None:
            was_unavailable = self._gpu_unavailable_since is not None
            self._gpu_unavailable_since = None
            if was_unavailable:
                LOG.info("watchdog: GPU monitor visibility restored")
            return []

        if self._gpu_unavailable_since is None:
            self._gpu_unavailable_since = now

        duration = now - self._gpu_unavailable_since
        if duration >= self._unavailable_critical_s:
            key = "gpu_visibility_lost"
            action = await self._trigger_safety_halt(
                key,
                reason=(
                    f"GPU monitor unavailable for {duration:.0f}s "
                    f"(threshold {self._unavailable_critical_s:.0f}s)"
                ),
            )
            return [
                HealthSignal(
                    name="gpu_visibility",
                    severity=Severity.CRITICAL,
                    message=(
                        f"GPU monitor has been unavailable for {duration:.0f}s; "
                        f"cannot admit safely"
                    ),
                    key=key,
                    details={"duration_s": round(duration, 1)},
                    action=action,
                )
            ]

        if duration >= self._unavailable_warn_s:
            return [
                HealthSignal(
                    name="gpu_visibility",
                    severity=Severity.WARN,
                    message=f"GPU monitor unavailable for {duration:.0f}s",
                    key="gpu_visibility_stale",
                    details={"duration_s": round(duration, 1)},
                )
            ]

        return []

    async def _check_temperature(self) -> list[HealthSignal]:
        signals: list[HealthSignal] = []
        status = await self._gpu_monitor.get_status()
        if status is None:
            return signals  # covered by _check_gpu_visibility

        temp = status.temperature_c
        health = getattr(status, "health", None)

        if temp is not None and temp >= self._temp_ceiling_c:
            self._temperature_warn_active = False
            self._temperature_cleared_at = None
            key = f"temperature_ceiling:{int(self._temp_ceiling_c)}"
            action = await self._trigger_safety_halt(
                key,
                reason=(
                    f"GPU temperature {temp}°C exceeded ceiling "
                    f"{self._temp_ceiling_c:.0f}°C"
                ),
            )
            signals.append(
                HealthSignal(
                    name="temperature",
                    severity=Severity.CRITICAL,
                    message=(
                        f"GPU temperature {temp}°C "
                        f"at or above ceiling {self._temp_ceiling_c:.0f}°C"
                    ),
                    key=key,
                    details={
                        "temperature_c": temp,
                        "ceiling_c": self._temp_ceiling_c,
                    },
                    action=action,
                )
            )
        elif temp is not None and temp >= self._temp_warn_c:
            self._temperature_warn_active = True
            self._temperature_cleared_at = None
            signals.append(
                HealthSignal(
                    name="temperature",
                    severity=Severity.WARN,
                    message=(
                        f"GPU temperature {temp}°C "
                        f"above warn threshold {self._temp_warn_c:.0f}°C"
                    ),
                    key=f"temperature_warn:{int(self._temp_warn_c)}",
                    details={
                        "temperature_c": temp,
                        "warn_c": self._temp_warn_c,
                    },
                )
            )
        else:
            if self._temperature_warn_active:
                self._temperature_warn_active = False
                self._temperature_cleared_at = time.monotonic()
                LOG.info(
                    "watchdog: GPU temperature back below %.0f°C "
                    "(now %s°C)",
                    self._temp_warn_c, temp,
                )
            # If a thermal halt is still active, nudge the operator
            # that the underlying condition is gone. Never clear it here.
            if "temperature_ceiling" in self._halt_triggered_for:
                if self._temperature_cleared_at is None:
                    self._temperature_cleared_at = time.monotonic()
                if temp is not None and temp < self._temp_warn_c:
                    signals.append(
                        HealthSignal(
                            name="temperature",
                            severity=Severity.WARN,
                            message=(
                                f"GPU temperature now {temp}°C; safety halt "
                                f"remains engaged until operator clears it "
                                f"(banana-brain mode clear-halt)"
                            ),
                            key="temperature_clearable",
                            details={"temperature_c": temp},
                        )
                    )

        if health is not None:
            if getattr(health, "thermal_slowdown", False):
                signals.append(
                    HealthSignal(
                        name="temperature",
                        severity=Severity.WARN,
                        message="GPU is thermal-throttling",
                        key="thermal_slowdown",
                        details={"throttle_reasons": getattr(health, "throttle_reasons", 0)},
                    )
                )
            if getattr(health, "power_brake", False):
                signals.append(
                    HealthSignal(
                        name="temperature",
                        severity=Severity.WARN,
                        message="GPU power brake engaged; performance reduced",
                        key="power_brake",
                    )
                )
            if getattr(health, "device_lost", False):
                # Populated by future gpu_monitor versions.
                key = "device_lost"
                action = await self._trigger_safety_halt(
                    key, reason="GPU reported device lost to NVML"
                )
                signals.append(
                    HealthSignal(
                        name="device",
                        severity=Severity.CRITICAL,
                        message="GPU device lost (NVML)",
                        key=key,
                        action=action,
                    )
                )

        return signals

    async def _check_stuck_job(self) -> list[HealthSignal]:
        signals: list[HealthSignal] = []
        current = getattr(self._scheduler, "current_job", None)
        now = time.monotonic()

        # Clear tracking for jobs that are no longer current.
        if current is None:
            if self._cancel_requested:
                LOG.info(
                    "watchdog: current job cleared; releasing %d cancel "
                    "request(s)",
                    len(self._cancel_requested),
                )
                self._cancel_requested.clear()
            return signals

        started_at = getattr(current, "started_at", None)
        if started_at is None:
            return signals  # scheduler hasn't marked RUNNING yet; not stuck

        age = max(0.0, time.time() - float(started_at))
        job_id = str(current.id)

        if age < self._stuck_job_s:
            return signals

        already_cancelled = job_id in self._cancel_requested

        if not already_cancelled:
            cancel_ok = await self._request_cancel(job_id)
            if cancel_ok:
                self._cancel_requested[job_id] = now
            signals.append(
                HealthSignal(
                    name="stuck_job",
                    severity=Severity.ERROR,
                    message=(
                        f"job {job_id} has been running for {age:.0f}s "
                        f"(threshold {self._stuck_job_s:.0f}s); "
                        f"cancellation requested"
                    ),
                    key=f"stuck_job:{job_id}",
                    details={
                        "job_id": job_id,
                        "adapter": getattr(current, "adapter", None),
                        "age_s": round(age, 1),
                        "threshold_s": self._stuck_job_s,
                    },
                    action=(
                        "cancel_requested"
                        if cancel_ok
                        else "cancel_request_failed"
                    ),
                )
            )
            return signals

        cancel_age = now - self._cancel_requested[job_id]
        if cancel_age >= self._cancel_grace_s:
            signals.append(
                HealthSignal(
                    name="stuck_job",
                    severity=Severity.CRITICAL,
                    message=(
                        f"job {job_id} still running {cancel_age:.0f}s after "
                        f"cancellation request; adapter is not honouring "
                        f"the interrupt"
                    ),
                    key=f"stuck_job_uninterruptible:{job_id}",
                    details={
                        "job_id": job_id,
                        "adapter": getattr(current, "adapter", None),
                        "age_s": round(age, 1),
                        "cancel_age_s": round(cancel_age, 1),
                    },
                    action="operator_review_required",
                )
            )

        return signals

    async def _check_services(self) -> list[HealthSignal]:
        signals: list[HealthSignal] = []
        for name, adapter in self._adapters.items():
            probe = _resolve_probe(adapter)
            if probe is None:
                continue
            try:
                await probe()
                if self._service_failures.get(name, 0):
                    LOG.info(
                        "watchdog: service %s recovered", name
                    )
                self._service_failures[name] = 0
                continue
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                failures = self._service_failures.get(name, 0) + 1
                self._service_failures[name] = failures
                severity = (
                    Severity.ERROR
                    if failures >= self._service_failure_threshold
                    else Severity.WARN
                )
                signals.append(
                    HealthSignal(
                        name=f"service:{name}",
                        severity=severity,
                        message=(
                            f"adapter {name} probe failed ({failures}x): "
                            f"{type(exc).__name__}: {exc}"
                        ),
                        key=f"service_down:{name}",
                        details={
                            "adapter": name,
                            "consecutive_failures": failures,
                            "threshold": self._service_failure_threshold,
                        },
                    )
                )
        return signals

    async def _check_reservations(self) -> list[HealthSignal]:
        signals: list[HealthSignal] = []
        try:
            snapshot = await self._vram_manager.snapshot()
        except Exception:
            LOG.exception("watchdog: vram_manager.snapshot() raised")
            return signals

        reservations = snapshot.get("reservations") or []
        current = getattr(self._scheduler, "current_job", None)
        current_id = str(current.id) if current is not None else None

        live_ids: set[str] = set()
        for reservation in reservations:
            job_id = str(reservation.get("job_id") or "")
            if not job_id:
                continue
            live_ids.add(job_id)
            age = float(reservation.get("age_seconds") or 0.0)
            if age < self._lease_expiry_s:
                continue
            if job_id == current_id:
                continue  # legitimate long-running job; not a leak
            if job_id in self._lease_reported:
                continue
            self._lease_reported.add(job_id)
            signals.append(
                HealthSignal(
                    name="lease_expiry",
                    severity=Severity.ERROR,
                    message=(
                        f"VRAM reservation for job {job_id} has been held "
                        f"{age:.0f}s with no running job (threshold "
                        f"{self._lease_expiry_s:.0f}s); this indicates a "
                        f"leak in the scheduler's dispatch path"
                    ),
                    key=f"lease_expiry:{job_id}",
                    details={
                        "job_id": job_id,
                        "age_s": round(age, 1),
                        "bytes": reservation.get("bytes"),
                        "adapter": reservation.get("adapter"),
                        "state": reservation.get("state"),
                    },
                )
            )

        # Clean up the reported-set so a resubmitted job would be reported
        # again if it later leaks.
        self._lease_reported.intersection_update(live_ids)

        return signals

    # ------------------------------------------------------------------
    # Signal handling
    # ------------------------------------------------------------------

    async def _handle_signals(self, signals: list[HealthSignal]) -> None:
        """
        Deduplicate and dispatch signals to the log and notifications.

        Cooldown suppresses WARN-and-below signals by key so a persistent
        condition does not flood the log. ERROR and CRITICAL are always
        emitted: they represent actions taken or required, and silencing
        them would hide the fact that the watchdog did something.
        """
        now = time.monotonic()
        for signal in signals:
            if signal.severity <= Severity.WARN:
                last = self._signal_last_logged.get(signal.key)
                if last is not None and now - last < self._signal_cooldown_s:
                    continue
                self._signal_last_logged[signal.key] = now

            self._log_signal(signal)
            await self._notify(signal)

    def _log_signal(self, signal: HealthSignal) -> None:
        if signal.severity is Severity.CRITICAL:
            LOG.critical(
                "[%s] %s%s",
                signal.name, signal.message,
                f" (action={signal.action})" if signal.action else "",
            )
        elif signal.severity is Severity.ERROR:
            LOG.error(
                "[%s] %s%s",
                signal.name, signal.message,
                f" (action={signal.action})" if signal.action else "",
            )
        elif signal.severity is Severity.WARN:
            LOG.warning("[%s] %s", signal.name, signal.message)
        else:
            LOG.debug("[%s] %s", signal.name, signal.message)

    async def _notify(self, signal: HealthSignal) -> None:
        if self._notifications is None:
            return
        if signal.severity < Severity.ERROR:
            return
        notifier = getattr(self._notifications, "notify", None)
        if not callable(notifier):
            return
        try:
            await notifier(
                level=signal.severity.label().lower(),
                title=signal.name,
                message=signal.message,
                details=signal.details,
            )
        except Exception:
            LOG.exception("watchdog: notification failed for %s", signal.key)

    # ------------------------------------------------------------------
    # Escalation
    # ------------------------------------------------------------------

    async def _trigger_safety_halt(
        self, key: str, *, reason: str
    ) -> Optional[str]:
        """
        Engage the safety overlay once per `key`.

        Returns a short action description for the signal, or None if no
        mode manager is available (in which case the signal is still
        produced but no halt is attempted).
        """
        if key in self._halt_triggered_for:
            return "halt_already_engaged"
        if self._mode_manager is None:
            LOG.error(
                "watchdog: CRITICAL condition but no mode manager wired; "
                "cannot engage safety halt: %s", reason,
            )
            return "no_mode_manager"

        halt = getattr(self._mode_manager, "force_safety_halt", None)
        if not callable(halt):
            LOG.error(
                "watchdog: mode manager has no force_safety_halt(); "
                "cannot halt: %s", reason,
            )
            return "mode_manager_api_missing"

        try:
            await halt(reason)
        except Exception:
            LOG.exception("watchdog: force_safety_halt raised")
            return "halt_failed"

        self._halt_triggered_for.add(key)
        LOG.critical(
            "watchdog: safety halt engaged (%s): %s", key, reason
        )
        return "safety_halt_engaged"

    # ------------------------------------------------------------------
    # Cancellation helper
    # ------------------------------------------------------------------

    async def _request_cancel(self, job_id: str) -> bool:
        try:
            return bool(
                await self._scheduler.cancel(job_id, force=True)
            )
        except Exception:
            LOG.exception(
                "watchdog: failed to request cancel for job %s", job_id
            )
            return False


# ---------------------------------------------------------------------------
# Probe resolution
# ---------------------------------------------------------------------------

def _resolve_probe(adapter: Any) -> Optional[Any]:
    """
    Prefer a public ``probe()`` method. Fall back to the private
    ``_probe()`` / ``_probe_stt()`` methods that the current adapters
    implement, so the watchdog works today without adapter changes.

    The fallback is documented as fragile: adapters should add a public
    ``probe()`` for the next minor version.
    """
    if adapter is None:
        return None
    probe = getattr(adapter, "probe", None)
    if callable(probe):
        return probe
    for candidate in ("_probe", "_probe_stt"):
        fallback = getattr(adapter, candidate, None)
        if callable(fallback):
            return fallback
    return None


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _cfg_get(config: Any, name: str) -> Any:
    if isinstance(config, dict):
        return config.get(name)
    return getattr(config, name, None)


def _cfg_num(config: Any, name: str, default: float) -> float:
    value = _cfg_get(config, name)
    return float(value) if isinstance(value, (int, float)) else default