"""
banana_brain.gpu_modes — explicit GPU operating modes.

Responsibilities (from the Banana Brain design doc):
  * Provide the AI / image / mixed / maintenance / manual-gaming modes.
  * Gate dispatch admission so that exclusive modes actually exclude work.
  * Suspend queued jobs during exclusive modes and resume them on exit.
  * Cooperatively unload models when entering an exclusive mode.
  * Persist the current mode so a restart resumes the operator's intent.
  * Provide a safety overlay that survives across mode changes so a
    thermal event does not also silently overwrite the operator's mode.

Public API:

  async start()                                    -> None
  async stop()                                     -> None
  @property current_mode                           -> GPUMode
  @property safety_halted                          -> bool
  def       is_admission_allowed(job)              -> bool  (called by scheduler)
  async set_mode(target, *, reason, ...)           -> ModeTransitionResult
  async resume_previous(*, reason, ...)            -> ModeTransitionResult
  async get_state()                                -> dict
  async force_safety_halt(reason)                  -> None  (called by watchdog)
  async clear_safety_halt(*, reason, cleared_by)   -> None  (operator action)
  async cancel_suspended(job_id)                   -> bool
  async get_suspended()                            -> list[dict]

Lifecycle (called by the composition root):
  async start()
  async stop()

Integration with the scheduler:

  * In start(), installs a callback via scheduler.set_admission_checker().
    This requires a small additive patch to Scheduler (documented below).
  * Wakes the scheduler after every mode change via
    scheduler.request_dispatch() (or scheduler._wake.set() as a fallback).
  * Reads scheduler.current_job to wait for in-flight work.

The suspended-jobs mechanism requires that priority_manager operations be
idempotent by job id. PriorityManager already provides that via its
pop-by-id `remove()` and dict-keyed storage.

Configuration fields consumed:

  mode_default: str                     default "mixed"
  mode_persistence_enabled: bool        default true
  mode_state_path: Path                 default "data/banana-brain.mode.json"
  mode_transition_timeout_s: float      default 300.0
  mode_drain_interval_s: float          default 5.0

  shutdown_grace_seconds: float         reused for stop() drain

Dependencies:
  scheduler          .current_job, .cancel, .request_dispatch / ._wake
  priority_manager   .peek, .push, .remove, .size
  job_store          .save, .get
  adapters           .unload_idle_models(needed_bytes)  [optional per-adapter]
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .job_models import Job, JobState, Priority

__all__ = [
    "GPUMode",
    "GPUModeManager",
    "ModeTransitionError",
    "ModeTransitionResult",
    "ModeTransitionTimeout",
]

LOG = logging.getLogger("banana_brain.gpu_modes")

GIB = 1024**3

#: Passed to adapters' unload_idle_models() to mean "free as much as you can".
_UNLOAD_ALL_BYTES = 1024 * GIB  # larger than any single GPU's VRAM


# ---------------------------------------------------------------------------
# Mode enum and results
# ---------------------------------------------------------------------------


class GPUMode(StrEnum):
    """Operator-facing GPU modes. Order matches the design doc's priority ladder."""

    AI = "ai"  # LLM-focused: Ollama / PyGPT workloads
    IMAGE = "image"  # Image-generation-focused: ComfyUI
    MIXED = "mixed"  # Default: everything, priority-ordered
    MAINTENANCE = "maintenance"  # Operator-exclusive; benchmark/repair jobs only
    GAMING = "gaming"  # Manual exclusive; no scheduled work

    def is_exclusive(self) -> bool:
        return self in (GPUMode.MAINTENANCE, GPUMode.GAMING)


@dataclass(frozen=True)
class ModeTransitionResult:
    success: bool
    from_mode: GPUMode
    to_mode: GPUMode
    reason: str
    requested_by: str | None
    elapsed_s: float
    interrupted_job_id: str | None = None
    suspended_count: int = 0
    error: str | None = None


class ModeTransitionError(RuntimeError):
    """Base class for mode transition failures."""


