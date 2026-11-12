"""
banana_brain.job_models — canonical types for GPU jobs.

This is a leaf module: it MUST NOT import from any other banana_brain
module. Every other module may import from here.

Provides:
  Job               structured job with identity, priority, deadline,
                    VRAM estimate, state, attempts and result.
  JobState          enum of job states; string-compatible with existing
                    code that uses "pending", "running", etc.
  Priority          IntEnum of well-known priority levels (10..100).
  JobResult         optional structured result for adapters.
  JobValidationError / JobTransitionError
  new_job_id()      uuid4 helper.

Field lifetime contract, as relied on by banana_brain.scheduler:
  * The scheduler may assign job.id and job.priority at submit() time.
  * The scheduler sets state, timestamps, attempts, last_error, result.
  * to_dict() / from_dict() are the persistence contract used by
    job_store and must round-trip every scheduler-assigned field.
  * Adapters receive the fully-populated Job in execute(job).

Adapters should return either a JSON-serialisable dict or a JobResult.
Anything else will cause job_store.save() to raise during persistence,
which is intentional: silent repr-based lossy storage hides adapter bugs.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import IntEnum, StrEnum
from typing import Any

__all__ = [
    "ACTIVE_STATES",
    "ALL_STATES",
    "TERMINAL_STATES",
    "Adapters",
    "Job",
    "JobResult",
    "JobState",
    "JobTransitionError",
    "JobValidationError",
    "Priority",
    "new_job_id",
]


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class JobState(StrEnum):
    """
    Lifecycle states for a job.

    StrEnum makes ``JobState.PENDING == "pending"`` true and keeps hashes
    compatible with the plain strings currently used in
    banana_brain.scheduler. The whole package relies on string equality
    for backward compatibility.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_active(self) -> bool:
        return self in ACTIVE_STATES

    @property
    def is_terminal(self) -> bool:
        return self in TERMINAL_STATES


ACTIVE_STATES: frozenset[JobState] = frozenset({JobState.PENDING, JobState.RUNNING})
TERMINAL_STATES: frozenset[JobState] = frozenset(
    {JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED}
)
ALL_STATES: frozenset[JobState] = ACTIVE_STATES | TERMINAL_STATES


#: Legal transitions. The scheduler is not required to enforce these — it
#: currently assigns state directly — but any component that wants stricter
#: checking can call Job.can_transition_to() / Job.transition_to().
_LEGAL_TRANSITIONS: dict[JobState, frozenset[JobState]] = {
    JobState.PENDING: frozenset(
        {JobState.RUNNING, JobState.CANCELLED, JobState.FAILED}
    ),
    JobState.RUNNING: frozenset(
        {JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED}
    ),
    JobState.COMPLETED: frozenset(),
    JobState.FAILED: frozenset({JobState.PENDING}),  # retry path
    JobState.CANCELLED: frozenset(),
}


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------


class Priority(IntEnum):
    """
    Well-known priority levels from the Banana Brain design doc, §3.

    Higher is more important. Values are deliberately stable so they can
    be persisted and compared across versions; do not renumber.
    """

    SAFETY = 100  # thermal / hardware safety halt
    EXCLUSIVE = 90  # manual exclusive mode (gaming, operator task)
    INTERACTIVE = 80  # interactive Huey / PyGPT requests
    IMAGE = 70  # user-requested image generation
    AUDIO = 60  # user-requested audio tasks
    BACKGROUND = 40  # background RAG / embeddings
    BATCH = 20  # batch image / video generation
    MAINTENANCE = 10  # maintenance / benchmarking


# ---------------------------------------------------------------------------
# Adapter name constants (informational; config is authoritative)
# ---------------------------------------------------------------------------


