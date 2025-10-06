from __future__ import annotations

import asyncio
import platform
import shutil
import socket
import time
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional

try:  # pragma: no cover - psutil is an optional dependency at runtime
    import psutil  # type: ignore
except Exception:  # pragma: no cover - fall back to stdlib metrics
    psutil = None  # type: ignore[assignment]

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from huey.memory.PY.ai_processor import AIProcessor
from monkey_head.pdf_utils import find_pdf, list_available_pdfs
from monkey_head.system_checks import system_check
from monkey_head.utils.auto_sort import auto_sort_memory
from monkey_head.utils.paths import get_memory_path


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


AI_PROCESSOR = AIProcessor()
_SERVICE_STATES: Dict[str, ServiceStatus] = {}


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


@app.get("/healthz", tags=["System"])
def healthz() -> Dict[str, str]:
    """Lightweight probe used by orchestrators to ensure the API is responsive."""

    return {"status": "ok", "service": "hueyos"}


@app.get("/system/status", response_model=SystemStatusResponse, tags=["System"])
def system_status() -> SystemStatusResponse:
    """Return operating system, hardware, and configuration details for HueyOS."""

    return _build_system_status()


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
