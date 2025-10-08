"""FastAPI application exposing the HueyOS control surface."""

from __future__ import annotations

import asyncio
import platform
import shutil
import socket
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

try:  # pragma: no cover - psutil is an optional dependency at runtime
    import psutil  # type: ignore
except Exception:  # pragma: no cover - fall back to stdlib metrics
    psutil = None  # type: ignore[assignment]

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from huey.memory.PY.ai_processor import AIProcessor
from monkey_head.core.resilience import (
    CrashRecoveryManager,
    EmergencyGovernanceController,
)
from monkey_head.core.task_scheduler import (
    Agent,
    ResourceProfile,
    TaskPriority,
    TaskRecord,
    TaskScheduler,
    TaskStatus,
)
from monkey_head.hardware import create_default_sensor_manager
from monkey_head.hardware.plugins import (
    SensorReading,
    list_sensor_plugin_metadata,
    list_sensor_plugins,
)
from monkey_head.honeycomb_index import HoneycombIndex
from monkey_head.honeycomb_monitor import HoneycombMonitor
from monkey_head.honeycomb_storage import HoneycombStorage
from monkey_head.network import NetworkManager
from monkey_head.pdf_utils import find_pdf, list_available_pdfs
from monkey_head.power import BatteryMonitor
from monkey_head.system_checks import system_check
from monkey_head.utils.auto_sort import auto_sort_memory
from monkey_head.utils.paths import get_memory_path

__all__ = [
    "AI_PROCESSOR",
    "AnalyzeTextRequest",
    "AnalyzeTextResponse",
    "AutoSortRequest",
    "AutoSortResponse",
    "BATTERY_MONITOR",
    "BatteryStatusResponse",
    "CRASH_MANAGER",
    "ComputeMeanRequest",
    "ComputeMeanResponse",
    "CrashEventModel",
    "CrashPollResponse",
    "EMERGENCY_CONTROLLER",
    "EmergencyActionRequest",
    "EmergencyExitRequest",
    "EmergencyModeRequest",
    "EmergencyServiceStatus",
    "EmergencyStatusResponse",
    "HoneycombContentUsage",
    "HoneycombGrowthSample",
    "HoneycombUsageEntry",
    "HoneycombUsageResponse",
    "HoneycombUsageTotals",
    "ManualOverrideRequest",
    "MonitoredProcessStatusModel",
    "NETWORK_MANAGER",
    "NetworkStatusResponse",
    "PDFDetailResponse",
    "PDFListResponse",
    "PowerEventResponse",
    "ProcessTextRequest",
    "ProcessTextResponse",
    "ResourceProfileModel",
    "ResourceSnapshotModel",
    "SCHEDULER",
    "SENSOR_MANAGER",
    "SensorHistoryResponse",
    "SensorListResponse",
    "SensorMetadata",
    "SensorPluginsResponse",
    "SensorPollAllResponse",
    "SensorReadingResponse",
    "SensorRegistrationRequest",
    "SensorRegistrationResponse",
    "ServiceStatus",
    "ServicesOverviewResponse",
    "SystemCheckResponse",
    "SystemStatusResponse",
    "TaskHistoryEntry",
    "TaskListResponse",
    "TaskResponse",
    "TaskSubmissionRequest",
    "admin_health_check",
    "admin_system_check",
    "ai_analyze_text",
    "ai_compute_mean",
    "ai_process_text",
    "app",
    "auto_sort",
    "battery_status",
    "cancel_task",
    "emergency_authorised_action",
    "emergency_status",
    "ensure_network_connectivity",
    "enter_emergency_mode",
    "exit_emergency_mode",
    "get_task",
    "healthz",
    "honeycomb_usage",
    "list_monitored_processes",
    "list_pdfs",
    "list_sensors",
    "list_services",
    "list_tasks_endpoint",
    "locate_pdf",
    "manual_restart_monitored_process",
    "network_status",
    "override_monitored_process",
    "poll_all_sensors",
    "poll_crash_manager",
    "poll_sensor",
    "power_should_shutdown",
    "register_sensor",
    "remove_sensor",
    "sensor_history",
    "sensor_plugins",
    "start_service",
    "stop_service",
    "stream_all_sensors",
    "stream_sensor",
    "submit_task",
    "system_status",
    "trigger_shutdown",
    "watchdog_ping",
]


app = FastAPI(
    title="HueyOS API",
    version="0.2.0",
    description=(
        "HueyOS exposes robotic control, knowledge management, and automation "
        "capabilities through a unified API for integrations and operator tooling."
    ),
)


