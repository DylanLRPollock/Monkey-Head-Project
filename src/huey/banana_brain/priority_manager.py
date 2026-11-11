"""
banana_brain.priority_manager — GPU job queue ordering.

Responsibilities (from the Banana Brain design doc):
  * Order queued jobs by effective priority, with FIFO tiebreak.
  * Honour deadlines: sooner-deadline jobs sort before
    later-or-no-deadline jobs at equal effective priority.
  * Prevent starvation via priority aging: long-waiting jobs gain
    effective priority over time, capped so they never exceed the
    safety and exclusive levels.
  * Provide a stable snapshot for the CLI and API.

Public API (all methods must be called from the asyncio event loop):

  async start()                         -> None
  async stop()                          -> None
  async push(job)                       -> None
  async peek(now=None)                  -> Job | None
  async remove(job_id)                  -> Job | None
  async size()                          -> int
  async clear()                         -> list[Job]
  async snapshot(now=None, limit=None)  -> dict
  def   default_priority(job)           -> int    reserved; always BACKGROUND
  def   head_is_exclusive(now=None)     -> bool   informational

Ordering, from highest to lowest precedence:

  1. Effective priority (higher first).
     effective = min(base + aging_bonus + overdue_bonus, aging_cap)
  2. Deadline present (jobs with deadlines first).
  3. Deadline time (sooner first).
  4. submitted_at (FIFO).
  5. job.id (stable tiebreak).

Concurrency:

  The scheduler is single-threaded but wakes on asyncio.Event, so two
  coroutines can call push()/remove() concurrently. Mutations are guarded
  by a lock. peek() does not need the lock (it only reads), but takes it
  for a consistent read against in-flight mutations during snapshot().

Contracts with other modules:

  Job (from job_models):
    id, adapter, priority (int), state (JobState), exclusive (bool),
    deadline (float | None), submitted_at (float | None)

  Scheduler:
    Calls peek() then remove(). Assumes remove(job.id) either returns
    the job it just peeked or None (racing cancellation). Never calls
    remove() with an id it did not obtain from peek() first.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from .job_models import Job, Priority

__all__ = ["PriorityManager"]

LOG = logging.getLogger("banana_brain.priority_manager")


class PriorityManager:
    """
    Effective-priority queue with aging and deadline awareness.

    All entries are held by job.id in a dict for O(1) remove and size;
    ordering is derived on each peek from the current wall clock, so
    aging takes effect without any background timer.
    """

    #: Default aging: +1 effective priority per 60s of waiting.
    DEFAULT_AGING_INTERVAL_S = 60.0
    DEFAULT_AGING_STEP = 1

    #: Aging can lift any job to just below SAFETY (100). A long-waiting
    #: maintenance job can therefore eventually outrun a fresh interactive
    #: request, but never outruns a hardware-safety halt or the operator's
    #: exclusive reservation at 90 — the cap at 99 is deliberate.
    DEFAULT_AGING_CAP = 99

    #: Flat boost applied to jobs whose deadline has passed.
    DEFAULT_OVERDUE_BOOST = 20

    def __init__(self, config: Any) -> None:
        self._config = config

        self._aging_interval = float(
            _cfg_num(config, "priority_aging_interval_seconds",
                     self.DEFAULT_AGING_INTERVAL_S)
        )
        self._aging_step = int(
            _cfg_num(config, "priority_aging_step", self.DEFAULT_AGING_STEP)
        )
        self._aging_cap = int(
            _cfg_num(config, "priority_aging_cap", self.DEFAULT_AGING_CAP)
        )
        self._overdue_boost = int(
            _cfg_num(config, "priority_overdue_boost", self.DEFAULT_OVERDUE_BOOST)
        )

        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()

        if self._aging_interval <= 0:
            LOG.warning(
                "priority_aging_interval_seconds=%.1f is non-positive; aging "
                "disabled", self._aging_interval,
            )
        if self._aging_cap < int(Priority.SAFETY):
            LOG.info(
                "priority aging cap is %d (< SAFETY=%d); starving jobs will "
                "never exceed this ceiling",
                self._aging_cap, int(Priority.SAFETY),
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        LOG.info(
            "priority_manager ready (aging +%d/%ds, cap=%d, overdue +%d)",
            self._aging_step, int(self._aging_interval),
            self._aging_cap, self._overdue_boost,
        )

    async def stop(self) -> None:
        async with self._lock:
            count = len(self._jobs)
            self._jobs.clear()
        if count:
            LOG.warning(
                "priority_manager stopped with %d job(s) discarded "
                "(scheduler should have drained before stop)", count,
            )

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    async def push(self, job: Job) -> None:
        """
        Enqueue a job. If a job with the same id already exists, the
        newer one wins — this is how recovery re-pushes previously-RUNNING
        jobs that were re-read from the store with updated state.
        """
        if job is None or not getattr(job, "id", None):
            raise ValueError("push(): job must have a non-empty id")
        async with self._lock:
            self._jobs[job.id] = job
        LOG.debug(
            "queued job %s (priority=%d, adapter=%s, queue=%d)",
            job.id, int(job.priority), job.adapter, len(self._jobs),
        )

    async def remove(self, job_id: str) -> Optional[Job]:
        """Remove and return the job, or None if it is no longer queued."""
        if not job_id:
            return None
        async with self._lock:
            return self._jobs.pop(job_id, None)

    async def clear(self) -> list[Job]:
        """Remove every queued job and return them. Used by tests."""
        async with self._lock:
            jobs = list(self._jobs.values())
            self._jobs.clear()
        return jobs

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------

    async def peek(self, *, now: Optional[float] = None) -> Optional[Job]:
        """
        Return the job that should run next, or None if the queue is empty.

        Does not mutate the queue; the scheduler is expected to remove()
        the returned job immediately after peeking, before dispatching.
        """
        async with self._lock:
            if not self._jobs:
                return None
            when = time.time() if now is None else float(now)
            return min(
                self._jobs.values(),
                key=lambda job: self._sort_key(job, when),
            )

    async def size(self) -> int:
        async with self._lock:
            return len(self._jobs)

    def default_priority(self, job: Job) -> int:
        """
        Default priority when the caller does not specify one.

        Always BACKGROUND. Reserved for adapters that later want to
        hint a default (e.g. comfyui batch workflows defaulting to BATCH);
        the scheduler currently never calls this because Job.__post_init__
        fills in BACKGROUND when priority is omitted.
        """
        return int(Priority.BACKGROUND)

    async def head_is_exclusive(self, *, now: Optional[float] = None) -> bool:
        """
        True if the job at the head of the queue has exclusive=True.

        Informational. Today the scheduler serialises so this does not
        affect dispatch; once concurrency is added, the scheduler will
        use this to decide whether to pause admission after the current
        job finishes.
        """
        head = await self.peek(now=now)
        return bool(head is not None and getattr(head, "exclusive", False))

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    async def snapshot(
        self,
        *,
        now: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Ordered view for the CLI and API.

        `limit` caps the number of entries returned; totals are still
        over the full queue. The list is ordered head-first.
        """
        when = time.time() if now is None else float(now)
        async with self._lock:
            jobs = list(self._jobs.values())

        jobs.sort(key=lambda job: self._sort_key(job, when))
        total = len(jobs)
        if limit is not None and limit >= 0:
            jobs = jobs[:limit]

        return {
            "size": total,
            "now": when,
            "entries": [
                {
                    "id": job.id,
                    "adapter": job.adapter,
                    "state": job.state.value,
                    "base_priority": int(job.priority),
                    "effective_priority": self._effective_priority(job, when),
                    "aging_bonus": self._aging_bonus(job, when),
                    "overdue": self._is_overdue(job, when),
                    "deadline": job.deadline,
                    "age_seconds": self._age(job, when),
                    "submitted_at": job.submitted_at,
                    "exclusive": bool(getattr(job, "exclusive", False)),
                }
                for job in jobs
            ],
        }

    # ------------------------------------------------------------------
    # Ordering internals
    # ------------------------------------------------------------------

    def _sort_key(self, job: Job, now: float) -> tuple:
        """
        Ascending tuple; the smallest is the next job to run.

        Element 0 is negated because min() is used, not max().
        """
        effective = self._effective_priority(job, now)
        has_deadline = job.deadline is not None
        deadline = float(job.deadline) if has_deadline else 0.0
        submitted = (
            float(job.submitted_at) if job.submitted_at is not None else 0.0
        )
        return (
            -effective,
            0 if has_deadline else 1,
            deadline,
            submitted,
            job.id,
        )

    def _effective_priority(self, job: Job, now: float) -> int:
        base = int(job.priority)
        bonus = self._aging_bonus(job, now)
        if self._is_overdue(job, now):
            bonus += self._overdue_boost
        return min(base + bonus, max(self._aging_cap, base))

    def _aging_bonus(self, job: Job, now: float) -> int:
        if self._aging_interval <= 0 or self._aging_step <= 0:
            return 0
        age = self._age(job, now)
        if age <= 0:
            return 0
        units = int(age // self._aging_interval)
        return units * self._aging_step

    @staticmethod
    def _age(job: Job, now: float) -> float:
        submitted = job.submitted_at
        if submitted is None:
            return 0.0
        # Clamp against a backward wall-clock jump so aging can only
        # ever help a job, never reorder it behind a newer arrival.
        return max(0.0, now - float(submitted))

    @staticmethod
    def _is_overdue(job: Job, now: float) -> bool:
        return job.deadline is not None and now > float(job.deadline)


# ---------------------------------------------------------------------------
# Config helpers (tolerant of dataclass, mapping, or attribute access)
# ---------------------------------------------------------------------------

def _cfg_num(config: Any, name: str, default: float) -> float:
    if isinstance(config, dict):
        value = config.get(name)
    else:
        value = getattr(config, name, None)
    return float(value) if isinstance(value, (int, float)) else default