# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Api module (src/huey)

"""FastAPI application exposing the HueyOS control surface."""

from __future__ import annotations

import asyncio
import datetime as dt
import hmac
import html
import os
import platform
import shutil
import socket
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence

try:  # pragma: no cover - psutil is an optional dependency at runtime
    import psutil  # type: ignore
except Exception:  # pragma: no cover - fall back to stdlib metrics
    psutil = None  # type: ignore[assignment]

from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse, StreamingResponse

from .env_validation import DEVELOPMENT_ENVS as _DEVELOPMENT_ENVS
from .env_validation import configured_environment as _configured_environment
from .env_validation import (
    validate_security_sensitive_environment,
)

# ``AIProcessor`` pulls in a large number of optional runtime dependencies from
# the legacy ``huey`` tree. When those modules are unavailable (for example in
# a trimmed CI environment) we fall back to a lightweight stub that mimics the
# subset of behaviour exercised by the API endpoints. The stub keeps the
# service operational for health checks and developer tooling while clearly
# signalling that the full ML stack is absent.
try:  # pragma: no cover - exercised indirectly during import
    from huey.memory.PY.ai_processor import AIProcessor  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - compatibility shim

    class AIProcessor:  # type: ignore[no-redef]
        """Minimal stand-in for the legacy :class:`AIProcessor`."""

        _DEFAULT_MODEL = "stub"

        def __init__(
            self,
            model: str | None = None,
            default_instruction: str | None = None,
            *,
            telemetry_store: "TelemetryStore" | None = None,
        ) -> None:
            self.model = model or self._DEFAULT_MODEL
            self.default_instruction = default_instruction or (
                "Rewrite the provided text to improve clarity while preserving meaning."
            )
            self.telemetry_store = telemetry_store

        # ------------------------------------------------------------------
        # Interface compatibility helpers
        # ------------------------------------------------------------------
        def get_model_catalog(self, refresh: bool = False) -> Dict[str, Any]:
            """Return static metadata describing the stub environment."""

            return {
                "backend": "stub",
                "active_model": self.model,
                "recommended_models": [self._DEFAULT_MODEL],
                "accelerators": [],
                "total_vram": 0,
            }

        def process_data(self, text: str) -> str:
            """Provide a deterministic echo transformation used by the API."""

            return f"Processed: {text.strip()}"

        def compute_mean(self, numbers: Sequence[float]) -> float:
            """Compute the arithmetic mean of ``numbers`` with basic validation."""

            values = list(numbers)
            if not values:
                raise ValueError("numbers must contain at least one value")
            return sum(values) / len(values)

        def analyze_data(self, text: str) -> Dict[str, Any]:
            """Return trivial metrics mirroring the real implementation signature."""

            length = len(text)
            return {
                "length": length,
                "words": len(text.split()),
                "unique_characters": len(set(text)),
            }


from huey.honeycomb.index import HoneycombIndex
from huey.honeycomb.monitor import HoneycombMonitor
from huey.honeycomb.storage import HoneycombStorage
from huey.os.core.resilience import (
    CrashRecoveryManager,
    EmergencyGovernanceController,
)
from huey.os.core.task_scheduler import (
    ResourceProfile,
    TaskPriority,
    TaskScheduler,
    TaskStatus,
)
from huey.os.hardware import create_default_sensor_manager
from huey.os.hardware.plugins import (
    SensorReading,
    list_sensor_plugin_metadata,
    list_sensor_plugins,
)
from huey.os.network import NetworkManager
from huey.os.pdf_utils import find_pdf, list_available_pdfs
from huey.os.power import BatteryMonitor
from huey.os.system_checks import system_check
from huey.os.utils.auto_sort import auto_sort_memory
from huey.os.utils.paths import get_memory_path
from huey.os.utils.persistence import AIInteraction, SensorTelemetry, TelemetryStore