class SystemStatusResponse(BaseModel):
    """Structured information about the running HueyOS environment."""

    system: str = Field(..., description="Operating system family (e.g. Linux, Darwin)")
    release: str = Field(..., description="Operating system release version")
    version: str = Field(..., description="Detailed OS version string")
    architecture: str = Field(..., description="CPU architecture reported by the OS")
    hostname: str = Field(..., description="Network hostname of the HueyOS node")
    python_version: str = Field(..., description="Version of Python executing HueyOS")
    cpu_count: Optional[int] = Field(
        None, description="Number of CPU cores detected on the host"
    )
    memory_total: Optional[int] = Field(
        None, description="Total physical memory reported in bytes"
    )
    memory_available: Optional[int] = Field(
        None, description="Available memory reported in bytes"
    )
    uptime_seconds: Optional[float] = Field(
        None, description="Seconds since the system booted, if available"
    )
    boot_time: Optional[float] = Field(
        None, description="POSIX timestamp of the last system boot"
    )
    disk_free: Optional[int] = Field(
        None, description="Free disk space on the root filesystem in bytes"
    )
    memory_path: str = Field(..., description="Primary HueyOS memory directory path")


class PDFListResponse(BaseModel):
    """List of PDFs discoverable by HueyOS."""

    pdfs: List[str] = Field(..., description="Sorted PDF filenames")
    directory: Optional[str] = Field(
        None, description="Directory scanned for PDF files when available"
    )


class PDFDetailResponse(BaseModel):
    """Details about a specific PDF accessible to HueyOS."""

    filename: str = Field(..., description="Requested PDF filename")
    found: bool = Field(..., description="Whether the PDF could be located")
    path: Optional[str] = Field(None, description="Absolute filesystem path if found")


class AutoSortRequest(BaseModel):
    """Parameters used to reorganise files in the shared memory directory."""

    source_dir: Optional[str] = Field(
        None,
        description="Directory containing unsorted files. Defaults to memory/RAW.",
    )
    destination_root: Optional[str] = Field(
        None,
        description="Destination directory that will receive typed subdirectories.",
    )
    dry_run: bool = Field(
        False,
        description="When true, only report planned moves without modifying files.",
    )


class AutoSortResponse(BaseModel):
    """Summary of the work performed by :func:`auto_sort_memory`."""

    source: str
    destination: str
    moved: List[str]
    skipped: List[str]


class HoneycombUsageEntry(BaseModel):
    """Metrics for a single comb inside the honeycomb storage."""

    comb: str
    cells: int
    payload_bytes: int
    oldest: Optional[float]
    newest: Optional[float]


class HoneycombContentUsage(BaseModel):
    """Aggregated metrics for a logical content type."""

    content_type: str
    cells: int
    payload_bytes: int
    oldest: Optional[float]
    newest: Optional[float]


class HoneycombGrowthSample(BaseModel):
    """Historical growth sample for the honeycomb."""

    date: str
    cells: int


class HoneycombUsageTotals(BaseModel):
    """Aggregate totals summarising honeycomb usage."""

    cells: int
    payload_bytes: int
    combs: int
    last_update: Optional[float]


class HoneycombUsageResponse(BaseModel):
    """Response payload describing honeycomb utilisation."""

    summary: List[HoneycombUsageEntry]
    totals: HoneycombUsageTotals
    content_types: List[HoneycombContentUsage]
    growth: List[HoneycombGrowthSample]


class ProcessTextRequest(BaseModel):
    """Body payload for the AI text processing endpoint."""

    text: str = Field(..., description="Plain text to process with HueyOS AI tools")


class ProcessTextResponse(BaseModel):
    """Response model when streaming is not requested."""

    processed_text: str = Field(..., description="Text after AIProcessor transformation")


class ComputeMeanRequest(BaseModel):
    """Body payload for computing the arithmetic mean of numeric values."""

    numbers: List[float] = Field(..., description="List of numbers to average")


class ComputeMeanResponse(BaseModel):
    """Response payload for the mean computation endpoint."""

    mean: float = Field(..., description="Arithmetic mean of the provided numbers")


class AnalyzeTextRequest(BaseModel):
    """Body payload for the text analysis endpoint."""

    text: str = Field(..., description="Plain text to analyse with AIProcessor")


class AnalyzeTextResponse(BaseModel):
    """Structured metrics returned by the text analysis endpoint."""

    metrics: Dict[str, int] = Field(
        ..., description="Dictionary of metrics produced by AIProcessor.analyze_data"
    )


