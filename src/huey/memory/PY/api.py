Warning: truncated output (original token count: 15526)
Total output lines: 1930

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
import sys
import time
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Sequence

try:  # pragma: no cover - psutil is an optional dependency at runtime
    import psutil  # type: ignore
except Exception:  # pragma: no cover - fall back to stdlib metrics
    psutil = None  # type: ignore[assignment]

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .env_validation import DEVELOPMENT_ENVS as _DEVELOPMENT_ENVS
from .env_validation import configured_environment as _configured_environment
from .env_validation import validate_security_sensitive_environment

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
_LOOPBACK_HOSTS = {
    "127.0.0.1",
    "::1",
    "::ffff:127.0.0.1",
    "localhost",
    "testclient",
    "testserver",
}

validate_security_sensitive_environment()


def _configured_api_token() -> str:
    """Return the legacy general-purpose API bearer token."""

    return os.getenv("HUEY_API_TOKEN", "").strip()


def _configured_api_tokens() -> dict[str, list[str]]:
    """Return configured API credentials mapped to their least privilege role."""

    tokens: dict[str, list[str]] = {}
    for role, variable in (
        ("operator", "HUEY_API_OPERATOR_TOKEN"),
        ("admin", "HUEY_API_ADMIN_TOKEN"),
    ):
        token = os.getenv(variable, "").strip()
        if token:
            tokens.setdefault(role, []).append(token)
    legacy_token = _configured_api_token()
    if legacy_token:
        tokens.setdefault("operator", []).append(legacy_token)
    admin_tokens = tokens.get("admin", [])
    operator_tokens = tokens.get("operator", [])
    if any(
        hmac.compare_digest(admin, operator)
        for admin in admin_tokens
        for operator in operator_tokens
    ):
        raise RuntimeError(
            "HUEY_API_ADMIN_TOKEN must be distinct from operator-scoped tokens"
        )
    return tokens


def _unsafe_task_submission_enabled() -> bool:
    """Return whether unsafe/free-form task submission is explicitly enabled."""

    value = os.getenv("HUEY_ENABLE_UNSAFE_TASKS", "false").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _is_loopback_host(host: str) -> bool:
    """Return ``True`` when ``host`` resolves to an allowed loopback alias."""

    return host.strip().strip("[]").lower() in _LOOPBACK_HOSTS


def _is_local_request(request: Request) -> bool:
    """Return ``True`` when the caller appears to be local to this host."""

    # The URL hostname is derived from the request Host header and is not a
    # trustworthy indicator of the peer's network address.
    client = getattr(request, "client", None)
    client_host = getattr(client, "host", "") if client is not None else ""
    return _is_loopback_host(client_host)


def _require_privileged_surface_access(request: Request) -> None:
    """Protect command/task surfaces when global bearer auth is not configured.

    These endpoints accept free-form task instructions that can eventually map to
    agent command execution. When ``HUEY_API_TOKEN`` is unset we allow local-only
    access for developer workflows and block remote access by default.
    """

    if _configured_api_tokens():
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


def require_strong_api_auth(request: Request) -> str:
    """Authenticate a scoped bearer token and return its least-privilege role."""

    configured_tokens = _configured_api_tokens()
    if not configured_tokens:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="API token authentication is required for this endpoint",
        )

    scheme, _, supplied_token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() == "bearer":
        for role in ("admin", "operator"):
            for expected_token in configured_tokens.get(role, []):
                if hmac.compare_digest(supplied_token, expected_token):
                    return role

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

    if _configured_api_tokens() and _c…9526 tokens truncated…s regardless of overrides."""

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
    passed = all(value for value in results.values() if isinstance(value, bool))
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