__all__ = [
    "AI_PROCESSOR",
    "TELEMETRY_STORE",
    "AcceleratorInfoModel",
    "AnalyzeTextRequest",
    "AnalyzeTextResponse",
    "AutoSortRequest",
    "AutoSortResponse",
    "BATTERY_MONITOR",
    "BatteryStatusResponse",
    "CRASH_MANAGER",
    "ComputeMeanRequest",
    "ComputeMeanResponse",
    "AIModelAvailabilityResponse",
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
    "TelemetrySensorRecord",
    "SensorTelemetryResponse",
    "AIInteractionRecord",
    "AIInteractionResponse",
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
    "system_accelerators",
    "list_ai_models",
    "override_monitored_process",
    "poll_all_sensors",
    "poll_crash_manager",
    "poll_sensor",
    "power_should_shutdown",
    "list_recent_sensor_telemetry",
    "list_recent_ai_interactions",
    "dashboard",
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

HTTP_401_UNAUTHORIZED = getattr(status, "HTTP_401_UNAUTHORIZED", 401)


app = FastAPI(
    title="HueyOS API",
    version="0.2.0",
    description=(
        "HueyOS exposes robotic control, knowledge management, and automation "
        "capabilities through a unified API for integrations and operator tooling."
    ),
)

_PUBLIC_PATHS = {"/healthz"}
_TOKEN_MIDDLEWARE_PATHS = {"/dashboard"}

validate_security_sensitive_environment()


def _configured_api_token() -> str:
    """Return the optional bearer token required for API access."""

    return os.getenv("HUEY_API_TOKEN", "").strip()


def _unsafe_task_submission_enabled() -> bool:
    """Return whether unsafe/free-form task submission is explicitly enabled."""

    value = os.getenv("HUEY_ENABLE_UNSAFE_TASKS", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _is_local_request(request: Request) -> bool:
    """Return ``True`` when the caller appears to be local to this host."""

    client = getattr(request, "client", None)
    host = getattr(client, "host", "") if client is not None else ""
    return host in {"127.0.0.1", "::1", "localhost", "testclient", "testserver"}


def _require_privileged_surface_access(request: Request) -> None:
    """Protect command/task surfaces when global bearer auth is not configured.

    These endpoints accept free-form task instructions that can eventually map to
    agent command execution. When ``HUEY_API_TOKEN`` is unset we allow local-only
    access for developer workflows and block remote access by default.
    """

    if _configured_api_token():
        return
    if _is_local_request(request):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "This endpoint requires local access when HUEY_API_TOKEN is unset. "
            "Configure HUEY_API_TOKEN for remote access."
        ),
    )


def require_strong_api_auth(request: Request) -> None:
    """Require explicit bearer-token authentication for dangerous endpoints."""

    expected_token = _configured_api_token()
    if not expected_token:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API token authentication is required for this endpoint",
        )

    scheme, _, supplied_token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(
        supplied_token,
        expected_token,
    ):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API token",
        )


def _require_unsafe_task_submission_access(request: Request) -> None:
    """Enforce defensive gating for free-form task submission surfaces.

    Policy:
    - Local developer workflows remain available when the API token is unset.
    - Remote/production usage requires authenticated API access plus explicit
      enablement through ``HUEY_ENABLE_UNSAFE_TASKS=true``.
    """

    _require_privileged_surface_access(request)

    if _unsafe_task_submission_enabled():
        return

    if _configured_api_token() and _configured_environment() in _DEVELOPMENT_ENVS:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Unsafe free-form task submission is disabled. Set "
            "HUEY_ENABLE_UNSAFE_TASKS=true to allow authenticated submission."
        ),
    )


def _requires_scheduler_auth() -> bool:
    """Return whether task surfaces should require explicit bearer auth."""

    return bool(_configured_api_token()) or SCHEDULER is DEFAULT_SCHEDULER


def _requires_emergency_auth() -> bool:
    """Return whether emergency-control surfaces should require explicit auth."""

    return bool(_configured_api_token()) or (
        EMERGENCY_CONTROLLER is DEFAULT_EMERGENCY_CONTROLLER
    )


@app.middleware("http")
async def require_api_token(request: Request, call_next):
    """Require a bearer token when HUEY_API_TOKEN is configured."""

    if request.url.path not in _TOKEN_MIDDLEWARE_PATHS:
        return await call_next(request)

    expected_token = _configured_api_token()
    if not expected_token or request.url.path in _PUBLIC_PATHS:
        return await call_next(request)

    scheme, _, supplied_token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(
        supplied_token,
        expected_token,
    ):
        return Response(
            status_code=HTTP_401_UNAUTHORIZED,
            data={"detail": "Missing or invalid API token"},
        )

    return await call_next(request)