class SensorMetadata(BaseModel):
    """Metadata describing a configured sensor plugin."""

    name: str
    plugin: str
    module: str
    config: Dict[str, Any] = Field(default_factory=dict)


class SensorPluginsResponse(BaseModel):
    """Response model listing available sensor plugins."""

    plugins: List[str]
    metadata: List[Dict[str, Any]] = Field(
        default_factory=list, description="Detailed metadata for available plugins"
    )


class SensorListResponse(BaseModel):
    """Response payload enumerating configured sensors."""

    sensors: List[SensorMetadata]


class SensorRegistrationRequest(BaseModel):
    """Request body for registering a sensor instance."""

    name: str
    plugin: str
    config: Dict[str, Any] = Field(default_factory=dict)


class SensorRegistrationResponse(BaseModel):
    """Response describing a registered sensor."""

    name: str
    plugin: str
    config: Dict[str, Any]


class SensorReadingResponse(BaseModel):
    """Single sensor reading returned to API clients."""

    name: str
    value: Any
    timestamp: float
    provenance: Dict[str, Any]


class SensorHistoryResponse(BaseModel):
    """Historical readings for a specific sensor."""

    sensor: str
    readings: List[SensorReadingResponse]


class SensorPollAllResponse(BaseModel):
    """Response returned when polling all configured sensors."""

    readings: List[SensorReadingResponse]


class NetworkStatusResponse(BaseModel):
    """Current network connectivity status."""

    active_interface: Optional[str]
    interfaces: Dict[str, Dict[str, Optional[float]]]
    wired_available: bool
    wifi_available: bool
    connected: bool
    last_checked: float


class BatteryStatusResponse(BaseModel):
    """Current battery metrics."""

    percent: Optional[float]
    secs_left: Optional[float]
    power_plugged: Optional[bool]
    estimated_runtime_minutes: Optional[float]


class PowerEventResponse(BaseModel):
    """Response describing a power management action."""

    timestamp: float
    action: str
    metadata: Dict[str, Any]


class ServiceStatus(BaseModel):
    """Runtime status for a managed HueyOS service."""

    name: str = Field(..., description="Human readable service identifier")
    status: str = Field(..., description="Current state such as 'running' or 'stopped'")
    last_changed: float = Field(
        default_factory=lambda: time.time(),
        description="Unix timestamp when the status last changed",
    )


class ServicesOverviewResponse(BaseModel):
    """Aggregate overview of all tracked service states."""

    services: List[ServiceStatus] = Field(
        ..., description="Collection of service status objects"
    )


class SystemCheckResponse(BaseModel):
    """Result of executing the HueyOS system check suite."""

    results: Dict[str, bool] = Field(..., description="Individual check outcomes")
    passed: bool = Field(..., description="True when every reported check passed")


class CrashEventModel(BaseModel):
    """Serialized representation of :class:`CrashEvent`."""

    process: str
    timestamp: float
    restarted: bool
    message: str
    metadata: Dict[str, Any]


class MonitoredProcessStatusModel(BaseModel):
    """Status information for a process monitored by the resilience manager."""

    name: str
    healthy: bool
    auto_restart: bool
    last_heartbeat: Optional[float]
    last_restart: Optional[float]
    restart_attempts: int
    manual_override_reason: Optional[str]


class CrashPollResponse(BaseModel):
    """Response emitted after polling the crash recovery manager."""

    events: List[CrashEventModel]


class ManualOverrideRequest(BaseModel):
    """Request payload used to toggle automatic crash recovery."""

    auto_restart: bool = Field(
        ..., description="Set to False to disable automatic restarts"
    )
    reason: Optional[str] = Field(
        None,
        description="Operator reason recorded when disabling automatic restarts",
    )


class EmergencyServiceStatus(BaseModel):
    """Metadata about a service managed during emergency mode."""

    name: str
    essential: bool
    managed: bool


class EmergencyStatusResponse(BaseModel):
    """Snapshot of the emergency governance controller state."""

    state: str
    active_since: Optional[float]
    reason: Optional[str]
    triggered_by: Optional[str]
    approvals: List[str]
    services: List[EmergencyServiceStatus]


class EmergencyModeRequest(BaseModel):
    """Parameters needed to activate emergency mode."""

    triggered_by: str = Field(..., description="Agent or operator requesting mode")
    reason: str = Field(..., description="Human readable reason for emergency")
    approvals: List[str] = Field(
        default_factory=list,
        description="List of additional approvers for quorum validation",
    )


