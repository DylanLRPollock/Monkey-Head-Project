"""
banana_brain.vram_manager — VRAM reservation and admission control.

Responsibilities (from the Banana Brain design doc):
  * Reserve GPU memory before dispatch so concurrent admissions cannot
    race each other into an OOM.
  * Enforce a configurable VRAM headroom for the OS, CUDA contexts,
    and unmanaged work (e.g. a Steam game that bypasses the scheduler).
  * Fail closed when NVML memory state is unavailable.

Public API (called by the scheduler and by API/CLI for diagnostics):

  async start()                                 -> None
  async stop()                                  -> None
  async try_reserve(job, required_bytes, *,
                    refresh=False)              -> bool
  def   release(job)                            -> None        idempotent
  def   mark_running(job)                       -> None        optional hint
  async available_bytes()                       -> int | None
  async snapshot()                              -> dict
  def   committed_bytes()                       -> int
  def   reservation_count()                     -> int

Contracts expected by callers:

  gpu_monitor.get_status()  -> GPUStatus | None
      GPUStatus.total_vram_bytes / free_vram_bytes: int
  gpu_monitor.refresh()     -> GPUStatus | None

  job.id        : str
  job.adapter   : str
  job.estimated_vram_bytes : int | None   (informational only)

Reservation lifecycle:
  try_reserve()  ->  state=RESERVED
  mark_running() ->  state=ACTIVE    (optional; scheduler should call this
                                      when concurrency is added)
  release()      ->  removed

Reservations are in-memory. They do not survive process restart; the
scheduler's own recovery path is expected to re-submit PENDING and
previously-RUNNING jobs on startup.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any

__all__ = [
    "AdmissionRefused",
    "Reservation",
    "ReservationState",
    "VRAMManager",
]

LOG = logging.getLogger("banana_brain.vram_manager")

GIB = 1024**3


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


class ReservationState(StrEnum):
    """
    RESERVED: memory promised to a job that has not yet started. Counts
              against allocatable free VRAM because NVML does not yet
              reflect it as used.

    ACTIVE:   the job is running; its allocation is already visible in
              NVML's free_vram_bytes. Does NOT count against allocatable
              free, to avoid double-counting.

    The transition RESERVED -> ACTIVE is made by the scheduler calling
    mark_running(job). Callers that never call mark_running leave every
    reservation in RESERVED, which is conservative and safe.
    """

    RESERVED = "reserved"
    ACTIVE = "active"


@dataclass(frozen=True)
class Reservation:
    job_id: str
    adapter: str
    bytes: int
    state: ReservationState
    created_at: float
    updated_at: float


class AdmissionRefused(Exception):
    """
    Raised only by callers who want an exception instead of a bool.

    try_reserve() itself never raises for expected refusals; it returns
    False and records the reason in snapshot()["last_refusal"].
    """


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class VRAMManager:
    """
    Tracks per-job VRAM reservations and decides whether a new job fits.

    All admission decisions are made against the current GPUStatus from
    gpu_monitor, so the caller must ensure that monitor is running.
    """

    #: Default headroom from the design doc: "reserve a few GiB".
    DEFAULT_HEADROOM_GIB = 3.0

    def __init__(self, config: Any, gpu_monitor: Any) -> None:
        self._config = config
        self._gpu_monitor = gpu_monitor

        self._headroom_gib = float(
            _cfg_num(config, "vram_headroom_gib", self.DEFAULT_HEADROOM_GIB)
        )
        self._headroom_percent = float(_cfg_num(config, "vram_headroom_percent", 0.0))

        self._reservations: dict[str, Reservation] = {}
        self._lock = asyncio.Lock()
        self._last_refusal: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        LOG.info(
            "vram_manager ready (headroom=%.2f GiB + %.1f%% of total)",
            self._headroom_gib,
            self._headroom_percent * 100.0,
        )

    async def stop(self) -> None:
        async with self._lock:
            if self._reservations:
                LOG.warning(
                    "vram_manager stopping with %d reservation(s) still held: %s",
                    len(self._reservations),
                    ", ".join(sorted(self._reservations)),
                )
                self._reservations.clear()

    # ------------------------------------------------------------------
    # Admission
    # ------------------------------------------------------------------

    async def try_reserve(
        self,
        job: Any,
        required_bytes: int,
        *,
        refresh: bool = False,
    ) -> bool:
        """
        Reserve `required_bytes` for `job`. Returns True on success.

        Idempotent: calling again for the same job with the same size
        returns True without touching the reservation. Calling with a
        different size updates the reservation atomically, provided the
        new size fits.

        On refusal, the reason is recorded in snapshot()["last_refusal"]
        so the API/CLI can explain why a job is waiting.
        """
        job_id = getattr(job, "id", None) or "<unknown>"
        adapter = getattr(job, "adapter", None) or "<unknown>"

        if (
            isinstance(required_bytes, bool)
            or not isinstance(required_bytes, int)
            or required_bytes <= 0
        ):
            self._refuse(
                "invalid_estimate",
                job_id=job_id,
                requested=required_bytes,
            )
            return False

        status = await self._fetch_status(refresh=refresh)
        if status is None:
            self._refuse("gpu_state_unknown", job_id=job_id, requested=required_bytes)
            return False

        total = int(getattr(status, "total_vram_bytes", 0) or 0)
        free = int(getattr(status, "free_vram_bytes", 0) or 0)

        # NVML sanity checks. Bad values must not be allowed through.
        if total <= 0 or free < 0 or free > total:
            self._refuse(
                "implausible_nvml_data",
                job_id=job_id,
                total=total,
                free=free,
            )
            return False

        if required_bytes > total:
            self._refuse(
                "estimate_exceeds_total",
                job_id=job_id,
                requested=required_bytes,
                total=total,
            )
            return False

        headroom = self._headroom_for(total)

        async with self._lock:
            committed_elsewhere = self._committed_excluding(job_id)
            allocatable = free - committed_elsewhere - headroom

            if required_bytes > allocatable:
                self._refuse(
                    "insufficient_vram",
                    job_id=job_id,
                    requested=required_bytes,
                    free=free,
                    committed_elsewhere=committed_elsewhere,
                    headroom=headroom,
                    allocatable=max(0, allocatable),
                )
                return False

            now = time.time()
            existing = self._reservations.get(job_id)
            if existing is not None:
                updated = replace(
                    existing,
                    bytes=required_bytes,
                    updated_at=now,
                    # Preserve state: if the job is already running we
                    # must not demote it back to RESERVED.
                    state=existing.state,
                )
                self._reservations[job_id] = updated
                if existing.bytes != required_bytes:
                    LOG.info(
                        "job %s reservation %d -> %d bytes",
                        job_id,
                        existing.bytes,
                        required_bytes,
                    )
                else:
                    LOG.debug("job %s reservation refreshed", job_id)
            else:
                self._reservations[job_id] = Reservation(
                    job_id=job_id,
                    adapter=adapter,
                    bytes=required_bytes,
                    state=ReservationState.RESERVED,
                    created_at=now,
                    updated_at=now,
                )
                LOG.info(
                    "job %s reserved %d bytes (free=%d, committed_elsewhere=%d, "
                    "headroom=%d, allocatable=%d)",
                    job_id,
                    required_bytes,
                    free,
                    committed_elsewhere,
                    headroom,
                    allocatable - required_bytes,
                )
            self._last_refusal = None

        return True

    def release(self, job: Any) -> None:
        """
        Release a reservation. Safe to call twice; safe to call when no
        reservation exists. Must NOT await, because the scheduler calls
        this from a finally block.
        """
        job_id = getattr(job, "id", None)
        if job_id is None:
            return
        existing = self._reservations.pop(job_id, None)
        if existing is not None:
            LOG.info(
                "job %s released %d bytes (was %s, held %.1fs)",
                job_id,
                existing.bytes,
                existing.state.value,
                time.time() - existing.created_at,
            )

    def mark_running(self, job: Any) -> None:
        """
        Optional hint: the job is now executing, so its memory is visible
        in NVML's free_vram_bytes. The reservation stops counting against
        allocatable free.

        The scheduler should call this once per job (after the adapter's
        execute() has begun allocating). Today the scheduler serialises
        jobs, so calling mark_running is a no-op improvement — but it is
        required for correct behaviour once concurrent execution is added.
        """
        job_id = getattr(job, "id", None)
        if job_id is None:
            return
        existing = self._reservations.get(job_id)
        if existing is None:
            LOG.debug("mark_running called for job %s with no reservation", job_id)
            return
        if existing.state is ReservationState.ACTIVE:
            return
        self._reservations[job_id] = replace(
            existing,
            state=ReservationState.ACTIVE,
            updated_at=time.time(),
        )
        LOG.debug("job %s reservation is now ACTIVE", job_id)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    async def available_bytes(self) -> int | None:
        """
        Bytes a fresh job could reserve right now, after headroom and
        existing RESERVED commitments. None when GPU state is unknown.
        """
        status = await self._gpu_monitor.get_status()
        if status is None:
            return None
        total = int(getattr(status, "total_vram_bytes", 0) or 0)
        free = int(getattr(status, "free_vram_bytes", 0) or 0)
        if total <= 0 or free < 0 or free > total:
            return None
        allocatable = free - self._committed_excluding(None) - self._headroom_for(total)
        return max(0, allocatable)

    async def snapshot(self) -> dict[str, Any]:
        """Diagnostic view for the control API and CLI."""
        status = await self._gpu_monitor.get_status()
        async with self._lock:
            reservations = [
                {
                    "job_id": r.job_id,
                    "adapter": r.adapter,
                    "bytes": r.bytes,
                    "state": r.state.value,
                    "age_seconds": round(time.time() - r.created_at, 3),
                }
                for r in self._reservations.values()
            ]
            committed = sum(
                r.bytes
                for r in self._reservations.values()
                if r.state is ReservationState.RESERVED
            )

        total = int(getattr(status, "total_vram_bytes", 0) or 0) if status else 0
        free = int(getattr(status, "free_vram_bytes", 0) or 0) if status else 0
        headroom = (
            self._headroom_for(total) if total > 0 else int(self._headroom_gib * GIB)
        )
        allocatable: int | None = None
        if status is not None and total > 0 and 0 <= free <= total:
            allocatable = max(0, free - committed - headroom)

        return {
            "gpu_state_known": status is not None,
            "total_vram_bytes": total,
            "free_vram_bytes": free,
            "committed_bytes": committed,
            "headroom_bytes": headroom,
            "allocatable_bytes": allocatable,
            "reservation_count": len(reservations),
            "reservations": reservations,
            "last_refusal": self._last_refusal,
        }

    def committed_bytes(self) -> int:
        """Sum of RESERVED reservations; ACTIVE ones are already in NVML."""
        return sum(
            r.bytes
            for r in self._reservations.values()
            if r.state is ReservationState.RESERVED
        )

    def reservation_count(self) -> int:
        return len(self._reservations)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _fetch_status(self, *, refresh: bool) -> Any:
        try:
            if refresh:
                return await self._gpu_monitor.refresh()
            return await self._gpu_monitor.get_status()
        except Exception:
            LOG.exception("gpu_monitor call failed while checking VRAM")
            return None

    def _committed_excluding(self, exclude_job_id: str | None) -> int:
        """Sum of RESERVED bytes for jobs other than `exclude_job_id`."""
        total = 0
        for reservation in self._reservations.values():
            if reservation.state is not ReservationState.RESERVED:
                continue
            if exclude_job_id is not None and reservation.job_id == exclude_job_id:
                continue
            total += reservation.bytes
        return total

    def _headroom_for(self, total_vram_bytes: int) -> int:
        fixed = int(self._headroom_gib * GIB)
        percent = int(self._headroom_percent * max(0, total_vram_bytes))
        return max(fixed, percent)

    def _refuse(self, reason: str, **details: Any) -> None:
        self._last_refusal = {
            "reason": reason,
            "at": time.time(),
            **details,
        }
        LOG.info("admission refused: %s %s", reason, details)


# ---------------------------------------------------------------------------
# Config helpers (tolerant of dataclass, mapping, or attribute access)
# ---------------------------------------------------------------------------


def _cfg_get(config: Any, name: str) -> Any:
    if isinstance(config, dict):
        return config.get(name)
    return getattr(config, name, None)


def _cfg_num(config: Any, name: str, default: float) -> float:
    value = _cfg_get(config, name)
    return float(value) if isinstance(value, (int, float)) else default
