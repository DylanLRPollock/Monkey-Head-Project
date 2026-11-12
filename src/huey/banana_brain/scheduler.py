"""
banana_brain.scheduler — central GPU scheduler.

Responsibilities (from the Banana Brain design doc):
  * Accept jobs from the API, adapters, and recovery.
  * Order them through the priority manager.
  * Ask the VRAM manager to reserve memory, unload idle models when needed,
    and confirm the reservation before dispatching.
  * Run exactly one GPU job at a time on the V100.
  * Persist every state transition through the job store.
  * Drain cleanly on shutdown; running jobs finish, pending jobs persist.

Public API (all methods must be called from the asyncio event loop):
  submit(job)                       -> Job       persist + enqueue
  cancel(job_id, force=False)       -> bool      cancel a pending or running job
  begin_shutdown()                  -> None      stop admitting new work
  wait_for_idle()                   -> None      resolves when nothing is running
  wait_until_empty(timeout)         -> bool      test/admin helper
  status()                          -> dict      snapshot for the API

Lifecycle (called by banana-brain_scheduler.py):
  async start()
  async stop()

Contracts expected from dependencies (duck-typed):

  job_store:
      async save(job)
      async list_by_state(states: set[str]) -> list[Job]

  gpu_monitor:
      async get_status() -> GPUStatus | None
          GPUStatus.total_vram_bytes: int
          GPUStatus.free_vram_bytes:  int

  vram_manager:
      async try_reserve(job, bytes: int) -> bool
      def   release(job) -> None

  priority_manager:
      async push(job)
      async peek() -> Job | None
      async remove(job_id: str) -> Job | None
      async size() -> int
      def   default_priority(job) -> int  # optional

  adapter (ollama_adapter, comfyui_adapter, ...):
      async execute(job) -> result
      async unload_idle_models(needed_bytes: int) -> int
      # optional:
      async estimate_vram(job) -> int
      async request_cancel(job) -> bool

A Job object (provided by job_models) must expose:
  id, adapter, payload, priority, state,
  submitted_at, started_at, finished_at,
  attempts, last_error, result,
  estimated_vram_bytes (optional), owner (optional)
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from .job_models import JobState

__all__ = [
    "JobNotCancellable",
    "JobState",
    "Scheduler",
    "SchedulerError",
    "SchedulerShuttingDown",
]

LOG = logging.getLogger("banana_brain.scheduler")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SchedulerError(Exception):
    """Base class for scheduler errors."""


class SchedulerShuttingDown(SchedulerError):
    """Raised by submit() while shutdown is in progress."""


class JobNotCancellable(SchedulerError):
    """Raised by cancel() when a running job is not force-cancellable."""


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


class Scheduler:
    """
    Central GPU job scheduler.

    Exactly one job runs at a time. Admission is driven by a single dispatch
    loop; submit() and cancel() only mutate queue state and wake the loop.
    """

    #: How often the dispatch loop re-checks admission when no wake arrives.
    #: This covers the case where memory becomes available due to an external
    #: process exiting (which no adapter would signal us about).
    REFRESH_INTERVAL_S = 5.0

    #: Default VRAM estimate when neither the job nor the adapter provides one.
    DEFAULT_VRAM_ESTIMATE_BYTES = 8 * 1024**3

    #: Used by wait_until_empty / stop() to bound the dispatch task join.
    DISPATCH_TASK_JOIN_S = 5.0

    def __init__(
        self,
        *,
        config: Any,
        job_store: Any,
        gpu_monitor: Any,
        vram_manager: Any,
        priority_manager: Any,
        adapters: dict[str, Any],
    ) -> None:
        self._config = config
        self._job_store = job_store
        self._gpu_monitor = gpu_monitor
        self._vram_manager = vram_manager
        self._priority_manager = priority_manager
        self._adapters = dict(adapters)

        self._dispatch_task: asyncio.Task[None] | None = None
        self._wake = asyncio.Event()
        self._idle = asyncio.Event()
        self._idle.set()  # idle until the loop starts
        self._shutting_down = False
        self._current_job: Any | None = None
        self._admission_checker: Callable[[Any], bool] | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """
        Recover unfinished work, then start the dispatch loop.

        Recovery policy:
          * PENDING jobs are re-enqueued as-is.
          * RUNNING jobs from the previous process are treated as PENDING.
            Their `attempts` counter is preserved (>= 1) so adapters can
            detect a retry and check idempotency against their backend
            (Ollama: no history, so adapters must dedupe by job.id if they
             need to; ComfyUI: consult /history/{prompt_id}).
          * Jobs whose adapter is unknown (config changed) are marked
            FAILED with a clear last_error and not re-enqueued.
          * Terminal jobs are left untouched.
        """
        if self._dispatch_task is not None:
            raise SchedulerError("scheduler already started")

        await self._recover_unfinished()
        self._idle.clear()
        self._dispatch_task = asyncio.create_task(
            self._dispatch_loop(), name="banana-brain-dispatch"
        )
        pending = await self._priority_manager.size()
        LOG.info("scheduler started (pending=%d)", pending)

    async def stop(self) -> None:
        """Initiate shutdown, wait for the loop to exit, join the task."""
        self.begin_shutdown()
        await self.wait_for_idle()

        task = self._dispatch_task
        if task is None:
            return
        try:
            await asyncio.wait_for(task, timeout=self.DISPATCH_TASK_JOIN_S)
        except TimeoutError:
            LOG.warning("dispatch loop did not exit; cancelling")
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        finally:
            self._dispatch_task = None
        LOG.info("scheduler stopped")

    def begin_shutdown(self) -> None:
        """Stop admitting new jobs. Existing jobs run to a safe completion."""
        if self._shutting_down:
            return
        LOG.info("scheduler shutting down: no new jobs will be admitted")
        self._shutting_down = True
        self._wake.set()

    async def wait_for_idle(self) -> None:
        """Resolve when the dispatch loop has exited and no job is running."""
        await self._idle.wait()

    async def wait_until_empty(self, timeout: float | None = None) -> bool:
        """
        Wait until the queue is empty and no job is running, without
        initiating shutdown. Returns True if it became empty in time.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            if self._current_job is None and await self._priority_manager.size() == 0:
                return True
            if deadline is not None and time.monotonic() >= deadline:
                return False
            await asyncio.sleep(0.1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_dispatch(self) -> None:
        """Wake the dispatch loop after an external state change."""
        self._wake.set()

    def set_admission_checker(self, checker: Callable[[Any], bool] | None) -> None:
        """Install or clear a synchronous policy gate for job dispatch."""
        self._admission_checker = checker
        self._wake.set()

    async def submit(self, job: Any) -> Any:
        """
        Persist and enqueue a job. Returns the job with id/state normalised.

        The caller owns job.payload and job.estimated_vram_bytes (optional).
        If job.priority is None, priority_manager may assign a default.
        """
        if self._shutting_down:
            raise SchedulerShuttingDown("scheduler is shutting down")

        if not getattr(job, "adapter", None):
            raise SchedulerError("job.adapter is required")
        if job.adapter not in self._adapters:
            raise SchedulerError(f"unknown adapter: {job.adapter!r}")

        if not getattr(job, "id", None):
            job.id = str(uuid.uuid4())

        if getattr(job, "priority", None) is None:
            default = getattr(self._priority_manager, "default_priority", None)
            job.priority = default(job) if callable(default) else 0

        job.state = JobState.PENDING
        job.submitted_at = getattr(job, "submitted_at", None) or time.time()
        job.started_at = None
        job.finished_at = None
        job.attempts = getattr(job, "attempts", 0) or 0
        job.last_error = None
        job.result = None

        await self._persist(job)
        await self._priority_manager.push(job)
        self._wake.set()
        LOG.info(
            "job %s submitted (adapter=%s priority=%s est_vram=%s)",
            job.id,
            job.adapter,
            job.priority,
            getattr(job, "estimated_vram_bytes", None),
        )
        return job

    async def cancel(self, job_id: str, *, force: bool = False) -> bool:
        """
        Cancel a pending job, or request cancellation of a running job.

        force=False (default):
            * PENDING -> removed from queue, marked CANCELLED, returns True.
            * RUNNING -> raises JobNotCancellable (do not silently kill work).
            * unknown -> returns False.
        force=True:
            * RUNNING -> calls adapter.request_cancel() if present; returns
              True on request delivery, regardless of outcome. The adapter
              is expected to honour cancellation at a safe point, or ignore
              it if the underlying kernel cannot be interrupted.
        """
        removed = await self._priority_manager.remove(job_id)
        if removed is not None:
            removed.state = JobState.CANCELLED
            removed.finished_at = time.time()
            await self._persist(removed)
            self._wake.set()
            LOG.info("job %s cancelled while pending", job_id)
            return True

        current = self._current_job
        if current is not None and current.id == job_id:
            if not force:
                raise JobNotCancellable(
                    f"job {job_id} is running; pass force=True to request "
                    f"cancellation at the adapter's next safe point"
                )
            adapter = self._adapters.get(current.adapter)
            request = getattr(adapter, "request_cancel", None)
            if callable(request):
                try:
                    await request(current)
                except Exception:
                    LOG.exception(
                        "adapter %s failed to request cancellation for %s",
                        current.adapter,
                        job_id,
                    )
            else:
                LOG.warning(
                    "adapter %s does not implement request_cancel; job %s "
                    "will run to completion",
                    current.adapter,
                    job_id,
                )
            return True

        return False

    async def status(self) -> dict[str, Any]:
        """Snapshot for the control API. Safe to call from any task."""
        current = self._current_job
        return {
            "shutting_down": self._shutting_down,
            "current_job_id": current.id if current is not None else None,
            "pending_jobs": await self._priority_manager.size(),
            "adapters": sorted(self._adapters.keys()),
        }

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    async def _recover_unfinished(self) -> None:
        try:
            unfinished = await self._job_store.list_by_state(
                {JobState.PENDING, JobState.RUNNING}
            )
        except Exception:
            LOG.exception("recovery: failed to load unfinished jobs from job store")
            return

        recovered = 0
        dropped = 0
        for job in unfinished:
            if job.adapter not in self._adapters:
                job.state = JobState.FAILED
                job.finished_at = time.time()
                job.last_error = f"adapter removed from config: {job.adapter!r}"
                await self._persist(job)
                dropped += 1
                LOG.error(
                    "recovery: job %s referenced missing adapter %r; marked failed",
                    job.id,
                    job.adapter,
                )
                continue

            if job.state == JobState.RUNNING:
                LOG.warning(
                    "recovery: job %s was RUNNING at last shutdown; requeueing "
                    "with attempts=%s",
                    job.id,
                    getattr(job, "attempts", 0),
                )
            job.state = JobState.PENDING
            job.started_at = None
            job.finished_at = None
            await self._persist(job)
            await self._priority_manager.push(job)
            recovered += 1

        if recovered or dropped:
            LOG.info("recovery complete: %d requeued, %d dropped", recovered, dropped)

    # ------------------------------------------------------------------
    # Dispatch loop
    # ------------------------------------------------------------------

    async def _dispatch_loop(self) -> None:
        consecutive_errors = 0
        try:
            while not self._shutting_down:
                try:
                    dispatched = await self._try_dispatch_next()
                    consecutive_errors = 0
                except asyncio.CancelledError:
                    raise
                except Exception:
                    consecutive_errors += 1
                    LOG.exception(
                        "dispatch iteration failed (consecutive=%d)",
                        consecutive_errors,
                    )
                    dispatched = False

                if self._shutting_down:
                    break
                if dispatched:
                    continue  # try to pick up the next job immediately

                # Nothing dispatchable. Wait for a wake or re-check.
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(
                        self._wake.wait(), timeout=self.REFRESH_INTERVAL_S
                    )
                self._wake.clear()
        finally:
            self._idle.set()
            LOG.debug("dispatch loop exited")

    async def _try_dispatch_next(self) -> bool:
        """
        Try to run the highest-priority job once.

        Returns True if a job was executed (successfully or not) — the loop
        should immediately try again. Returns False if no job could be
        admitted — the loop should wait for a wake.
        """
        if self._current_job is not None:
            LOG.debug("dispatch: a job is already running; skipping")
            return False

        job = await self._priority_manager.peek()
        if job is None:
            return False
        if self._shutting_down:
            return False
        checker = self._admission_checker
        if checker is not None:
            try:
                if not checker(job):
                    return False
            except Exception:
                LOG.exception("admission checker failed; refusing job %s", job.id)
                return False

        estimate = await self._estimate_vram(job)
        reserved = await self._reserve_memory(job, estimate)
        if not reserved:
            return False

        # Commit: remove from queue under the reservation. If a racing
        # cancel() already removed it, undo the reservation and move on.
        removed = await self._priority_manager.remove(job.id)
        if removed is None:
            LOG.info("job %s vanished from queue before dispatch; skipping", job.id)
            self._vram_manager.release(job)
            return False

        self._current_job = removed
        try:
            await self._run_job(removed)
        finally:
            self._current_job = None
            self._vram_manager.release(removed)

        return True

    async def _run_job(self, job: Any) -> None:
        """Transition through RUNNING and persist the terminal state."""
        job.state = JobState.RUNNING
        mark_running = getattr(self._vram_manager, "mark_running", None)
        if callable(mark_running):
            try:
                mark_running(job)
            except Exception:
                LOG.exception("vram_manager.mark_running failed for %s", job.id)
        job.started_at = time.time()
        job.attempts = int(getattr(job, "attempts", 0)) + 1
        await self._persist(job)
        LOG.info(
            "job %s running (adapter=%s attempts=%d)",
            job.id,
            job.adapter,
            job.attempts,
        )

        adapter = self._adapters.get(job.adapter)
        started_monotonic = time.monotonic()
        try:
            if adapter is None:
                raise SchedulerError(f"no adapter registered for {job.adapter!r}")
            result = await adapter.execute(job)
            job.state = JobState.COMPLETED
            job.result = result
            job.last_error = None
        except asyncio.CancelledError:
            job.state = JobState.CANCELLED
            raise
        except Exception as exc:
            job.state = JobState.FAILED
            job.last_error = f"{type(exc).__name__}: {exc}"
            LOG.exception("job %s failed", job.id)
        finally:
            job.finished_at = time.time()
            await self._persist(job)
            LOG.info(
                "job %s %s in %.2fs",
                job.id,
                job.state,
                time.monotonic() - started_monotonic,
            )

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    async def _estimate_vram(self, job: Any) -> int:
        explicit = getattr(job, "estimated_vram_bytes", None)
        if explicit:
            return int(explicit)

        adapter = self._adapters.get(job.adapter)
        estimate_fn = getattr(adapter, "estimate_vram", None)
        if callable(estimate_fn):
            try:
                return int(await estimate_fn(job))
            except Exception:
                LOG.exception(
                    "adapter %s failed to estimate VRAM for job %s",
                    job.adapter,
                    job.id,
                )

        LOG.warning(
            "no VRAM estimate for job %s; using default %d bytes",
            job.id,
            self.DEFAULT_VRAM_ESTIMATE_BYTES,
        )
        return self.DEFAULT_VRAM_ESTIMATE_BYTES

    async def _reserve_memory(self, job: Any, required_bytes: int) -> bool:
        """
        Try to reserve memory. On failure, ask adapters to free idle models
        and confirm the release via gpu_monitor before retrying once.

        Returns False if memory is still unavailable (the dispatch loop will
        wait and re-check on the next wake or timeout).
        """
        try:
            if await self._vram_manager.try_reserve(job, required_bytes):
                return True
        except Exception:
            LOG.exception("vram_manager.try_reserve raised for job %s", job.id)
            return False

        freed = await self._free_memory_for(job, required_bytes)
        if not freed:
            LOG.debug(
                "job %s waiting: %d bytes unavailable, no memory freed",
                job.id,
                required_bytes,
            )
            return False

        try:
            return await self._vram_manager.try_reserve(job, required_bytes)
        except Exception:
            LOG.exception(
                "vram_manager.try_reserve raised after freeing for job %s", job.id
            )
            return False

    async def _free_memory_for(self, job: Any, required_bytes: int) -> bool:
        """
        Ask every adapter (including the job's own adapter) to unload idle
        models, then confirm via gpu_monitor that free VRAM actually rose.

        We do NOT kill unmanaged processes, signal Steam, or touch anything
        the adapters refuse to release. Unloads are cooperative only.
        """
        before = await self._gpu_monitor.get_status()
        if before is None:
            LOG.warning(
                "gpu_monitor unavailable; cannot free memory for job %s", job.id
            )
            return False
        free_before = int(before.free_vram_bytes)

        for name, adapter in self._adapters.items():
            unload = getattr(adapter, "unload_idle_models", None)
            if not callable(unload):
                continue
            try:
                released = await unload(required_bytes)
                if released:
                    LOG.info("adapter %s released %d bytes", name, released)
            except Exception:
                LOG.exception("adapter %s failed to unload idle models", name)

        after = await self._gpu_monitor.get_status()
        if after is None:
            LOG.warning("gpu_monitor unavailable after freeing; cannot confirm release")
            return False
        free_after = int(after.free_vram_bytes)
        delta = free_after - free_before
        if delta > 0:
            LOG.info(
                "VRAM freed: +%d bytes (now %d free); retrying reservation for job %s",
                delta,
                free_after,
                job.id,
            )
            return True
        return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _persist(self, job: Any) -> None:
        """Best-effort persistence. A store failure must not stall the loop."""
        try:
            await self._job_store.save(job)
        except Exception:
            LOG.exception(
                "failed to persist job %s (state=%s); scheduler continues",
                getattr(job, "id", "?"),
                getattr(job, "state", "?"),
            )

    # ------------------------------------------------------------------
    # Introspection for tests
    # ------------------------------------------------------------------

    @property
    def current_job(self) -> Any | None:
        return self._current_job

    @property
    def is_shutting_down(self) -> bool:
        return self._shutting_down