class EmergencyExitRequest(BaseModel):
    """Parameters required to exit emergency mode."""

    requested_by: str = Field(..., description="Operator requesting exit")
    approvals: List[str] = Field(
        default_factory=list,
        description="Approvers confirming exit is safe",
    )


class EmergencyActionRequest(BaseModel):
    """Request payload for actions that require dual authorisation."""

    actor: str = Field(..., description="Agent initiating the action")
    approvals: List[str] = Field(
        default_factory=list,
        description="Additional approvers satisfying quorum",
    )
    action: str = Field(..., description="Description of the requested action")


AI_PROCESSOR = AIProcessor()
SCHEDULER = TaskScheduler()
CRASH_MANAGER = CrashRecoveryManager()
EMERGENCY_CONTROLLER = EmergencyGovernanceController()
_SERVICE_STATES: Dict[str, ServiceStatus] = {}
SENSOR_MANAGER = create_default_sensor_manager()
NETWORK_MANAGER = NetworkManager()
BATTERY_MONITOR = BatteryMonitor()


def _reading_to_response(reading: SensorReading) -> SensorReadingResponse:
    return SensorReadingResponse(
        name=reading.name,
        value=reading.value,
        timestamp=reading.timestamp,
        provenance=reading.provenance,
    )


async def _sensor_stream(sensor_name: Optional[str]):
    queue = SENSOR_MANAGER.subscribe(sensor_name)
    try:
        while True:
            reading = await queue.get()
            payload = _reading_to_response(reading).json()
            yield f"data: {payload}\n\n"
    finally:
        SENSOR_MANAGER.unsubscribe(queue)



class ResourceProfileModel(BaseModel):
    """API schema exposing the scheduler resource hints."""

    cpu: float = Field(0.3, ge=0.0, le=1.0, description="Expected CPU utilisation bias")
    memory: float = Field(0.2, ge=0.0, le=1.0, description="Expected memory utilisation bias")
    battery: float = Field(
        0.1,
        ge=0.0,
        le=1.0,
        description="Battery drain sensitivity; higher values require higher charge.",
    )
    gpu: float = Field(0.0, ge=0.0, le=1.0, description="Relative GPU demand if applicable")

    def to_profile(self) -> ResourceProfile:
        return ResourceProfile(
            cpu=self.cpu,
            memory=self.memory,
            battery=self.battery,
            gpu=self.gpu,
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

    command: str = Field(..., description="Instruction to execute within the agent context")
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


def _build_system_status() -> SystemStatusResponse:
    """Collect metrics describing the current operating environment."""

    uname = platform.uname()
    memory_path = get_memory_path(create=True)
    cpu_count: Optional[int] = None
    mem_total: Optional[int] = None
    mem_available: Optional[int] = None
    uptime: Optional[float] = None
    boot_time: Optional[float] = None

    if psutil is not None:  # pragma: no branch - psutil availability determined above
        try:
            cpu_count = psutil.cpu_count(logical=True)
        except Exception:  # pragma: no cover - defensive guard
            cpu_count = None
        try:
            virtual_mem = psutil.virtual_memory()
        except Exception:  # pragma: no cover - defensive guard
            virtual_mem = None
        if virtual_mem is not None:
            mem_total = int(virtual_mem.total)
            mem_available = int(virtual_mem.available)
        try:
            boot_time = float(psutil.boot_time())
        except Exception:  # pragma: no cover - defensive guard
            boot_time = None
        if boot_time is not None:
            uptime = time.time() - boot_time
    else:
        cpu_count = None

    disk_free: Optional[int] = None
    try:
        disk_usage = shutil.disk_usage(Path("/"))
    except Exception:  # pragma: no cover - defensive guard
        disk_usage = None
    if disk_usage is not None:
        disk_free = int(disk_usage.free)

    return SystemStatusResponse(
        system=uname.system,
        release=uname.release,
        version=uname.version,
        architecture=uname.machine,
        hostname=socket.gethostname(),
        python_version=platform.python_version(),
        cpu_count=cpu_count,
        memory_total=mem_total,
        memory_available=mem_available,
        uptime_seconds=uptime,
        boot_time=boot_time,
        disk_free=disk_free,
        memory_path=str(memory_path),
    )


def _stream_text(text: str, chunk_size: int = 64) -> AsyncGenerator[str, None]:
    """Yield ``text`` in fixed-sized chunks for streaming responses."""

    async def generator() -> AsyncGenerator[str, None]:
        for start in range(0, len(text), chunk_size):
            yield text[start : start + chunk_size]
            await asyncio.sleep(0)

    return generator()


def _update_service_status(name: str, status_value: str) -> ServiceStatus:
    """Persist and return the state of a HueyOS service."""

    state = ServiceStatus(name=name, status=status_value, last_changed=time.time())
    _SERVICE_STATES[name] = state
    return state


def _monitor_status(name: str) -> MonitoredProcessStatusModel:
    """Return the status object for ``name`` or raise ``KeyError``."""

    for status in CRASH_MANAGER.statuses():
        if status["name"] == name:
            return MonitoredProcessStatusModel(**status)
    raise KeyError(f"Unknown monitored process: {name}")


def _register_default_emergency_services() -> None:
    """Register baseline services that are paused during emergencies."""

    service_names = ("spark-agent", "zap-agent", "ollama")
    for service_name in service_names:
        EMERGENCY_CONTROLLER.register_service(
            service_name,
            stop=lambda name=service_name: _update_service_status(name, "stopped"),
            start=lambda name=service_name: _update_service_status(name, "running"),
            essential=False,
        )


_register_default_emergency_services()


@app.get("/healthz", tags=["System"])
def healthz() -> Dict[str, str]:
    """Lightweight probe used by orchestrators to ensure the API is responsive."""

    return {"status": "ok", "service": "hueyos"}


@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Task Management"],
)
def submit_task(request: TaskSubmissionRequest) -> TaskResponse:
    """Submit a task for execution by Spark or Zap."""

    profile = (
        request.resource_profile.to_profile()
        if request.resource_profile is not None
        else ResourceProfile()
    )
    record = SCHEDULER.submit_task(
        command=request.command,
        priority=request.priority,
        requested_agent=request.requested_agent,
        metadata=dict(request.metadata),
        resource_profile=profile,
    )
    return TaskResponse.from_record(record)