class AcceleratorInfoModel(BaseModel):
    """Hardware accelerator metadata exposed via the API."""

    name: str = Field(..., description="Friendly accelerator name")
    vendor: str = Field(..., description="Reported vendor for the device")
    driver: str = Field(..., description="Kernel driver handling the device")
    backend: str = Field(..., description="Acceleration backend (e.g. rocm)")
    vram_total: Optional[int] = Field(
        None, description="Total VRAM in bytes when known"
    )
    vram_free: Optional[int] = Field(None, description="Estimated free VRAM in bytes")
    bus_id: Optional[str] = Field(None, description="Bus address for the accelerator")
    node: Optional[str] = Field(None, description="Kernel device node identifier")


class AIModelAvailabilityResponse(BaseModel):
    """Recommended AI model summary based on detected accelerators."""

    backend: Optional[str]
    active_model: Optional[str]
    recommended_models: List[str]
    accelerators: List[AcceleratorInfoModel]
    total_vram: int


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
    accelerators: List[AcceleratorInfoModel] = Field(
        default_factory=list,
        description="Detected hardware accelerators available to the system",
    )


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

    processed_text: str = Field(
        ..., description="Text after AIProcessor transformation"
    )


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


class TelemetrySensorRecord(BaseModel):
    """Persisted sensor reading stored in the telemetry database."""

    name: str
    timestamp: float
    value: Any
    provenance: Dict[str, Any]


class SensorTelemetryResponse(BaseModel):
    """Recent telemetry records for sensors."""

    records: List[TelemetrySensorRecord]


class AIInteractionRecord(BaseModel):
    """Historical AI interaction stored for auditing."""

    timestamp: float
    prompt: str
    response: str
    model: Optional[str]
    backend: Optional[str]
    instruction: Optional[str]
    metadata: Dict[str, Any]
    status: str


class AIInteractionResponse(BaseModel):
    """Collection of AI interactions returned to clients."""

    records: List[AIInteractionRecord]


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
        default_factory=time.time,
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


TELEMETRY_STORE = TelemetryStore()

_REDACTED_TELEMETRY_TEXT = "[redacted]"
try:
    AI_PROCESSOR = AIProcessor(telemetry_store=TELEMETRY_STORE)
except TypeError:  # Backwards compatibility for stub AIProcessor in tests
    AI_PROCESSOR = AIProcessor()
SCHEDULER = TaskScheduler()
DEFAULT_SCHEDULER = SCHEDULER
CRASH_MANAGER = CrashRecoveryManager()
EMERGENCY_CONTROLLER = EmergencyGovernanceController()
DEFAULT_EMERGENCY_CONTROLLER = EMERGENCY_CONTROLLER
_SERVICE_STATES: Dict[str, ServiceStatus] = {}
SENSOR_MANAGER = create_default_sensor_manager(telemetry_store=TELEMETRY_STORE)
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

    catalog: Dict[str, Any] = {}
    if hasattr(AI_PROCESSOR, "get_model_catalog"):
        try:
            catalog = AI_PROCESSOR.get_model_catalog()
        except Exception:  # pragma: no cover - optional dependency failure
            catalog = {}
    accelerators = [
        AcceleratorInfoModel(**info) for info in catalog.get("accelerators", [])
    ]

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
        accelerators=accelerators,
    )


def _collect_accelerator_models(refresh: bool = False) -> List[AcceleratorInfoModel]:
    catalog = AI_PROCESSOR.get_model_catalog(refresh=refresh)
    return [AcceleratorInfoModel(**info) for info in catalog.get("accelerators", [])]


def _redact_ai_interaction(record: AIInteraction) -> AIInteraction:
    """Return a copy of ``record`` with sensitive textual fields redacted."""

    return AIInteraction(
        timestamp=record.timestamp,
        prompt=_REDACTED_TELEMETRY_TEXT,
        response=_REDACTED_TELEMETRY_TEXT,
        model=record.model,
        backend=record.backend,
        instruction=None,
        metadata={},
        status=record.status,
    )


