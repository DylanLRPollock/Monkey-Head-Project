"""Shared dataclasses used by GUI and command-center surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from typing import Literal

PhaseStatus = Literal[
    "not_started",
    "in_progress",
    "blocked",
    "ready_for_pr",
    "merged",
]
RiskLevel = Literal["low", "medium", "high", "critical"]
RepoRole = Literal["runtime", "cockpit", "dashboard", "website", "tooling"]
RunStatus = Literal["passed", "failed", "pending", "skipped"]
DataMode = Literal["mock", "live", "local"]


@dataclass
class RepoStatus:
    name: str
    full_name: str
    role: RepoRole
    description: str
    default_branch: str = "main"
    url: str = ""
    open_prs: int | None = None
    open_issues: int | None = None
    latest_workflow_status: str | None = None
    latest_commit: str | None = None
    data_mode: DataMode = "mock"


@dataclass
class MigrationPhase:
    id: str
    title: str
    target_repo: str
    status: PhaseStatus
    risk: RiskLevel
    owner: str = ""
    branch: str = ""
    pr_url: str = ""
    checklist: list[str] = field(default_factory=list)
    validation_commands: list[str] = field(default_factory=list)
    notes: str = ""
    blockers: list[str] = field(default_factory=list)


@dataclass
class ValidationCommand:
    id: str
    repo: str
    command: str
    purpose: str
    expected_result: str
    risk: RiskLevel = "low"
    phase_id: str | None = None
    notes: str = ""
    copy_only: bool = True


@dataclass
class V1RunRecord:
    id: str
    fixture: str
    status: RunStatus
    transcription_status: str = ""
    cognition_status: str = ""
    response_text: str = ""
    error: str = ""
    raw: dict[str, object] = field(default_factory=dict)


@dataclass
class OperatorPanelState:
    api_url: str = "http://127.0.0.1:1995"
    health_status: str = "unknown"
    memory_status: str = "mock"
    governance_status: str = "mock"
    connector_status: str = "mock"
    runtime_status: str = "standby"
    ffmpeg_status: str = "unknown"
    v1_status: str = "mock"
    mock_only: bool = True


def dataclass_to_dict(value: object) -> dict[str, object]:
    """Convert a GUI dataclass to a JSON-safe dict."""

    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "model_dump"):
        return dict(value.model_dump())
    raise TypeError(f"Unsupported value for dataclass_to_dict: {type(value)!r}")


def dataclass_list_to_dicts(values: list[object]) -> list[dict[str, object]]:
    """Convert a list of GUI dataclasses to JSON-safe dicts."""

    return [dataclass_to_dict(value) for value in values]


__all__ = [
    "DataMode",
    "MigrationPhase",
    "OperatorPanelState",
    "PhaseStatus",
    "RepoRole",
    "RepoStatus",
    "RiskLevel",
    "RunStatus",
    "V1RunRecord",
    "ValidationCommand",
    "dataclass_list_to_dicts",
    "dataclass_to_dict",
]