@app.get("/tasks", response_model=TaskListResponse, tags=["Task Management"])
def list_tasks_endpoint(
    status_filter: Optional[List[TaskStatus]] = Query(
        None,
        alias="status",
        description="Filter results to tasks with the specified status",
    )
) -> TaskListResponse:
    """List known tasks with optional status filters."""

    records = SCHEDULER.list_tasks(status_filter)
    return TaskListResponse(tasks=[TaskResponse.from_record(record) for record in records])


@app.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    tags=["Task Management"],
)
def get_task(task_id: str) -> TaskResponse:
    """Return the scheduler record for a specific task."""

    try:
        record = SCHEDULER.get_task(task_id)
    except KeyError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TaskResponse.from_record(record)


@app.post(
    "/tasks/{task_id}/cancel",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Task Management"],
)
def cancel_task(task_id: str) -> TaskResponse:
    """Cancel a pending or running task."""

    try:
        record = SCHEDULER.cancel_task(task_id)
    except KeyError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TaskResponse.from_record(record)


@app.get("/system/status", response_model=SystemStatusResponse, tags=["System"])
def system_status() -> SystemStatusResponse:
    """Return operating system, hardware, and configuration details for HueyOS."""

    return _build_system_status()


@app.get("/sensors/plugins", response_model=SensorPluginsResponse, tags=["Sensors"])
def sensor_plugins() -> SensorPluginsResponse:
    """List available sensor plugin identifiers."""

    registry = SENSOR_MANAGER.registry
    plugins = list_sensor_plugins(registry)
    metadata = list_sensor_plugin_metadata(registry)
    return SensorPluginsResponse(plugins=plugins, metadata=metadata)


@app.get("/sensors", response_model=SensorListResponse, tags=["Sensors"])
def list_sensors() -> SensorListResponse:
    """Enumerate configured sensors."""

    metadata: List[SensorMetadata] = []
    for entry in SENSOR_MANAGER.list_sensors():
        metadata.append(
            SensorMetadata(
                name=entry["name"],
                plugin=str(entry.get("plugin")),
                module=str(entry.get("module")),
                config=dict(entry.get("config") or {}),
            )
        )
    return SensorListResponse(sensors=metadata)


@app.post(
    "/sensors/register",
    response_model=SensorRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Sensors"],
)
def register_sensor(request: SensorRegistrationRequest) -> SensorRegistrationResponse:
    """Register a new sensor plugin instance at runtime."""

    try:
        SENSOR_MANAGER.add_sensor(request.plugin, request.name, request.config)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown sensor plugin {request.plugin!r}",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SensorRegistrationResponse(
        name=request.name,
        plugin=request.plugin,
        config=dict(request.config),
    )