def _render_dashboard(
    system: SystemStatusResponse,
    battery: Dict[str, Any],
    sensor_records: Sequence[SensorTelemetry],
    ai_records: Sequence[AIInteraction],
    catalog: Dict[str, Any],
) -> str:
    def _fmt(value: Any) -> str:
        if value is None:
            return "&mdash;"
        return html.escape(str(value))

    def _format_bytes(value: Optional[int]) -> str:
        if value is None:
            return "&mdash;"
        units = ["B", "KiB", "MiB", "GiB", "TiB"]
        amount = float(value)
        for unit in units:
            if amount < 1024.0 or unit == units[-1]:
                return f"{amount:.1f} {unit}"
            amount /= 1024.0
        return f"{amount:.1f} {units[-1]}"

    def _format_ts(value: Optional[float]) -> str:
        if value is None:
            return "&mdash;"
        try:
            return html.escape(
                dt.datetime.fromtimestamp(value).isoformat(sep=" ", timespec="seconds")
            )
        except Exception:
            return _fmt(value)

    accelerators = system.accelerators or []
    accelerator_rows = (
        "".join(
            f"<tr><td>{_fmt(acc.name)}</td><td>{_fmt(acc.vendor)}</td><td>{_fmt(acc.backend)}</td>"
            f"<td>{_format_bytes(acc.vram_total)}</td><td>{_format_bytes(acc.vram_free)}</td></tr>"
            for acc in accelerators
        )
        or "<tr><td colspan='5'>No accelerators detected</td></tr>"
    )

    recommended = catalog.get("recommended_models", [])
    recommended_models = (
        ", ".join(html.escape(str(model)) for model in recommended) or "None"
    )

    sensor_rows = (
        "".join(
            f"<tr><td>{_fmt(record.name)}</td><td>{_format_ts(record.timestamp)}</td>"
            f"<td>{_fmt(record.value)}</td></tr>"
            for record in sensor_records[:10]
        )
        or "<tr><td colspan='3'>No sensor telemetry recorded yet.</td></tr>"
    )

    ai_rows = (
        "".join(
            f"<tr><td>{_format_ts(record.timestamp)}</td>"
            f"<td>{_fmt(record.model)}</td><td>{_fmt(record.backend)}</td>"
            f"<td>{_fmt(record.status)}</td>"
            f"<td class='prompt'>{_fmt(record.prompt)[:160]}</td>"
            f"<td class='response'>{_fmt(record.response)[:160]}</td></tr>"
            for record in ai_records[:10]
        )
        or "<tr><td colspan='6'>No AI interactions logged.</td></tr>"
    )

    battery_percent = _fmt(battery.get("percent"))
    battery_secs = _fmt(battery.get("secs_left"))
    battery_plugged = _fmt(battery.get("power_plugged"))
    battery_runtime = _fmt(battery.get("estimated_runtime_minutes"))

    now = html.escape(dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8" />
        <meta http-equiv="refresh" content="30" />
        <title>HueyOS Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 1.5rem; background: #0f111a; color: #f0f3ff; }}
            h1 {{ margin-bottom: 0.2rem; }}
            h2 {{ margin-top: 1.5rem; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; }}
            th, td {{ border: 1px solid #23263b; padding: 0.5rem; text-align: left; }}
            th {{ background-color: #1d2030; }}
            tr:nth-child(even) {{ background-color: #131522; }}
            .prompt, .response {{ max-width: 24rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .meta {{ display: flex; gap: 2rem; flex-wrap: wrap; }}
            .meta section {{ background: #16192a; padding: 1rem; border-radius: 0.5rem; min-width: 18rem; box-shadow: 0 0 12px rgba(0,0,0,0.4); }}
            a {{ color: #8ab4ff; }}
        </style>
    </head>
    <body>
        <h1>HueyOS Operations Dashboard</h1>
        <p>Last updated {now}</p>
        <div class="meta">
            <section>
                <h2>System</h2>
                <p><strong>Host:</strong> {html.escape(system.hostname)}</p>
                <p><strong>OS:</strong> {html.escape(system.system)} {html.escape(system.release)}</p>
                <p><strong>Python:</strong> {html.escape(system.python_version)}</p>
                <p><strong>Memory Path:</strong> {html.escape(system.memory_path)}</p>
            </section>
            <section>
                <h2>Battery</h2>
                <p><strong>Charge:</strong> {battery_percent}%</p>
                <p><strong>Plugged:</strong> {battery_plugged}</p>
                <p><strong>Seconds Remaining:</strong> {battery_secs}</p>
                <p><strong>Estimated Runtime (minutes):</strong> {battery_runtime}</p>
            </section>
            <section>
                <h2>AI Models</h2>
                <p><strong>Backend:</strong> {_fmt(catalog.get('backend'))}</p>
                <p><strong>Active Model:</strong> {_fmt(catalog.get('active_model'))}</p>
                <p><strong>Recommended:</strong> {recommended_models}</p>
            </section>
        </div>

        <h2>Accelerators</h2>
        <table>
            <thead>
                <tr><th>Name</th><th>Vendor</th><th>Backend</th><th>Total VRAM</th><th>Free VRAM</th></tr>
            </thead>
            <tbody>{accelerator_rows}</tbody>
        </table>

        <h2>Recent Sensor Telemetry</h2>
        <table>
            <thead>
                <tr><th>Sensor</th><th>Timestamp</th><th>Value</th></tr>
            </thead>
            <tbody>{sensor_rows}</tbody>
        </table>

        <h2>Recent AI Interactions</h2>
        <table>
            <thead>
                <tr><th>Timestamp</th><th>Model</th><th>Backend</th><th>Status</th><th>Prompt</th><th>Response</th></tr>
            </thead>
            <tbody>{ai_rows}</tbody>
        </table>
    </body>
    </html>
    """


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

    for status_entry in CRASH_MANAGER.statuses():
        if status_entry["name"] == name:
            return MonitoredProcessStatusModel(**status_entry)
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


def _register_battery_hooks() -> None:
    """Attach event-driven hooks to the battery monitor."""

    def _schedule_power_saving(status: Dict[str, Any]) -> None:
        TELEMETRY_STORE.log_event("battery_low", status)
        active = [
            record
            for record in SCHEDULER.list_tasks([TaskStatus.PENDING, TaskStatus.RUNNING])
            if record.metadata.get("power_event") == "battery_low"
        ]
        if active:
            return
        SCHEDULER.schedule_task(
            command="activate_power_saving",
            priority=TaskPriority.CRITICAL,
            metadata={
                "power_event": "battery_low",
                "battery_percent": status.get("percent"),
                "source": status.get("source"),
            },
            resource_profile=ResourceProfile(
                cpu=0.05, memory=0.05, battery=1.0, gpu=0.0
            ),
        )

    def _log_recovery(status: Dict[str, Any]) -> None:
        TELEMETRY_STORE.log_event("battery_recovered", status)

    def _log_power_connected(status: Dict[str, Any]) -> None:
        TELEMETRY_STORE.log_event("power_connected", status)

    def _log_power_disconnected(status: Dict[str, Any]) -> None:
        TELEMETRY_STORE.log_event("power_disconnected", status)

    BATTERY_MONITOR.register_hook("battery_low", _schedule_power_saving)
    BATTERY_MONITOR.register_hook("battery_recovered", _log_recovery)
    BATTERY_MONITOR.register_hook("power_connected", _log_power_connected)
    BATTERY_MONITOR.register_hook("power_disconnected", _log_power_disconnected)


_register_battery_hooks()


from huey.os.api.routers.network import router as network_router
from huey.os.api.routers.power import router as power_router
from huey.os.api.routers.sensors import router as sensors_router
from huey.os.api.routers.system import healthz
from huey.os.api.routers.system import router as system_router
from huey.os.api.routers.system import system_status
from huey.os.api.routers.tasks import (
    cancel_task,
    get_task,
    list_tasks_endpoint,
)
from huey.os.api.routers.tasks import router as tasks_router
from huey.os.api.routers.tasks import (
    submit_task,
)
from huey.os.services.tasks import (
    ResourceProfileModel,
    ResourceSnapshotModel,
    TaskHistoryEntry,
    TaskListResponse,
    TaskResponse,
    TaskSubmissionRequest,
)

app.include_router(system_router)
app.include_router(tasks_router)
app.include_router(sensors_router)
app.include_router(network_router)
app.include_router(power_router)


@app.get(
    "/system/accelerators",
    response_model=List[AcceleratorInfoModel],
    tags=["System"],
)
def system_accelerators() -> List[AcceleratorInfoModel]:
    """Return detected hardware accelerators and VRAM metrics."""

    return _collect_accelerator_models(refresh=True)


def sensor_plugins() -> SensorPluginsResponse:
    """List available sensor plugin identifiers."""

    registry = SENSOR_MANAGER.registry
    plugins = list_sensor_plugins(registry)
    metadata = list_sensor_plugin_metadata(registry)
    return SensorPluginsResponse(plugins=plugins, metadata=metadata)


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return SensorRegistrationResponse(
        name=request.name,
        plugin=request.plugin,
        config=dict(request.config),
    )


def remove_sensor(sensor_name: str) -> Dict[str, str]:
    """Remove a configured sensor instance."""

    if SENSOR_MANAGER.get_sensor(sensor_name) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found"
        )
    SENSOR_MANAGER.remove_sensor(sensor_name)
    return {"status": "removed", "sensor": sensor_name}


def poll_sensor(sensor_name: str) -> SensorReadingResponse:
    """Poll a single sensor and store the reading in honeycomb storage."""

    try:
        reading = SENSOR_MANAGER.poll_sensor(sensor_name)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found"
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    return _reading_to_response(reading)


def poll_all_sensors() -> SensorPollAllResponse:
    """Poll every configured sensor."""

    readings = [_reading_to_response(reading) for reading in SENSOR_MANAGER.poll_all()]
    return SensorPollAllResponse(readings=readings)


def sensor_history(
    sensor_name: str,
    limit: int = Query(
        50, ge=1, le=500, description="Maximum number of readings to return"
    ),
) -> SensorHistoryResponse:
    """Return historical sensor readings from honeycomb storage."""

    if SENSOR_MANAGER.get_sensor(sensor_name) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found"
        )
    history = SENSOR_MANAGER.load_history(sensor_name, limit=limit)
    readings = [SensorReadingResponse(**record) for record in history]
    return SensorHistoryResponse(sensor=sensor_name, readings=readings)


async def stream_sensor(sensor_name: str) -> StreamingResponse:
    """Stream real-time readings for ``sensor_name`` using server-sent events."""

    if SENSOR_MANAGER.get_sensor(sensor_name) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sensor not found"
        )
    return StreamingResponse(
        _sensor_stream(sensor_name), media_type="text/event-stream"
    )


async def stream_all_sensors() -> StreamingResponse:
    """Stream readings for all sensors using server-sent events."""

    return StreamingResponse(_sensor_stream(None), media_type="text/event-stream")


@app.get(
    "/telemetry/sensors/recent",
    response_model=SensorTelemetryResponse,
    tags=["Telemetry"],
)
def list_recent_sensor_telemetry(
    limit: int = Query(
        25, ge=1, le=500, description="Maximum number of records to return"
    ),
    name: Optional[str] = Query(
        None, description="Filter telemetry to a specific sensor"
    ),
) -> SensorTelemetryResponse:
    """Return recent sensor telemetry captured in the persistent store."""

    records = TELEMETRY_STORE.fetch_recent_sensor_readings(name=name, limit=limit)
    payload = [
        TelemetrySensorRecord(
            name=record.name,
            timestamp=record.timestamp,
            value=record.value,
            provenance=record.provenance,
        )
        for record in records
    ]
    return SensorTelemetryResponse(records=payload)


@app.get(
    "/telemetry/ai/recent",
    response_model=AIInteractionResponse,
    tags=["Telemetry"],
)
def list_recent_ai_interactions(
    limit: int = Query(
        25, ge=1, le=500, description="Maximum number of AI interactions to return"
    ),
) -> AIInteractionResponse:
    """Return recent AI Processor interactions from the telemetry store."""

    records = TELEMETRY_STORE.fetch_recent_ai_results(limit=limit)
    payload = [
        AIInteractionRecord(
            timestamp=redacted.timestamp,
            prompt=redacted.prompt,
            response=redacted.response,
            model=redacted.model,
            backend=redacted.backend,
            instruction=redacted.instruction,
            metadata=redacted.metadata,
            status=redacted.status,
        )
        for redacted in (_redact_ai_interaction(record) for record in records)
    ]
    return AIInteractionResponse(records=payload)


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def dashboard(request: Request) -> HTMLResponse:
    """Render a lightweight operational dashboard for HueyOS."""

    _require_privileged_surface_access(request)
    system = _build_system_status()
    battery = BATTERY_MONITOR.get_status()
    sensor_records = TELEMETRY_STORE.fetch_recent_sensor_readings(limit=10)
    ai_records = [
        _redact_ai_interaction(record)
        for record in TELEMETRY_STORE.fetch_recent_ai_results(limit=10)
    ]
    try:
        catalog = AI_PROCESSOR.get_model_catalog()
    except Exception:  # pragma: no cover - optional dependency failure
        catalog = {}
    content = _render_dashboard(system, battery, sensor_records, ai_records, catalog)
    return HTMLResponse(content=content)


def network_status() -> NetworkStatusResponse:
    """Return the most recent network connectivity snapshot."""

    status_snapshot = NETWORK_MANAGER.check_status()
    return NetworkStatusResponse(**status_snapshot.__dict__)


def ensure_network_connectivity() -> NetworkStatusResponse:
    """Ensure wired connectivity is preferred with Wi-Fi failover."""

    status_snapshot = NETWORK_MANAGER.ensure_connectivity()
    return NetworkStatusResponse(**status_snapshot.__dict__)


def battery_status() -> BatteryStatusResponse:
    """Expose the current battery status."""

    status = BATTERY_MONITOR.get_status()
    return BatteryStatusResponse(**status)


def power_should_shutdown() -> Dict[str, Any]:
    """Return whether the system recommends a safe shutdown."""

    return {
        "should_shutdown": BATTERY_MONITOR.should_shutdown(),
        "threshold": BATTERY_MONITOR.shutdown_threshold,
    }


def trigger_shutdown() -> PowerEventResponse:
    """Initiate a safe shutdown sequence."""

    event = BATTERY_MONITOR.initiate_shutdown()
    return PowerEventResponse(
        timestamp=event.timestamp, action=event.action, metadata=event.metadata
    )


@app.get(
    "/resilience/monitors",
    response_model=List[MonitoredProcessStatusModel],
    tags=["Resilience"],
)
def list_monitored_processes() -> List[MonitoredProcessStatusModel]:
    """Return the set of processes being watched by the crash manager."""

    return [
        MonitoredProcessStatusModel(**status) for status in CRASH_MANAGER.statuses()
    ]


@app.post(
    "/resilience/monitors/{name}/override",
    response_model=MonitoredProcessStatusModel,
    tags=["Resilience"],
)
def override_monitored_process(
    name: str, request: ManualOverrideRequest
) -> MonitoredProcessStatusModel:
    """Enable or disable automatic crash recovery for the given process."""

    try:
        process_status = CRASH_MANAGER.toggle_auto_restart(
            name, request.auto_restart, reason=request.reason
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return MonitoredProcessStatusModel(**process_status)


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
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
def list_pdfs(
    pdf_dir: Optional[str] = Query(None, description="Override PDF search root")
) -> PDFListResponse:
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
def locate_pdf(
    filename: str,
    pdf_dir: Optional[str] = Query(None, description="Optional PDF search root"),
) -> PDFDetailResponse:
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
def auto_sort(request: AutoSortRequest, http_request: Request) -> AutoSortResponse:
    """Trigger automated organisation of files in the HueyOS memory directory."""

    require_strong_api_auth(http_request)
    try:
        summary = auto_sort_memory(
            source_dir=request.source_dir,
            destination_root=request.destination_root,
            dry_run=request.dry_run,
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
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


@app.get("/ai/models", response_model=AIModelAvailabilityResponse, tags=["AI Tools"])
def list_ai_models() -> AIModelAvailabilityResponse:
    """Report active AI backend and recommended local models."""

    catalog = AI_PROCESSOR.get_model_catalog(refresh=True)
    return AIModelAvailabilityResponse(
        backend=catalog.get("backend"),
        active_model=catalog.get("active_model"),
        recommended_models=list(catalog.get("recommended_models", [])),
        accelerators=[
            AcceleratorInfoModel(**info) for info in catalog.get("accelerators", [])
        ],
        total_vram=int(catalog.get("total_vram", 0)),
    )


@app.post(
    "/ai/process-text",
    response_model=ProcessTextResponse,
    tags=["AI Tools"],
)
async def ai_process_text(
    request: ProcessTextRequest,
    stream: bool = Query(False, description="When true, stream the response body"),
):
    """Apply :class:`AIProcessor` transformations to the supplied text."""

    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty for processing.",
        )

    if stream:
        return StreamingResponse(_stream_text(request.text), media_type="text/plain")

    processed = await asyncio.to_thread(AI_PROCESSOR.process_data, request.text)
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

    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text must not be empty for analysis.",
        )

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
def enter_emergency_mode(
    request: EmergencyModeRequest, http_request: Request
) -> EmergencyStatusResponse:
    """Enter emergency mode after validating approvals."""

    if _requires_emergency_auth():
        require_strong_api_auth(http_request)
    try:
        EMERGENCY_CONTROLLER.enter_emergency_mode(
            triggered_by=request.triggered_by,
            reason=request.reason,
            approvals=request.approvals,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return emergency_status()


@app.post(
    "/governance/emergency/exit",
    response_model=EmergencyStatusResponse,
    tags=["Governance"],
)
def exit_emergency_mode(
    request: EmergencyExitRequest, http_request: Request
) -> EmergencyStatusResponse:
    """Exit emergency mode when sufficient approvals are provided."""

    if _requires_emergency_auth():
        require_strong_api_auth(http_request)
    try:
        EMERGENCY_CONTROLLER.exit_emergency_mode(
            requested_by=request.requested_by,
            approvals=request.approvals,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return emergency_status()


@app.post(
    "/governance/emergency/action",
    tags=["Governance"],
)
def emergency_authorised_action(
    request: EmergencyActionRequest, http_request: Request
) -> Dict[str, str]:
    """Validate that an emergency action has dual authorisation."""

    if _requires_emergency_auth():
        require_strong_api_auth(http_request)
    try:
        EMERGENCY_CONTROLLER.request_authorised_action(
            actor=request.actor,
            approvals=request.approvals,
            action=request.action,
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    return {"status": "authorised", "action": request.action}


@app.get(
    "/admin/services", response_model=ServicesOverviewResponse, tags=["Administration"]
)
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


@app.post(
    "/admin/system-check", response_model=SystemCheckResponse, tags=["Administration"]
)
def admin_system_check() -> SystemCheckResponse:
    """Execute the full HueyOS system check suite and report individual results."""

    results = system_check()
    passed = all(results.values()) if results else True
    return SystemCheckResponse(results=results, passed=passed)


@app.post("/admin/health-check", tags=["Administration"])
def admin_health_check() -> Dict[str, str]:
    """Delegate to the primary health endpoint for administrative callers."""

    return healthz()


def main(argv: Sequence[str] | None = None) -> None:
    """Run the HueyOS API server from the console entry point."""
    import argparse

    import uvicorn

    env_reload = os.getenv("HUEY_RELOAD", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    parser = argparse.ArgumentParser(description="Run the HueyOS API server.")
    parser.add_argument(
        "--host",
        default=os.getenv("HUEY_HOST", "127.0.0.1"),
        help="Host/interface to bind. Defaults to HUEY_HOST or 127.0.0.1.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("HUEY_PORT", "1995")),
        help="Port to bind. Defaults to HUEY_PORT or 1995.",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=env_reload,
        help="Enable uvicorn reload mode. Also enabled by HUEY_RELOAD=true.",
    )

    args = parser.parse_args(argv)

    uvicorn.run("huey.api:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
