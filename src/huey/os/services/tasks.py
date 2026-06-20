"""Task API service helpers and response models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from huey.os.core.task_scheduler import (
    Agent,
    ResourceProfile,
    TaskPriority,
    TaskRecord,
    TaskStatus,
)


class ResourceProfileModel(BaseModel):
    """API schema exposing the scheduler resource hints."""

    cpu: float = Field(0.3, ge=0.0, le=1.0, description="Expected CPU utilisation bias")
    memory: float = Field(
        0.2, ge=0.0, le=1.0, description="Expected memory utilisation bias"
    )
    battery: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Battery drain sensitivity; higher values require higher charge.",
    )
    gpu: float = Field(
        0.0, ge=0.0, le=1.0, description="Relative GPU demand if applicable"
    )

    def to_profile(self) -> ResourceProfile:
        return ResourceProfile(
            cpu=self.cpu, memory=self.memory, battery=self.battery, gpu=self.gpu
        )


class ResourceSnapshotModel(BaseModel):
    """Current host health metrics observed during scheduling decisions."""

    timestamp: Optional[float] = None
    cpu_percent: Optional[float] = None
    memory_available: Optional[float] = None
    memory_total: Optional[float] = None
    battery_percent: Optional[float] = None
    notes: Optional[str] = None


class TaskHistoryEntry(BaseModel):
    """Chronological log entries captured for each task."""

    timestamp: float
    status: TaskStatus
    message: str


class TaskResponse(BaseModel):
    """Serialized representation of a scheduled task."""

    task_id: str
    command: str
    priority: int
    requested_agent: Optional[Agent]
    assigned_agent: Optional[Agent]
    status: TaskStatus
    created_at: float
    updated_at: float
    attempts: int
    result: Optional[Any]
    error: Optional[str]
    metadata: Dict[str, Any]
    resource_profile: ResourceProfileModel
    snapshot: Optional[ResourceSnapshotModel]
    history: List[TaskHistoryEntry]

    @classmethod
    def from_record(cls, record: TaskRecord) -> "TaskResponse":
        snapshot = None
        if record.snapshot is not None:
            snapshot = ResourceSnapshotModel(
                timestamp=record.snapshot.timestamp,
                cpu_percent=record.snapshot.cpu_percent,
                memory_available=record.snapshot.memory_available,
                memory_total=record.snapshot.memory_total,
                battery_percent=record.snapshot.battery_percent,
                notes=record.snapshot.notes,
            )
        return cls(
            task_id=record.task_id,
            command=record.command,
            priority=int(record.priority),
            requested_agent=record.requested_agent,
            assigned_agent=record.assigned_agent,
            status=record.status,
            created_at=record.created_at,
            updated_at=record.updated_at,
            attempts=record.attempts,
            result=record.result,
            error=record.error,
            metadata=record.metadata,
            resource_profile=ResourceProfileModel(
                cpu=record.resource_profile.cpu,
                memory=record.resource_profile.memory,
                battery=record.resource_profile.battery,
                gpu=record.resource_profile.gpu,
            ),
            snapshot=snapshot,
            history=[
                TaskHistoryEntry(
                    timestamp=entry.timestamp,
                    status=entry.status,
                    message=entry.message,
                )
                for entry in record.history
            ],
        )


class TaskSubmissionRequest(BaseModel):
    """Payload for creating a new task via the scheduler."""

    command: str = Field(
        ..., description="Instruction to execute within the agent context"
    )
    priority: TaskPriority = Field(
        TaskPriority.NORMAL,
        description="Relative priority for queue ordering; higher values run sooner.",
    )
    requested_agent: Optional[Agent] = Field(
        None, description="Preferred agent when coordination requires affinity"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary metadata echoed back in task status queries.",
    )
    resource_profile: Optional[ResourceProfileModel] = Field(
        None,
        description="Expected resource intensity. Defaults are tuned for general work.",
    )


class TaskListResponse(BaseModel):
    """Container for multiple tasks."""

    tasks: List[TaskResponse]