@app.delete("/sensors/{sensor_name}", tags=["Sensors"])
def remove_sensor(sensor_name: str) -> Dict[str, str]:
    """Remove a configured sensor instance."""

    if SENSOR_MANAGER.get_sensor(sensor_name) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    SENSOR_MANAGER.remove_sensor(sensor_name)
    return {"status": "removed", "sensor": sensor_name}


@app.post(
    "/sensors/{sensor_name}/poll",
    response_model=SensorReadingResponse,
    tags=["Sensors"],
)
def poll_sensor(sensor_name: str) -> SensorReadingResponse:
    """Poll a single sensor and store the reading in honeycomb storage."""

    try:
        reading = SENSOR_MANAGER.poll_sensor(sensor_name)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return _reading_to_response(reading)


@app.post("/sensors/poll", response_model=SensorPollAllResponse, tags=["Sensors"])
def poll_all_sensors() -> SensorPollAllResponse:
    """Poll every configured sensor."""

    readings = [_reading_to_response(reading) for reading in SENSOR_MANAGER.poll_all()]
    return SensorPollAllResponse(readings=readings)


@app.get(
    "/sensors/{sensor_name}/history",
    response_model=SensorHistoryResponse,
    tags=["Sensors"],
)
def sensor_history(
    sensor_name: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of readings to return"),
) -> SensorHistoryResponse:
    """Return historical sensor readings from honeycomb storage."""

    if SENSOR_MANAGER.get_sensor(sensor_name) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    history = SENSOR_MANAGER.load_history(sensor_name, limit=limit)
    readings = [SensorReadingResponse(**record) for record in history]
    return SensorHistoryResponse(sensor=sensor_name, readings=readings)


@app.get("/sensors/{sensor_name}/stream", tags=["Sensors"])
async def stream_sensor(sensor_name: str) -> StreamingResponse:
    """Stream real-time readings for ``sensor_name`` using server-sent events."""

    if SENSOR_MANAGER.get_sensor(sensor_name) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found")
    return StreamingResponse(_sensor_stream(sensor_name), media_type="text/event-stream")


@app.get("/sensors/stream", tags=["Sensors"])
async def stream_all_sensors() -> StreamingResponse:
    """Stream readings for all sensors using server-sent events."""

    return StreamingResponse(_sensor_stream(None), media_type="text/event-stream")


@app.get("/network/status", response_model=NetworkStatusResponse, tags=["Network"])
def network_status() -> NetworkStatusResponse:
    """Return the most recent network connectivity snapshot."""

    status_snapshot = NETWORK_MANAGER.check_status()
    return NetworkStatusResponse(**status_snapshot.__dict__)


@app.post("/network/ensure", response_model=NetworkStatusResponse, tags=["Network"])
def ensure_network_connectivity() -> NetworkStatusResponse:
    """Ensure wired connectivity is preferred with Wi-Fi failover."""

    status_snapshot = NETWORK_MANAGER.ensure_connectivity()
    return NetworkStatusResponse(**status_snapshot.__dict__)


@app.get("/power/battery", response_model=BatteryStatusResponse, tags=["Power"])
def battery_status() -> BatteryStatusResponse:
    """Expose the current battery status."""

    status = BATTERY_MONITOR.get_status()
    return BatteryStatusResponse(**status)


@app.get("/power/should-shutdown", tags=["Power"])
def power_should_shutdown() -> Dict[str, Any]:
    """Return whether the system recommends a safe shutdown."""

    return {
        "should_shutdown": BATTERY_MONITOR.should_shutdown(),
        "threshold": BATTERY_MONITOR.shutdown_threshold,
    }


@app.post("/power/shutdown", response_model=PowerEventResponse, tags=["Power"])
def trigger_shutdown() -> PowerEventResponse:
    """Initiate a safe shutdown sequence."""

    event = BATTERY_MONITOR.initiate_shutdown()
    return PowerEventResponse(timestamp=event.timestamp, action=event.action, metadata=event.metadata)


@app.get(
    "/resilience/monitors",
    response_model=List[MonitoredProcessStatusModel],
    tags=["Resilience"],
)
def list_monitored_processes() -> List[MonitoredProcessStatusModel]:
    """Return the set of processes being watched by the crash manager."""

    return [MonitoredProcessStatusModel(**status) for status in CRASH_MANAGER.statuses()]


