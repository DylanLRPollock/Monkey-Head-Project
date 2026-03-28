# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Task Scheduler module (src/hueyos/core)

"""Task scheduling and resource aware assignment for HueyOS agents."""

from __future__ import annotations

import heapq
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from threading import RLock
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

try:  # pragma: no cover - psutil is optional at runtime
    import psutil  # type: ignore
except Exception:  # pragma: no cover - provide stub behaviour when psutil missing
    psutil = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)


class Agent(str, Enum):
    """Enumeration of the primary AI agents managed by the scheduler."""

    SPARK = "spark"
    ZAP = "zap"


class TaskStatus(str, Enum):
    """Lifecycle states for submitted tasks."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(IntEnum):
    """Integer priority levels compatible with queue comparisons."""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class ResourceProfile:
    """Relative resource expectations for a task.

    Values represent a fraction between 0.0 and 1.0 describing the expected
    utilisation of the referenced resource. They are heuristics rather than
    guarantees but enable the scheduler to decline heavy work when the system is
    already constrained.
    """

    cpu: float = 0.3
    memory: float = 0.2
    battery: float = 0.1
    gpu: float = 0.0

    def clamp(self) -> "ResourceProfile":
        """Return a new profile with values constrained to the 0..1 range."""

        return ResourceProfile(
            cpu=min(max(self.cpu, 0.0), 1.0),
            memory=min(max(self.memory, 0.0), 1.0),
            battery=min(max(self.battery, 0.0), 1.0),
            gpu=min(max(self.gpu, 0.0), 1.0),
        )


@dataclass
class ResourceSnapshot:
    """Point-in-time observation of host resource utilisation."""

    timestamp: float = field(default_factory=lambda: time.time())
    cpu_percent: Optional[float] = None
    memory_available: Optional[float] = None
    memory_total: Optional[float] = None
    battery_percent: Optional[float] = None
    notes: Optional[str] = None


@dataclass
class TaskLogEntry:
    """Historical status update for a task."""

    timestamp: float
    status: TaskStatus
    message: str


@dataclass
class TaskRecord:
    """Internal representation of a tracked task."""

    task_id: str
    command: str
    priority: TaskPriority
    requested_agent: Optional[Agent]
    assigned_agent: Optional[Agent]
    status: TaskStatus
    created_at: float
    updated_at: float
    attempts: int = 0
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    resource_profile: ResourceProfile = field(default_factory=ResourceProfile)
    snapshot: Optional[ResourceSnapshot] = None
    history: List[TaskLogEntry] = field(default_factory=list)
    excluded_agents: Set[Agent] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the record to a JSON compatible mapping."""

        return {
            "task_id": self.task_id,
            "command": self.command,
            "priority": int(self.priority),
            "requested_agent": (
                self.requested_agent.value if self.requested_agent else None
            ),
            "assigned_agent": (
                self.assigned_agent.value if self.assigned_agent else None
            ),
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "attempts": self.attempts,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
            "resource_profile": {
                "cpu": self.resource_profile.cpu,
                "memory": self.resource_profile.memory,
                "battery": self.resource_profile.battery,
                "gpu": self.resource_profile.gpu,
            },
            "snapshot": {
                "timestamp": self.snapshot.timestamp if self.snapshot else None,
                "cpu_percent": self.snapshot.cpu_percent if self.snapshot else None,
                "memory_available": (
                    self.snapshot.memory_available if self.snapshot else None
                ),
                "memory_total": self.snapshot.memory_total if self.snapshot else None,
                "battery_percent": (
                    self.snapshot.battery_percent if self.snapshot else None
                ),
                "notes": self.snapshot.notes if self.snapshot else None,
            },
            "history": [
                {
                    "timestamp": entry.timestamp,
                    "status": entry.status.value,
                    "message": entry.message,
                }
                for entry in self.history
            ],
        }


HealthProvider = Callable[[], ResourceSnapshot]