class ModeTransitionTimeout(ModeTransitionError):
    """Raised internally when waiting for in-flight jobs exceeds the timeout."""


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class GPUModeManager:
    """
    Manages the current GPU mode, its admission rules, and its suspended queue.

    All set_mode calls are serialised through an asyncio.Lock; concurrent
    transitions are queued and applied in order. Read-only queries
    (current_mode, is_admission_allowed, get_state) are lock-free.
    """

    def __init__(
        self,
        config: Any,
        *,
        scheduler: Any,
        priority_manager: Any,
        job_store: Any,
        adapters: dict[str, Any],
    ) -> None:
        self._config = config
        self._scheduler = scheduler
        self._priority_manager = priority_manager
        self._job_store = job_store
        self._adapters = dict(adapters or {})

        self._default_mode = _parse_mode(
            _cfg_str(config, "mode_default") or GPUMode.MIXED.value
        )
        self._persistence_enabled = _cfg_bool(config, "mode_persistence_enabled", True)
        state_path = _cfg_str(config, "mode_state_path")
        self._state_path = Path(
            state_path or "data/banana-brain.mode.json"
        ).expanduser()
        self._transition_timeout = float(
            _cfg_num(config, "mode_transition_timeout_s", 300.0)
        )
        self._drain_interval = float(_cfg_num(config, "mode_drain_interval_s", 5.0))

        self._current_mode: GPUMode = self._default_mode
        self._previous_non_exclusive: GPUMode = self._default_mode
        self._mode_since: float = time.time()
        self._mode_reason: str = "initial default"
        self._mode_requested_by: str | None = None

        self._safety_halted: bool = False
        self._safety_halt_reason: str | None = None

        self._suspended_jobs: list[Job] = []
        self._transition_lock = asyncio.Lock()
        self._housekeeping_task: asyncio.Task[None] | None = None
        self._housekeeping_stop = asyncio.Event()
        self._admission_installed: bool = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        persisted = self._load_persisted_state()
        if persisted is not None:
            self._current_mode = _parse_mode(
                persisted.get("mode", self._default_mode.value)
            )
            self._mode_since = float(persisted.get("since", time.time()))
            self._mode_reason = str(persisted.get("reason") or "restored from disk")
            self._mode_requested_by = _maybe_str(persisted.get("requested_by"))
            if self._current_mode not in (GPUMode.MAINTENANCE, GPUMode.GAMING):
                self._previous_non_exclusive = self._current_mode
            else:
                prev = persisted.get("previous_non_exclusive_mode")
                if prev:
                    self._previous_non_exclusive = _parse_mode(prev)

        self._admission_installed = self._install_admission_check()
        self._housekeeping_task = asyncio.create_task(
            self._housekeeping_loop(), name="banana-brain-gpu-modes-housekeeping"
        )
        LOG.info(
            "gpu_modes ready: mode=%s (persisted=%s, admission_check=%s, "
            "transition_timeout=%.0fs)",
            self._current_mode.value,
            "yes" if persisted is not None else "no",
            "installed" if self._admission_installed else "unavailable",
            self._transition_timeout,
        )

    async def stop(self) -> None:
        self._housekeeping_stop.set()
        if self._housekeeping_task is not None:
            self._housekeeping_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._housekeeping_task
            self._housekeeping_task = None

        if self._admission_installed:
            setter = getattr(self._scheduler, "set_admission_checker", None)
            if callable(setter):
                try:
                    setter(None)
                except Exception:
                    LOG.debug("could not uninstall admission check", exc_info=True)

        # Persist current mode so the next startup resumes it.
        self._save_persisted_state()
        LOG.info("gpu_modes stopped (final mode=%s)", self._current_mode.value)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_mode(self) -> GPUMode:
        return self._current_mode

    @property
    def safety_halted(self) -> bool:
        return self._safety_halted

    # ------------------------------------------------------------------
    # Admission (called by scheduler)
    # ------------------------------------------------------------------

    def is_admission_allowed(self, job: Job) -> bool:
        """
        Return True iff `job` may be dispatched in the current mode.

        This must be fast (no I/O, no awaits): the scheduler calls it in
        the dispatch hot path. All state it reads is set by set_mode()
        and force_safety_halt(), both of which run in the same loop.
        """
        if self._safety_halted:
            return False
        mode = self._current_mode
        if mode is GPUMode.GAMING:
            return False
        if mode is GPUMode.MAINTENANCE:
            return self._is_maintenance_workload(job)
        # AI, IMAGE, MIXED: everything is allowed; the priority ladder
        # provides ordering without needing a gate.
        return True

    # ------------------------------------------------------------------
    # Mode transitions
    # ------------------------------------------------------------------

    async def set_mode(
        self,
        target: GPUMode | str,
        *,
        reason: str,
        requested_by: str | None = None,
        force: bool = False,
        timeout: float | None = None,
    ) -> ModeTransitionResult:
        """
        Transition to `target`, waiting for in-flight work when required.

        Parameters:
          reason         free-form, recorded in the transition log
          requested_by   caller identity (CLI user, API client, "watchdog")
          force          if True, request cancellation of the current job
                         before waiting; otherwise wait for it to finish
          timeout        seconds to wait for the current job; default from
                         config (mode_transition_timeout_s)

        Entering GAMING or MAINTENANCE:
          1. Wait for the current job to finish (or request cancel if force).
          2. Drain non-matching jobs from the priority queue into suspension.
          3. Ask all adapters to unload idle models.
          4. Wake the scheduler so any matching jobs (maintenance only) can run.

        Leaving GAMING or MAINTENANCE:
          1. Re-push suspended jobs to the priority queue.
          2. Wake the scheduler.

        No-op if target == current_mode; returns success with elapsed_s=0.
        Concurrent calls are serialised by an asyncio.Lock.
        """
        target_mode = _parse_mode(target)
        wait_budget = self._transition_timeout if timeout is None else float(timeout)

        async with self._transition_lock:
            started = time.monotonic()
            from_mode = self._current_mode

            if target_mode is from_mode:
                return ModeTransitionResult(
                    success=True,
                    from_mode=from_mode,
                    to_mode=target_mode,
                    reason=reason,
                    requested_by=requested_by,
                    elapsed_s=0.0,
                )

            if self._safety_halted:
                LOG.warning(
                    "set_mode(%s) called while safety_halted; the halt overlay "
                    "remains active — is_admission_allowed() will still refuse "
                    "everything until clear_safety_halt() is called",
                    target_mode.value,
                )

            LOG.info(
                "mode transition: %s -> %s (reason=%r, by=%r, force=%s)",
                from_mode.value,
                target_mode.value,
                reason,
                requested_by,
                force,
            )

            interrupted_job_id: str | None = None
            suspended_count = 0

            if target_mode.is_exclusive():
                interrupted_job_id = await self._await_current_job(
                    wait_budget, force=force
                )
                if interrupted_job_id is not None:
                    LOG.warning(
                        "mode transition: job %s still running after %.0fs; "
                        "operator must resolve it manually",
                        interrupted_job_id,
                        wait_budget,
                    )

            # Commit the mode before draining, so admission checks during
            # the drain agree with the new intent.
            self._current_mode = target_mode
            self._mode_since = time.time()
            self._mode_reason = reason
            self._mode_requested_by = requested_by
            if not target_mode.is_exclusive():
                self._previous_non_exclusive = target_mode

            if target_mode.is_exclusive():
                suspended_count = await self._suspend_non_matching()
                await self._unload_all_adapters()
            else:
                resumed = await self._resume_all_suspended()
                if resumed:
                    LOG.info("mode transition: resumed %d suspended job(s)", resumed)

            self._save_persisted_state()
            self._wake_scheduler()

            return ModeTransitionResult(
                success=interrupted_job_id is None,
                from_mode=from_mode,
                to_mode=target_mode,
                reason=reason,
                requested_by=requested_by,
                elapsed_s=round(time.monotonic() - started, 3),
                interrupted_job_id=interrupted_job_id,
                suspended_count=suspended_count,
                error=(
                    f"job {interrupted_job_id} still running after {wait_budget:.0f}s"
                    if interrupted_job_id is not None
                    else None
                ),
            )

    async def resume_previous(
        self,
        *,
        reason: str = "resume previous non-exclusive mode",
        requested_by: str | None = None,
    ) -> ModeTransitionResult:
        """
        Exit an exclusive mode by returning to the most recent non-exclusive
        mode (or the configured default if none). Convenience for the CLI's
        ``banana-brain mode resume``.
        """
        return await self.set_mode(
            self._previous_non_exclusive,
            reason=reason,
            requested_by=requested_by,
        )

    # ------------------------------------------------------------------
    # Safety overlay
    # ------------------------------------------------------------------

    async def force_safety_halt(self, reason: str) -> None:
        """
        Enter the safety overlay. Called by the watchdog on thermal events.

        Refuses all admissions (existing behaviour of the current mode is
        preserved for when the halt is cleared). Suspends every queued job
        so that clearing the halt is enough to resume normal operation.
        """
        if self._safety_halted:
            LOG.warning(
                "force_safety_halt called again while already halted: %s", reason
            )
            return
        self._safety_halted = True
        self._safety_halt_reason = reason
        LOG.error("safety halt engaged: %s", reason)

        self._wake_scheduler()
        try:
            suspended = await self._suspend_non_matching()
            if suspended:
                LOG.info("safety halt: suspended %d queued job(s)", suspended)
        except Exception:
            LOG.exception("safety halt: failed to suspend queue")

    async def clear_safety_halt(
        self, *, reason: str, cleared_by: str | None = None
    ) -> None:
        """Clear the safety overlay and resume normal operation."""
        if not self._safety_halted:
            LOG.info("clear_safety_halt called while not halted; ignoring")
            return
        self._safety_halted = False
        self._safety_halt_reason = None
        LOG.warning(
            "safety halt cleared by %s: %s",
            cleared_by or "<unknown>",
            reason,
        )
        try:
            resumed = await self._resume_all_suspended()
            if resumed:
                LOG.info("safety halt cleared: resumed %d job(s)", resumed)
        except Exception:
            LOG.exception("clear_safety_halt: failed to resume queue")
        self._wake_scheduler()

    # ------------------------------------------------------------------
    # Suspended-job management
    # ------------------------------------------------------------------

    async def cancel_suspended(self, job_id: str) -> bool:
        """
        Cancel a job that is currently in the suspended list.

        The scheduler's cancel() cannot reach these jobs because they are
        not in priority_manager. This method is the supported way to
        cancel them; the CLI and API should call it in addition to (or
        instead of) scheduler.cancel().
        """
        for index, job in enumerate(self._suspended_jobs):
            if job.id == job_id:
                job.state = JobState.CANCELLED
                job.finished_at = time.time()
                del self._suspended_jobs[index]
                try:
                    await self._job_store.save(job)
                except Exception:
                    LOG.exception(
                        "cancel_suspended: failed to persist cancellation for %s",
                        job_id,
                    )
                LOG.info("cancelled suspended job %s", job_id)
                return True
        return False

    async def get_suspended(self) -> list[dict[str, Any]]:
        return [
            {
                "id": job.id,
                "adapter": job.adapter,
                "priority": int(job.priority),
                "state": job.state.value,
                "submitted_at": job.submitted_at,
                "age_seconds": (
                    round(time.time() - job.submitted_at, 1)
                    if job.submitted_at is not None
                    else None
                ),
                "exclusive": bool(getattr(job, "exclusive", False)),
            }
            for job in self._suspended_jobs
        ]

    # ------------------------------------------------------------------
    # State for API / CLI
    # ------------------------------------------------------------------

    async def get_state(self) -> dict[str, Any]:
        current = getattr(self._scheduler, "current_job", None)
        return {
            "mode": self._current_mode.value,
            "safety_halted": self._safety_halted,
            "safety_halt_reason": self._safety_halt_reason,
            "mode_since": self._mode_since,
            "mode_age_seconds": round(time.time() - self._mode_since, 1),
            "mode_reason": self._mode_reason,
            "mode_requested_by": self._mode_requested_by,
            "previous_non_exclusive_mode": self._previous_non_exclusive.value,
            "suspended_jobs": len(self._suspended_jobs),
            "current_job_id": current.id if current is not None else None,
            "available_modes": [m.value for m in GPUMode],
            "admission_check_installed": self._admission_installed,
        }

    # ------------------------------------------------------------------
    # Internal: admission installation
    # ------------------------------------------------------------------

    def _install_admission_check(self) -> bool:
        setter = getattr(self._scheduler, "set_admission_checker", None)
        if not callable(setter):
            LOG.warning(
                "scheduler does not implement set_admission_checker(); "
                "mode gating will only work via queue suspension. "
                "Add Scheduler.set_admission_checker() to enable full gating."
            )
            return False
        try:
            setter(self.is_admission_allowed)
            return True
        except Exception:
            LOG.exception("failed to install admission check on scheduler")
            return False

    def _wake_scheduler(self) -> None:
        wake = getattr(self._scheduler, "request_dispatch", None)
        if callable(wake):
            try:
                wake()
                return
            except Exception:
                LOG.debug("scheduler.request_dispatch raised", exc_info=True)
        event = getattr(self._scheduler, "_wake", None)
        if event is not None and hasattr(event, "set"):
            event.set()
            return
        LOG.debug("could not wake scheduler; no public dispatch API available")

    # ------------------------------------------------------------------
    # Internal: waiting for current job
    # ------------------------------------------------------------------

    async def _await_current_job(self, timeout: float, *, force: bool) -> str | None:
        """
        Wait for scheduler.current_job to become None.

        Returns None on success, or the interrupted job's id on timeout.
        If force=True, requests cancellation of the current job first.
        """
        current = getattr(self._scheduler, "current_job", None)
        if current is None:
            return None

        if force:
            try:
                await self._scheduler.cancel(current.id, force=True)
                LOG.info(
                    "mode transition: requested cancellation of job %s",
                    current.id,
                )
            except Exception:
                LOG.exception(
                    "mode transition: failed to request cancellation of job %s",
                    current.id,
                )

        deadline = time.monotonic() + timeout
        while True:
            current = getattr(self._scheduler, "current_job", None)
            if current is None:
                return None
            if time.monotonic() >= deadline:
                return current.id
            await asyncio.sleep(0.25)

    # ------------------------------------------------------------------
    # Internal: queue suspension
    # ------------------------------------------------------------------

    async def _suspend_non_matching(self) -> int:
        """
        Drain the priority queue; keep allowed jobs, hold the rest.

        Idempotent with respect to the priority manager's id-keyed storage:
        a job that races with the scheduler's peek/remove is simply not
        re-pushed (the scheduler's "job vanished" path handles it).

        Returns the count of jobs that were moved into suspension.
        """
        to_keep: list[Job] = []
        to_suspend: list[Job] = []

        while True:
            job = await self._priority_manager.peek()
            if job is None:
                break
            removed = await self._priority_manager.remove(job.id)
            if removed is None:
                # Scheduler beat us to it; nothing to do.
                continue
            if self.is_admission_allowed(removed):
                to_keep.append(removed)
            else:
                to_suspend.append(removed)

        for job in to_keep:
            try:
                await self._priority_manager.push(job)
            except Exception:
                LOG.exception(
                    "failed to re-push allowed job %s during suspension",
                    job.id,
                )

        if to_suspend:
            self._suspended_jobs.extend(to_suspend)
            LOG.info(
                "suspended %d job(s) during exclusive-mode entry " "(%d kept in queue)",
                len(to_suspend),
                len(to_keep),
            )
        return len(to_suspend)

    async def _resume_all_suspended(self) -> int:
        """
        Re-push every suspended job. Drops any that have become terminal in
        the meantime (cancelled via cancel_suspended, or via the store).
        """
        if not self._suspended_jobs:
            return 0

        still_pending: list[Job] = []
        dropped = 0
        for job in self._suspended_jobs:
            try:
                fresh = await self._job_store.get(job.id)
            except Exception:
                LOG.exception(
                    "resume: could not reload job %s from store; dropping",
                    job.id,
                )
                dropped += 1
                continue
            if fresh is None or fresh.state.is_terminal:
                dropped += 1
                continue
            still_pending.append(fresh)

        self._suspended_jobs = []
        if dropped:
            LOG.info("resume: dropped %d terminal suspended job(s)", dropped)

        resumed = 0
        for job in still_pending:
            try:
                await self._priority_manager.push(job)
                resumed += 1
            except Exception:
                LOG.exception(
                    "failed to resume suspended job %s; leaving in job_store",
                    job.id,
                )
        return resumed

    # ------------------------------------------------------------------
    # Internal: adapters
    # ------------------------------------------------------------------

    async def _unload_all_adapters(self) -> None:
        """
        Ask every adapter to release idle models. Best-effort: failures are
        logged and do not abort the mode transition.

        The byte count is a bound larger than any GPU, which adapters
        interpret as "free as much as you can." The scheduler's own
        _free_memory_for path uses gpu_monitor to confirm real release;
        this is the same cooperative model applied on mode entry.
        """
        for name, adapter in self._adapters.items():
            unload = getattr(adapter, "unload_idle_models", None)
            if not callable(unload):
                continue
            try:
                freed = await unload(_UNLOAD_ALL_BYTES)
                if freed:
                    LOG.info(
                        "mode transition: adapter %s released %d bytes",
                        name,
                        freed,
                    )
            except Exception:
                LOG.exception("mode transition: adapter %s unload raised", name)

    # ------------------------------------------------------------------
    # Internal: housekeeping
    # ------------------------------------------------------------------

    async def _housekeeping_loop(self) -> None:
        """
        Periodically re-drain non-matching jobs during exclusive modes.

        The immediate drain in set_mode() covers the common case; this
        loop covers jobs submitted *during* an exclusive mode, which the
        scheduler accepts (queue-then-block) and which would otherwise
        remain at the queue head until the next transition. Drain is
        quick — typically an empty queue — and only runs in exclusive
        modes or during safety halt.
        """
        while not self._housekeeping_stop.is_set():
            try:
                await asyncio.wait_for(
                    self._housekeeping_stop.wait(),
                    timeout=self._drain_interval,
                )
                # stop event was set; exit
                return
            except TimeoutError:
                pass
            if not (self._current_mode.is_exclusive() or self._safety_halted):
                continue
            try:
                await self._suspend_non_matching()
            except Exception:
                LOG.exception("housekeeping drain failed; will retry")

    # ------------------------------------------------------------------
    # Internal: persistence
    # ------------------------------------------------------------------

    def _load_persisted_state(self) -> dict[str, Any] | None:
        if not self._persistence_enabled:
            return None
        path = self._state_path
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            LOG.warning(
                "could not parse persisted mode state from %s; using default",
                path,
                exc_info=True,
            )
            return None
        if not isinstance(data, dict):
            return None
        return data

    def _save_persisted_state(self) -> None:
        if not self._persistence_enabled:
            return
        path = self._state_path
        tmp = path.with_suffix(path.suffix + ".tmp")
        data = {
            "mode": self._current_mode.value,
            "since": self._mode_since,
            "reason": self._mode_reason,
            "requested_by": self._mode_requested_by,
            "previous_non_exclusive_mode": self._previous_non_exclusive.value,
        }
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
            os.replace(tmp, path)
        except Exception:
            LOG.exception("failed to persist mode state to %s", path)

    # ------------------------------------------------------------------
    # Internal: predicates
    # ------------------------------------------------------------------

    @staticmethod
    def _is_maintenance_workload(job: Job) -> bool:
        if bool(getattr(job, "exclusive", False)):
            return True
        try:
            priority = int(getattr(job, "priority", 0))
        except (TypeError, ValueError):
            priority = 0
        if priority >= int(Priority.EXCLUSIVE):
            return True
        tags = getattr(job, "tags", {}) or {}
        return bool(tags.get("maintenance"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_mode(value: Any) -> GPUMode:
    if isinstance(value, GPUMode):
        return value
    try:
        return GPUMode(str(value).strip().lower())
    except (ValueError, AttributeError) as exc:
        raise ModeTransitionError(
            f"unknown GPU mode {value!r}; valid modes: "
            f"{', '.join(m.value for m in GPUMode)}"
        ) from exc


def _maybe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


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