@app.post(
    "/resilience/monitors/{name}/override",
    response_model=MonitoredProcessStatusModel,
    tags=["Resilience"],
)
def override_monitored_process(name: str, request: ManualOverrideRequest) -> MonitoredProcessStatusModel:
    """Enable or disable automatic crash recovery for the given process."""

    try:
        status = CRASH_MANAGER.toggle_auto_restart(
            name, request.auto_restart, reason=request.reason
        )
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MonitoredProcessStatusModel(**status)


@app.post(
    "/resilience/monitors/{name}/restart",
    response_model=MonitoredProcessStatusModel,
    tags=["Resilience"],
)
def manual_restart_monitored_process(name: str) -> MonitoredProcessStatusModel:
    """Force a restart for a monitored process regardless of overrides."""

    try:
        CRASH_MANAGER.manual_restart(name)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _monitor_status(name)


@app.post(
    "/resilience/poll",
    response_model=CrashPollResponse,
    tags=["Resilience"],
)
def poll_crash_manager() -> CrashPollResponse:
    """Poll the crash manager and return any crash events."""

    events = [
        CrashEventModel(
            process=event.process,
            timestamp=event.timestamp,
            restarted=event.restarted,
            message=event.message,
            metadata=event.metadata,
        )
        for event in CRASH_MANAGER.poll()
    ]
    return CrashPollResponse(events=events)


@app.post(
    "/resilience/watchdog/ping",
    tags=["Resilience"],
)
def watchdog_ping() -> Dict[str, bool]:
    """Forward a watchdog heartbeat to the host environment."""

    return {"watchdog": CRASH_MANAGER.ping_watchdog()}


@app.get("/memory/pdfs", response_model=PDFListResponse, tags=["Memory"])
def list_pdfs(pdf_dir: Optional[str] = Query(None, description="Override PDF search root")) -> PDFListResponse:
    """List the PDF resources HueyOS can currently access."""

    pdfs = list_available_pdfs(pdf_dir=pdf_dir)
    directory: Optional[str] = None
    if pdfs:
        sample = find_pdf(pdfs[0], pdf_dir=pdf_dir)
        if sample is not None:
            directory = str(sample.parent)
    elif pdf_dir is not None:
        directory = pdf_dir
    return PDFListResponse(pdfs=pdfs, directory=directory)


@app.get(
    "/memory/pdfs/{filename}",
    response_model=PDFDetailResponse,
    tags=["Memory"],
)
def locate_pdf(filename: str, pdf_dir: Optional[str] = Query(None, description="Optional PDF search root")) -> PDFDetailResponse:
    """Resolve an absolute path for a specific PDF."""

    path = find_pdf(filename, pdf_dir=pdf_dir)
    if path is None:
        return PDFDetailResponse(filename=filename, found=False, path=None)
    return PDFDetailResponse(filename=filename, found=True, path=str(path))


@app.post(
    "/memory/auto-sort",
    response_model=AutoSortResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Memory"],
)
def auto_sort(request: AutoSortRequest) -> AutoSortResponse:
    """Trigger automated organisation of files in the HueyOS memory directory."""

    try:
        summary = auto_sort_memory(
            source_dir=request.source_dir,
            destination_root=request.destination_root,
            dry_run=request.dry_run,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AutoSortResponse(**summary)


@app.get(
    "/memory/honeycomb/usage",
    response_model=HoneycombUsageResponse,
    tags=["Memory"],
)
def honeycomb_usage(
    window_days: int = Query(
        30,
        ge=1,
        le=365,
        description="Number of days to include when calculating growth statistics.",
    )
) -> HoneycombUsageResponse:
    """Return aggregate metrics describing honeycomb storage utilisation."""

    with HoneycombStorage() as storage:
        index = HoneycombIndex(storage)
        monitor = HoneycombMonitor(storage, index=index)
        report = monitor.build_usage_report(window_days=window_days)
    summary = [HoneycombUsageEntry(**item) for item in report["summary"]]
    content_types = [HoneycombContentUsage(**item) for item in report["content_types"]]
    totals = HoneycombUsageTotals(**report["totals"])
    growth = [HoneycombGrowthSample(**item) for item in report["growth"]]
    return HoneycombUsageResponse(
        summary=summary,
        totals=totals,
        content_types=content_types,
        growth=growth,
    )


@app.post(
    "/ai/process-text",
    response_model=ProcessTextResponse,
    tags=["AI Tools"],
)
def ai_process_text(
    request: ProcessTextRequest,
    stream: bool = Query(False, description="When true, stream the response body"),
):
    """Apply :class:`AIProcessor` transformations to the supplied text."""

    processed = AI_PROCESSOR.process_data(request.text)
    if stream:
        return StreamingResponse(_stream_text(processed), media_type="text/plain")
    return ProcessTextResponse(processed_text=processed)


@app.post("/ai/compute-mean", response_model=ComputeMeanResponse, tags=["AI Tools"])
def ai_compute_mean(request: ComputeMeanRequest) -> ComputeMeanResponse:
    """Compute the arithmetic mean of a list of numbers using :class:`AIProcessor`."""

    if not request.numbers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one number must be provided to compute a mean.",
        )
    result = AI_PROCESSOR.compute_mean(request.numbers)
    return ComputeMeanResponse(mean=result)