class TaskScheduler:
    """Priority aware scheduler with host resource monitoring."""

    def __init__(
        self,
        *,
        cpu_threshold: float = 85.0,
        battery_threshold: float = 20.0,
        min_free_memory: float = 0.15,
        health_provider: Optional[HealthProvider] = None,
        max_retries: int = 1,
        max_concurrency: Optional[Dict[Agent, int]] = None,
        default_concurrency: int = 1,
    ) -> None:
        self.cpu_threshold = cpu_threshold
        self.battery_threshold = battery_threshold
        self.min_free_memory = min_free_memory
        self.health_provider = health_provider or self._default_health_provider
        self.max_retries = max_retries
        self._lock = RLock()
        self._tasks: Dict[str, TaskRecord] = {}
        self._pending_heap: List[Tuple[int, float, str]] = []
        self._pending_index: Set[str] = set()

        if max_concurrency is None:
            max_concurrency = {
                agent: max(1, int(default_concurrency)) for agent in Agent
            }
        else:
            max_concurrency = {
                agent: max(0, int(max_concurrency.get(agent, default_concurrency)))
                for agent in Agent
            }
        self._agent_capacity: Dict[Agent, int] = max_concurrency
        self._agent_load: Dict[Agent, int] = {agent: 0 for agent in Agent}

    # ------------------------------------------------------------------
    # Health monitoring
    # ------------------------------------------------------------------
    def _default_health_provider(self) -> ResourceSnapshot:  # pragma: no cover -
        """Collect current resource usage metrics from the operating system."""

        snapshot = ResourceSnapshot()
        if psutil is None:
            snapshot.notes = "psutil not available"
            return snapshot

        try:
            snapshot.cpu_percent = float(psutil.cpu_percent(interval=0.05))
        except Exception as exc:  # pragma: no cover - defensive
            snapshot.notes = f"cpu_percent unavailable: {exc}"

        try:
            virtual_mem = psutil.virtual_memory()
            snapshot.memory_available = float(virtual_mem.available)
            snapshot.memory_total = float(virtual_mem.total)
        except Exception as exc:  # pragma: no cover - defensive
            snapshot.notes = (snapshot.notes or "") + f" memory unavailable: {exc}"

        try:
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    snapshot.battery_percent = float(battery.percent)
        except Exception as exc:  # pragma: no cover - defensive
            snapshot.notes = (snapshot.notes or "") + f" battery unavailable: {exc}"

        return snapshot

    def _system_ready(
        self, profile: ResourceProfile
    ) -> Tuple[bool, Optional[str], ResourceSnapshot]:
        """Determine whether the host can accept additional load."""

        profile = profile.clamp()
        snapshot = self.health_provider()
        reason: Optional[str] = None

        cpu_percent = snapshot.cpu_percent
        if cpu_percent is not None:
            allowed = max(0.0, self.cpu_threshold - (profile.cpu * 15.0))
            if cpu_percent > allowed:
                reason = f"CPU utilisation {cpu_percent:.1f}% exceeds {allowed:.1f}% allowance"

        if (
            reason is None
            and snapshot.memory_available is not None
            and snapshot.memory_total
        ):
            free_ratio = snapshot.memory_available / snapshot.memory_total
            minimum = max(0.05, self.min_free_memory - (profile.memory * 0.1))
            if free_ratio < minimum:
                reason = (
                    "Insufficient memory headroom "
                    f"({free_ratio:.2%} available, required >= {minimum:.2%})"
                )

        battery_percent = snapshot.battery_percent
        if (
            reason is None
            and battery_percent is not None
            and battery_percent < (self.battery_threshold + profile.battery * 10.0)
        ):
            reason = (
                f"Battery level {battery_percent:.0f}% below threshold "
                f"{self.battery_threshold:.0f}%"
            )

        return reason is None, reason, snapshot

    # ------------------------------------------------------------------
    # Task management helpers
    # ------------------------------------------------------------------
    def _available_agents(self) -> List[Agent]:
        return [
            agent
            for agent in Agent
            if self._agent_load[agent] < self._agent_capacity[agent]
        ]

    def _select_agent(self, record: TaskRecord) -> Optional[Agent]:
        """Choose an agent based on requested preference, exclusions, and load."""

        available = self._available_agents()
        if not available:
            return None

        requested = record.requested_agent
        if (
            requested is not None
            and requested in available
            and requested not in record.excluded_agents
        ):
            return requested

        available.sort(
            key=lambda agent: (agent in record.excluded_agents, self._agent_load[agent])
        )
        return available[0]

    def _log_transition(self, record: TaskRecord, message: str) -> None:
        entry = TaskLogEntry(
            timestamp=time.time(), status=record.status, message=message
        )
        record.history.append(entry)
        LOGGER.debug("Task %s: %s", record.task_id, message)

    def _update_status(
        self, record: TaskRecord, status: TaskStatus, message: str
    ) -> None:
        record.status = status
        record.updated_at = time.time()
        self._log_transition(record, message)

    def _enqueue_pending(self, record: TaskRecord) -> None:
        if record.status is not TaskStatus.PENDING:
            return
        if record.task_id in self._pending_index:
            return
        heapq.heappush(
            self._pending_heap,
            (-int(record.priority), record.created_at, record.task_id),
        )
        self._pending_index.add(record.task_id)

    def _attempt_dispatch(
        self,
        record: TaskRecord,
        *,
        from_queue: bool = False,
        success_message: Optional[str] = None,
    ) -> bool:
        can_run, reason, snapshot = self._system_ready(record.resource_profile)
        record.snapshot = snapshot
        if not can_run:
            self._update_status(
                record,
                TaskStatus.PENDING,
                reason or "System health unknown; task pending",
            )
            return False

        agent = self._select_agent(record)
        if agent is None:
            self._update_status(
                record,
                TaskStatus.PENDING,
                "All agents at capacity; task pending",
            )
            return False

        record.assigned_agent = agent
        record.attempts += 1
        self._agent_load[agent] += 1
        record.excluded_agents.discard(agent)
        message = success_message or (
            "Task dispatched from queue" if from_queue else "Task dispatched to agent"
        )
        self._update_status(record, TaskStatus.RUNNING, message)
        return True

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def schedule_task(
        self,
        *,
        command: str,
        priority: TaskPriority = TaskPriority.NORMAL,
        requested_agent: Optional[Agent] = None,
        metadata: Optional[Dict[str, Any]] = None,
        resource_profile: Optional[ResourceProfile] = None,
    ) -> TaskRecord:
        """Register a new task and attempt assignment to an agent."""

        resource_profile = (resource_profile or ResourceProfile()).clamp()
        task_id = uuid.uuid4().hex
        created = time.time()
        record = TaskRecord(
            task_id=task_id,
            command=command,
            priority=priority,
            requested_agent=requested_agent,
            assigned_agent=None,
            status=TaskStatus.PENDING,
            created_at=created,
            updated_at=created,
            metadata=metadata or {},
            resource_profile=resource_profile,
        )

        with self._lock:
            self._tasks[task_id] = record
            if not self._attempt_dispatch(record):
                self._enqueue_pending(record)
        return record

    # Backwards compatibility -------------------------------------------------
    submit_task = schedule_task

    def run_pending(self, limit: Optional[int] = None) -> List[TaskRecord]:
        """Attempt to dispatch queued tasks based on priority order."""

        dispatched: List[TaskRecord] = []
        with self._lock:
            processed = 0
            while self._pending_heap and (limit is None or processed < limit):
                priority, created, task_id = heapq.heappop(self._pending_heap)
                if task_id not in self._pending_index:
                    continue
                self._pending_index.discard(task_id)
                record = self._tasks.get(task_id)
                if record is None or record.status is not TaskStatus.PENDING:
                    continue
                if self._attempt_dispatch(record, from_queue=True):
                    dispatched.append(record)
                    processed += 1
                else:
                    # Conditions still not satisfied; requeue and stop to avoid busy loop
                    self._enqueue_pending(record)
                    break
        return dispatched

    def reconcile(self) -> List[TaskRecord]:
        """Alias for :meth:`run_pending` to support legacy call sites."""

        return self.run_pending()

    def complete_task(self, task_id: str, result: Optional[Any] = None) -> TaskRecord:
        with self._lock:
            record = self._require_task(task_id)
            if record.assigned_agent:
                self._agent_load[record.assigned_agent] = max(
                    0, self._agent_load[record.assigned_agent] - 1
                )
            record.result = result
            record.assigned_agent = None
            self._update_status(
                record, TaskStatus.COMPLETED, "Task completed successfully"
            )
            self.run_pending()
            return record

    def fail_task(self, task_id: str, error: str) -> TaskRecord:
        with self._lock:
            record = self._require_task(task_id)
            previous_agent = record.assigned_agent
            if previous_agent is not None:
                self._agent_load[previous_agent] = max(
                    0, self._agent_load[previous_agent] - 1
                )
                record.excluded_agents.add(previous_agent)
            record.error = error
            record.assigned_agent = None

            if record.attempts <= self.max_retries:
                self._update_status(record, TaskStatus.PENDING, error)
                if self._attempt_dispatch(
                    record,
                    from_queue=True,
                    success_message="Reassigned to agent after failure",
                ):
                    return record
                self._enqueue_pending(record)
                self.run_pending()
                return record

            self._update_status(record, TaskStatus.FAILED, error)
            return record

    def cancel_task(
        self, task_id: str, reason: str = "Cancelled by request"
    ) -> TaskRecord:
        with self._lock:
            record = self._require_task(task_id)
            if record.status in {TaskStatus.COMPLETED, TaskStatus.CANCELLED}:
                return record
            if record.assigned_agent:
                self._agent_load[record.assigned_agent] = max(
                    0, self._agent_load[record.assigned_agent] - 1
                )
            record.error = reason
            record.assigned_agent = None
            self._pending_index.discard(task_id)
            self._update_status(record, TaskStatus.CANCELLED, reason)
            self.run_pending()
            return record

    def get_task(self, task_id: str) -> TaskRecord:
        with self._lock:
            return self._require_task(task_id)

    def list_tasks(
        self, statuses: Optional[Iterable[TaskStatus]] = None
    ) -> List[TaskRecord]:
        with self._lock:
            records = list(self._tasks.values())
        if statuses is None:
            return records
        allowed = {status for status in statuses}
        return [record for record in records if record.status in allowed]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _require_task(self, task_id: str) -> TaskRecord:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"Unknown task_id {task_id}") from exc


__all__ = [
    "Agent",
    "TaskStatus",
    "TaskPriority",
    "ResourceProfile",
    "ResourceSnapshot",
    "TaskScheduler",
    "TaskRecord",
    "TaskLogEntry",
]