class Adapters:
    """Well-known adapter names. Config validates which are installed."""

    OLLAMA = "ollama"
    COMFYUI = "comfyui"
    AUDIO = "audio"
    PYGpt = "pygpt"  # reserved; P1


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class JobResult:
    """
    Optional structured result for adapters to return.

    Adapters are free to return any JSON-serialisable object; JobResult is
    provided so that adapters which want to report metrics or a message
    have a stable shape to do so without inventing their own.
    """

    ok: bool
    data: dict[str, Any] = field(default_factory=dict)
    message: str = ""
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": bool(self.ok),
            "data": dict(self.data or {}),
            "message": str(self.message or ""),
            "metrics": {k: float(v) for k, v in (self.metrics or {}).items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JobResult:
        return cls(
            ok=bool(data.get("ok", True)),
            data=dict(data.get("data") or {}),
            message=str(data.get("message") or ""),
            metrics={
                k: float(v)
                for k, v in (data.get("metrics") or {}).items()
                if isinstance(v, (int, float))
            },
        )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class JobValidationError(ValueError):
    """Raised by Job.validate() when the job is malformed."""


class JobTransitionError(ValueError):
    """Raised by Job.transition_to() for an illegal state transition."""


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------

#: JSON-serialisation discriminator for embedded JobResults.
_RESULT_TAG = "__bb_class__"


@dataclass(eq=False)
class Job:
    """
    A single GPU job.

    Construct with ``adapter`` and ``payload``; everything else has a
    sensible default. ``id`` is auto-generated if not provided.

    Mutable. The scheduler, adapters, and job_store are permitted to
    mutate fields as the job progresses. Equality is by ``id`` only.
    """

    # ---- Required ---------------------------------------------------------
    adapter: str
    payload: dict[str, Any]

    # ---- Identity ---------------------------------------------------------
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # ---- Scheduling -------------------------------------------------------
    priority: int = int(Priority.BACKGROUND)
    state: JobState = JobState.PENDING
    exclusive: bool = False
    deadline: float | None = None  # absolute unix timestamp

    # ---- Resources --------------------------------------------------------
    estimated_vram_bytes: int | None = None

    # ---- Accountability ---------------------------------------------------
    owner: str | None = None
    tags: dict[str, str] = field(default_factory=dict)
    idempotency_key: str | None = None

    # ---- Progress ---------------------------------------------------------
    submitted_at: float | None = None
    started_at: float | None = None
    finished_at: float | None = None
    attempts: int = 0
    max_attempts: int = 1
    last_error: str | None = None
    result: Any | None = None

    # ---- Optimistic concurrency (job_store) -------------------------------
    version: int = 0

    # ------------------------------------------------------------------
    # Construction and normalisation
    # ------------------------------------------------------------------

    def __post_init__(self) -> None:
        # Coerce state from str (persisted) or JobState (fresh).
        if not isinstance(self.state, JobState):
            try:
                self.state = JobState(self.state)
            except ValueError as exc:
                raise JobValidationError(
                    f"invalid job state {self.state!r}: {exc}"
                ) from exc

        # Always store priority as a plain int. Priority.PENDING -> int works
        # because IntEnum is int; accidental None becomes BACKGROUND.
        if self.priority is None:
            self.priority = int(Priority.BACKGROUND)
        else:
            self.priority = int(self.priority)

        # Defensive: getattr(job, "id", None) is used everywhere; ensure
        # an empty-string id from a caller doesn't silently pass through.
        if not self.id:
            self.id = str(uuid.uuid4())

    # ------------------------------------------------------------------
    # Identity semantics
    # ------------------------------------------------------------------

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Job):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        short_id = self.id[:8] + "…" if len(self.id) > 8 else self.id
        return (
            f"Job(id={short_id} adapter={self.adapter} "
            f"state={self.state.value} priority={self.priority} "
            f"attempts={self.attempts}/{self.max_attempts})"
        )

    # ------------------------------------------------------------------
    # State helpers
    # ------------------------------------------------------------------

    @property
    def is_active(self) -> bool:
        return self.state in ACTIVE_STATES

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def can_retry(self) -> bool:
        return self.state is JobState.FAILED and self.attempts < self.max_attempts

    def can_transition_to(self, new_state: JobState | str) -> bool:
        if not isinstance(new_state, JobState):
            new_state = JobState(new_state)
        if new_state is self.state:
            return True
        return new_state in _LEGAL_TRANSITIONS.get(self.state, frozenset())

    def transition_to(self, new_state: JobState | str) -> None:
        if not isinstance(new_state, JobState):
            new_state = JobState(new_state)
        if not self.can_transition_to(new_state):
            raise JobTransitionError(
                f"job {self.id}: illegal transition "
                f"{self.state.value} -> {new_state.value}"
            )
        self.state = new_state

    def reset_for_retry(self) -> bool:
        """
        Return a FAILED job to PENDING for another attempt.

        Does NOT increment attempts — that counter is updated by the
        scheduler when the job starts running. Returns False if the job
        is not in a retryable state.
        """
        if not self.can_retry:
            return False
        self.state = JobState.PENDING
        self.started_at = None
        self.finished_at = None
        self.last_error = None
        return True

    # ------------------------------------------------------------------
    # Timing helpers
    # ------------------------------------------------------------------

    def age_seconds(self, *, now: float | None = None) -> float | None:
        """Seconds since submission; None if never submitted."""
        if self.submitted_at is None:
            return None
        return (time.time() if now is None else now) - self.submitted_at

    def remaining_seconds(self, *, now: float | None = None) -> float | None:
        """Seconds until deadline; None if no deadline set."""
        if self.deadline is None:
            return None
        return self.deadline - (time.time() if now is None else now)

    def is_overdue(self, *, now: float | None = None) -> bool:
        remaining = self.remaining_seconds(now=now)
        return remaining is not None and remaining < 0

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        Raise JobValidationError if the job is internally inconsistent.

        The scheduler does not call this on every submit (to keep the hot
        path fast), but scheduler_api and scheduler_cli should call it on
        incoming jobs to produce clear errors for callers.
        """
        problems = self._validation_problems()

        if problems:
            raise JobValidationError(f"job {self.id}: " + "; ".join(problems))

    def _validation_problems(self) -> list[str]:
        problems: list[str] = []
        self._validate_core_fields(problems)
        self._validate_attempt_fields(problems)
        self._validate_optional_fields(problems)
        return problems

    def _validate_core_fields(self, problems: list[str]) -> None:
        if not isinstance(self.id, str) or not self.id:
            problems.append("id must be a non-empty string")
        if not isinstance(self.adapter, str) or not self.adapter:
            problems.append("adapter must be a non-empty string")
        if not isinstance(self.payload, dict):
            problems.append("payload must be a dict")
        if not isinstance(self.priority, int) or isinstance(self.priority, bool):
            problems.append("priority must be an int")
        if not isinstance(self.state, JobState):
            problems.append(f"state must be JobState, got {type(self.state).__name__}")

    def _validate_attempt_fields(self, problems: list[str]) -> None:
        if self.estimated_vram_bytes is not None and (
            not isinstance(self.estimated_vram_bytes, int)
            or self.estimated_vram_bytes <= 0
        ):
            problems.append("estimated_vram_bytes must be a positive int")
        if self.deadline is not None and self.deadline < 0:
            problems.append("deadline must be a non-negative unix timestamp")
        if not isinstance(self.attempts, int) or self.attempts < 0:
            problems.append("attempts must be a non-negative int")
        if not isinstance(self.max_attempts, int) or self.max_attempts < 1:
            problems.append("max_attempts must be an int >= 1")

    def _validate_optional_fields(self, problems: list[str]) -> None:
        if self.owner is not None and not isinstance(self.owner, str):
            problems.append("owner must be a string or None")
        if self.idempotency_key is not None and not isinstance(
            self.idempotency_key, str
        ):
            problems.append("idempotency_key must be a string or None")
        if not isinstance(self.tags, dict):
            problems.append("tags must be a dict")
            return
        for key, value in self.tags.items():
            if not isinstance(key, str) or not isinstance(value, str):
                problems.append("tags keys and values must be strings")
                break

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        JSON-serialisable representation. Used by job_store.save().

        Deliberately does NOT coerce ``result`` beyond JobResult tagging —
        if an adapter returns a non-serialisable object, json.dumps() will
        raise here and the operator will see which adapter needs fixing.
        """
        return {
            "id": self.id,
            "adapter": self.adapter,
            "payload": self.payload,
            "priority": int(self.priority),
            "state": self.state.value,
            "exclusive": bool(self.exclusive),
            "deadline": self.deadline,
            "estimated_vram_bytes": self.estimated_vram_bytes,
            "owner": self.owner,
            "tags": dict(self.tags or {}),
            "idempotency_key": self.idempotency_key,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "attempts": int(self.attempts),
            "max_attempts": int(self.max_attempts),
            "last_error": self.last_error,
            "result": _serialise_result(self.result),
            "version": int(self.version),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Job:
        """
        Inverse of to_dict(). Tolerant of missing/extra keys but strict
        about adapter (required) and state (must parse).
        """
        if "adapter" not in data:
            raise JobValidationError("from_dict: missing required field 'adapter'")
        return cls(
            adapter=str(data["adapter"]),
            payload=dict(data.get("payload") or {}),
            id=str(data.get("id") or str(uuid.uuid4())),
            priority=_coerce_int(data.get("priority"), int(Priority.BACKGROUND)),
            state=_coerce_state(data.get("state", JobState.PENDING.value)),
            exclusive=bool(data.get("exclusive", False)),
            deadline=_maybe_float(data.get("deadline")),
            estimated_vram_bytes=_maybe_positive_int(data.get("estimated_vram_bytes")),
            owner=_maybe_str(data.get("owner")),
            tags=dict(data.get("tags") or {}),
            idempotency_key=_maybe_str(data.get("idempotency_key")),
            submitted_at=_maybe_float(data.get("submitted_at")),
            started_at=_maybe_float(data.get("started_at")),
            finished_at=_maybe_float(data.get("finished_at")),
            attempts=_coerce_int(data.get("attempts"), 0),
            max_attempts=max(1, _coerce_int(data.get("max_attempts"), 1)),
            last_error=_maybe_str(data.get("last_error")),
            result=_deserialise_result(data.get("result")),
            version=_coerce_int(data.get("version"), 0),
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def new_job_id() -> str:
    """Return a fresh job id. Exposed for tests and adapters."""
    return str(uuid.uuid4())


def _coerce_state(value: Any) -> JobState:
    if isinstance(value, JobState):
        return value
    try:
        return JobState(value)
    except ValueError as exc:
        raise JobValidationError(f"invalid job state {value!r}") from exc


def _coerce_int(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _maybe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _maybe_positive_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        ivalue = int(value)
    except (TypeError, ValueError):
        return None
    return ivalue if ivalue > 0 else None


def _maybe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _serialise_result(result: Any) -> Any:
    """
    Serialise a job result for persistence.

    A JobResult is tagged so from_dict can restore it. Anything else is
    passed through unchanged, letting json.dumps() raise if the adapter
    returned a non-serialisable object (that failure is intentional).
    """
    if result is None:
        return None
    if isinstance(result, JobResult):
        return {_RESULT_TAG: "JobResult", **result.to_dict()}
    return result


def _deserialise_result(data: Any) -> Any:
    if data is None:
        return None
    if isinstance(data, dict) and data.get(_RESULT_TAG) == "JobResult":
        try:
            return JobResult.from_dict(data)
        except Exception:
            return data
    return data