@app.post("/ai/analyze-text", response_model=AnalyzeTextResponse, tags=["AI Tools"])
def ai_analyze_text(request: AnalyzeTextRequest) -> AnalyzeTextResponse:
    """Return lightweight analytics describing the provided text."""

    metrics = AI_PROCESSOR.analyze_data(request.text)
    return AnalyzeTextResponse(metrics=metrics)


@app.get(
    "/governance/emergency/status",
    response_model=EmergencyStatusResponse,
    tags=["Governance"],
)
def emergency_status() -> EmergencyStatusResponse:
    """Return the current emergency governance state."""

    snapshot = EMERGENCY_CONTROLLER.status()
    services = [EmergencyServiceStatus(**service) for service in snapshot["services"]]
    return EmergencyStatusResponse(
        state=snapshot["state"],
        active_since=snapshot["active_since"],
        reason=snapshot["reason"],
        triggered_by=snapshot["triggered_by"],
        approvals=snapshot["approvals"],
        services=services,
    )


@app.post(
    "/governance/emergency/enter",
    response_model=EmergencyStatusResponse,
    tags=["Governance"],
)
def enter_emergency_mode(request: EmergencyModeRequest) -> EmergencyStatusResponse:
    """Enter emergency mode after validating approvals."""

    try:
        EMERGENCY_CONTROLLER.enter_emergency_mode(
            triggered_by=request.triggered_by,
            reason=request.reason,
            approvals=request.approvals,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return emergency_status()


@app.post(
    "/governance/emergency/exit",
    response_model=EmergencyStatusResponse,
    tags=["Governance"],
)
def exit_emergency_mode(request: EmergencyExitRequest) -> EmergencyStatusResponse:
    """Exit emergency mode when sufficient approvals are provided."""

    try:
        EMERGENCY_CONTROLLER.exit_emergency_mode(
            requested_by=request.requested_by,
            approvals=request.approvals,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return emergency_status()


@app.post(
    "/governance/emergency/action",
    tags=["Governance"],
)
def emergency_authorised_action(request: EmergencyActionRequest) -> Dict[str, str]:
    """Validate that an emergency action has dual authorisation."""

    try:
        EMERGENCY_CONTROLLER.request_authorised_action(
            actor=request.actor,
            approvals=request.approvals,
            action=request.action,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return {"status": "authorised", "action": request.action}


@app.get("/admin/services", response_model=ServicesOverviewResponse, tags=["Administration"])
def list_services() -> ServicesOverviewResponse:
    """Report the last known status of services managed by HueyOS."""

    return ServicesOverviewResponse(services=list(_SERVICE_STATES.values()))


@app.post(
    "/admin/services/{service_name}/start",
    response_model=ServiceStatus,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Administration"],
)
def start_service(service_name: str) -> ServiceStatus:
    """Mark a HueyOS service as running."""

    return _update_service_status(service_name, "running")


@app.post(
    "/admin/services/{service_name}/stop",
    response_model=ServiceStatus,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Administration"],
)
def stop_service(service_name: str) -> ServiceStatus:
    """Mark a HueyOS service as stopped."""

    return _update_service_status(service_name, "stopped")


@app.post("/admin/system-check", response_model=SystemCheckResponse, tags=["Administration"])
def admin_system_check() -> SystemCheckResponse:
    """Execute the full HueyOS system check suite and report individual results."""

    results = system_check()
    passed = all(results.values()) if results else True
    return SystemCheckResponse(results=results, passed=passed)


@app.post("/admin/health-check", tags=["Administration"])
def admin_health_check() -> Dict[str, str]:
    """Delegate to the primary health endpoint for administrative callers."""

    return healthz()
