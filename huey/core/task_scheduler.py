"""Task scheduling and resource aware assignment for HueyOS agents."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

try:  # pragma: no cover - psutil optional at runtime
    import psutil  # type: ignore
except Exception:  # pragma: no cover - provide stub behaviour
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


class TaskPriority(int, Enum):
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

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the record to a JSON compatible mapping."""

        return {
            "task_id": self.task_id,
            "command": self.command,
            "priority": int(self.priority),
            "requested_agent": self.requested_agent.value if self.requested_agent else None,
            "assigned_agent": self.assigned_agent.value if self.assigned_agent else None,
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
                "memory_available": self.snapshot.memory_available if self.snapshot else None,
                "memory_total": self.snapshot.memory_total if self.snapshot else None,
                "battery_percent": self.snapshot.battery_percent if self.snapshot else None,
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
    ) -> None:
        self.cpu_threshold = cpu_threshold
        self.battery_threshold = battery_threshold
        self.min_free_memory = min_free_memory
        self.health_provider = health_provider or self._default_health_provider
        self.max_retries = max_retries
        self._lock = RLock()
        self._tasks: Dict[str, TaskRecord] = {}
        self._agent_load: Dict[Agent, int] = {Agent.SPARK: 0, Agent.ZAP: 0}

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

        if reason is None and snapshot.memory_available is not None and snapshot.memory_total:
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
    def _select_agent(self, requested: Optional[Agent]) -> Agent:
        """Choose an agent based on requested preference and load."""

        if requested is not None:
            return requested
        # Prefer the agent with fewer running tasks
        spark_load = self._agent_load[Agent.SPARK]
        zap_load = self._agent_load[Agent.ZAP]
        return Agent.SPARK if spark_load <= zap_load else Agent.ZAP

    def _log_transition(self, record: TaskRecord, message: str) -> None:
        entry = TaskLogEntry(timestamp=time.time(), status=record.status, message=message)
        record.history.append(entry)
        LOGGER.debug("Task %s: %s", record.task_id, message)

    def _update_status(self, record: TaskRecord, status: TaskStatus, message: str) -> None:
        record.status = status
        record.updated_at = time.time()
        self._log_transition(record, message)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def submit_task(
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
            can_run, reason, snapshot = self._system_ready(resource_profile)
            record.snapshot = snapshot
            if can_run:
                agent = self._select_agent(requested_agent)
                record.assigned_agent = agent
                record.attempts += 1
                self._agent_load[agent] += 1
                self._update_status(record, TaskStatus.RUNNING, "Task dispatched to agent")
            else:
                self._update_status(
                    record,
                    TaskStatus.PENDING,
                    reason or "System health unknown; task pending",
                )
            self._tasks[task_id] = record

        return record

    def reconcile(self) -> List[TaskRecord]:
        """Re-evaluate pending tasks to see if they can now be dispatched."""

        dispatched: List[TaskRecord] = []
        with self._lock:
            for record in sorted(
                self._tasks.values(),
                key=lambda r: (int(-r.priority), r.created_at),
            ):
                if record.status is not TaskStatus.PENDING:
                    continue
                can_run, reason, snapshot = self._system_ready(record.resource_profile)
                record.snapshot = snapshot
                if not can_run:
                    self._log_transition(record, reason or "Still pending due to health")
                    continue
                agent = self._select_agent(record.requested_agent)
                record.assigned_agent = agent
                record.attempts += 1
                self._agent_load[agent] += 1
                self._update_status(record, TaskStatus.RUNNING, "Task dispatched during reconcile")
                dispatched.append(record)
        return dispatched

    def complete_task(self, task_id: str, result: Optional[Any] = None) -> TaskRecord:
        with self._lock:
            record = self._require_task(task_id)
            if record.assigned_agent:
                self._agent_load[record.assigned_agent] = max(
                    0, self._agent_load[record.assigned_agent] - 1
                )
            record.result = result
            self._update_status(record, TaskStatus.COMPLETED, "Task completed successfully")
            return record

    def fail_task(self, task_id: str, error: str) -> TaskRecord:
        with self._lock:
            record = self._require_task(task_id)
            record.error = error
            previous_agent = record.assigned_agent
            if previous_agent is not None:
                self._agent_load[previous_agent] = max(
                    0, self._agent_load[previous_agent] - 1
                )

            if record.attempts <= self.max_retries:
                alternate = self._alternate_agent(previous_agent)
                can_run, reason, snapshot = self._system_ready(record.resource_profile)
                record.snapshot = snapshot
                if can_run:
                    record.assigned_agent = alternate
                    record.attempts += 1
                    self._agent_load[alternate] += 1
                    self._update_status(
                        record,
                        TaskStatus.RUNNING,
                        f"Reassigned to {alternate.value} after failure",
                    )
                    return record
                self._log_transition(record, reason or "Reassignment blocked by health")

            record.assigned_agent = None
            self._update_status(record, TaskStatus.FAILED, error)
            return record

    def cancel_task(self, task_id: str, reason: str = "Cancelled by request") -> TaskRecord:
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
            self._update_status(record, TaskStatus.CANCELLED, reason)
            return record

    def get_task(self, task_id: str) -> TaskRecord:
        with self._lock:
            return self._require_task(task_id)

    def list_tasks(self, statuses: Optional[Iterable[TaskStatus]] = None) -> List[TaskRecord]:
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

    def _alternate_agent(self, current: Optional[Agent]) -> Agent:
        if current is None:
            return self._select_agent(None)
        return Agent.ZAP if current is Agent.SPARK else Agent.SPARK


__all__ = [
    "Agent",
    "TaskStatus",
    "TaskPriority",
    "ResourceProfile",
    "ResourceSnapshot",
    "TaskScheduler",
    "TaskRecord",
]
