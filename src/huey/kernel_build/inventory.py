"""Read-only host inventory for the HueyOS kernel build framework.

The inventory is the framework's only source of truth about the **host**
before a build. It is strictly read-only: no command that mutates host state
is permitted, no file outside the workspace is written, and any failed probe
becomes a :class:`ValidationFinding` rather than an exception. This lets
``doctor`` explain what could not be inspected without blocking further
read-only steps.

Key design decisions
--------------------
* **V100 is identified by PCI BDF and UUID**, never by enumeration index.
  The index (``0``, ``1``, …) is unstable across reboots and driver
  reloads, so it is never used as an identifier.
* **`nvidia-smi`'s CUDA version is the driver-advertised API**, not proof
  that a matching toolkit is installed. The installed toolkit is parsed
  separately from ``nvcc --version`` and recorded as
  ``cuda_toolkit_version`` with ``verified_toolkit_via='nvcc --version'``.
* **Module flavor** is inferred from the DKMS status output. When the DKMS
  output does not clearly indicate an open-module package, the baseline
  defaults to ``proprietary`` (the R580 lineage is proprietary) and a
  WARNING finding records the inference so the operator can confirm.
* **Secure Boot state** is ``UNKNOWN`` when ``mokutil --sb-state`` is
  missing, fails, or reports that EFI variables are unavailable. It is
  never silently treated as ``DISABLED``.
* **Path independence.** Filesystem probes go through an injectable
  :class:`HostFs` so tests run against a temp tree, and production runs
  against the real ``/``.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence

from huey.kernel_build.models import (
    DriverBaseline,
    GPUIdentity,
    GPUVendor,
    ModuleFlavor,
    Severity,
    ValidationFinding,
)
from huey.kernel_build.policy import SecureBootState
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerProtocol,
    RunnerResult,
    RunnerTimeout,
)

logger = logging.getLogger(__name__)

__all__ = [
    "FakeHostFs",
    "HostFs",
    "HostInventory",
    "InventoryReport",
    "RealHostFs",
    "collect_inventory",
]


# ---------------------------------------------------------------------------
# HostFs protocol and implementations
# ---------------------------------------------------------------------------


class HostFs(Protocol):
    """Read-only filesystem interface used by :class:`HostInventory`."""

    def read_text(self, path: Path) -> str | None:
        """Return the text content of ``path`` or ``None`` if unreadable."""

    def list_dir(self, path: Path) -> tuple[Path, ...]:
        """Return direct children of ``path`` or ``()`` if unreadable."""

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` exists (file or directory)."""


class RealHostFs:
    """Production :class:`HostFs` reading directly from the real filesystem."""

    def read_text(self, path: Path) -> str | None:
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return None

    def list_dir(self, path: Path) -> tuple[Path, ...]:
        try:
            return tuple(sorted(path.iterdir()))
        except (OSError, PermissionError):
            return ()

    def exists(self, path: Path) -> bool:
        try:
            return path.exists()
        except OSError:
            return False


class FakeHostFs:
    """Test-oriented :class:`HostFs` that overlays a temp root.

    Paths are mapped as ``root / str(path).lstrip("/")``. This lets tests
    create ``fake_root / "boot" / "config-7.2.15-huey1"`` and have the
    inspector read ``/boot/config-7.2.15-huey1``.
    """

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    def _map(self, path: Path) -> Path:
        return self._root / str(path).lstrip("/")

    def read_text(self, path: Path) -> str | None:
        try:
            return self._map(path).read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            return None

    def list_dir(self, path: Path) -> tuple[Path, ...]:
        try:
            return tuple(
                sorted(
                    Path(str(child))
                    for child in self._map(path).iterdir()
                )
            )
        except (OSError, PermissionError):
            return ()

    def exists(self, path: Path) -> bool:
        try:
            return self._map(path).exists()
        except OSError:
            return False


# ---------------------------------------------------------------------------
# InventoryReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class InventoryReport:
    """Snapshot of the host as observed at :attr:`collected_at`."""

    running_kernel: str | None
    os_release: dict[str, str]
    secure_boot: SecureBootState
    gpus: tuple[GPUIdentity, ...]
    driver: DriverBaseline | None
    dkms_status_lines: tuple[str, ...]
    dkms_kernel_releases_for_driver: tuple[str, ...]
    nvcc_version: str | None
    kernel_configs_available: tuple[str, ...]
    kernel_headers_available: tuple[str, ...]
    findings: tuple[ValidationFinding, ...] = field(default_factory=tuple)
    collected_at: str = ""

    def __post_init__(self) -> None:
        for name in ("gpus", "dkms_status_lines", "dkms_kernel_releases_for_driver",
                     "kernel_configs_available", "kernel_headers_available", "findings"):
            value = getattr(self, name)
            if isinstance(value, list):
                object.__setattr__(self, name, tuple(value))
        if not isinstance(self.os_release, dict):
            raise TypeError("InventoryReport.os_release must be dict[str, str]")

    def has_blocking_findings(self) -> bool:
        return any(
            f.severity in (Severity.ERROR, Severity.CRITICAL) for f in self.findings
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "running_kernel": self.running_kernel,
            "os_release": dict(self.os_release),
            "secure_boot": self.secure_boot.value,
            "gpus": [g.to_dict() for g in self.gpus],
            "driver": self.driver.to_dict() if self.driver else None,
            "dkms_status_lines": list(self.dkms_status_lines),
            "dkms_kernel_releases_for_driver": list(
                self.dkms_kernel_releases_for_driver
            ),
            "nvcc_version": self.nvcc_version,
            "kernel_configs_available": list(self.kernel_configs_available),
            "kernel_headers_available": list(self.kernel_headers_available),
            "findings": [f.to_dict() for f in self.findings],
            "collected_at": self.collected_at,
        }


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_OS_RELEASE_LINE_RE = re.compile(r'^([A-Z0-9_]+)="?(.*?)"?\s*$')

_PCI_FULL_RE = re.compile(r"^([0-9a-f]{1,8}):([0-9a-f]{2}):([0-9a-f]{2})\.([0-7])$", re.IGNORECASE)
_PCI_LSPCI_FULL_RE = re.compile(r"^([0-9a-f]{4}):([0-9a-f]{2}):([0-9a-f]{2})\.([0-7])\s", re.IGNORECASE)
_PCI_LSPCI_SHORT_RE = re.compile(r"^([0-9a-f]{2}):([0-9a-f]{2})\.([0-7])\s", re.IGNORECASE)
_GPU_CONTROLLER_CLASSES = (
    "VGA compatible controller",
    "3D controller",
    "Display controller",
)
_CC_DOTTED_RE = re.compile(r"^([0-9]+)\.([0-9]+)$")
_CUDA_API_RE = re.compile(r"CUDA Version:\s*([0-9]+(?:\.[0-9]+)*)")
_NVCC_RELEASE_RE = re.compile(r"release\s+([0-9]+(?:\.[0-9]+)?)")
_DKMS_NVIDIA_RE = re.compile(r"^nvidia/([^,\s]+),\s*([^,\s]+),")


def _normalize_pci(domain: str, bus: str, slot: str, function: str) -> str:
    return (
        f"{int(domain, 16):08x}:"
        f"{int(bus, 16):02x}:"
        f"{int(slot, 16):02x}."
        f"{int(function, 16)}"
    )


def _clean_field(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    if not v or v == "[N/A]" or v == "N/A":
        return None
    return v


def _compute_cap_to_sm(value: str | None) -> str | None:
    v = _clean_field(value)
    if not v:
        return None
    if v.startswith("sm_"):
        return v if re.match(r"^sm_[0-9]+$", v) else None
    m = _CC_DOTTED_RE.match(v)
    if m:
        return f"sm_{m.group(1)}{m.group(2)}"
    return None


def _parse_nvidia_smi_gpu_line(line: str) -> tuple[str, str | None, str | None, str | None] | None:
    """Parse a ``--format=csv,noheader`` row of ``name,uuid,pci.bus_id,compute_cap``.

    Fields are split from the right so a name containing ``, `` cannot corrupt
    the structured fields. Returns ``(name, uuid, pci, sm)`` or ``None`` if the
    line cannot be parsed as a valid NVIDIA GPU record.
    """
    stripped = line.strip()
    if not stripped:
        return None
    parts = stripped.rsplit(", ", 3)
    if len(parts) != 4:
        return None
    name, uuid, pci, cc = parts
    name = name.strip()
    if not name:
        return None
    pci_match = _PCI_FULL_RE.match(pci.strip())
    if not pci_match:
        return None
    domain, bus, slot, fn = pci_match.groups()
    pci_norm = _normalize_pci(domain, bus, slot, fn)
    uuid_clean = _clean_field(uuid)
    sm = _compute_cap_to_sm(cc)
    return name, uuid_clean, pci_norm, sm


def _parse_lspci_line(line: str) -> GPUIdentity | None:
    """Parse a single ``lspci -nnk`` line into a GPUIdentity (NVIDIA or AMD)."""
    full = _PCI_LSPCI_FULL_RE.match(line)
    short = _PCI_LSPCI_SHORT_RE.match(line)
    if full:
        domain, bus, slot, fn = full.groups()
        pci = _normalize_pci(domain, bus, slot, fn)
        rest = line[full.end():]
    elif short:
        bus, slot, fn = short.groups()
        pci = _normalize_pci("0000", bus, slot, fn)
        rest = line[short.end():]
    else:
        return None

    if not any(cls in line for cls in _GPU_CONTROLLER_CLASSES):
        return None

    if "NVIDIA" in rest:
        vendor = GPUVendor.NVIDIA
    elif "Advanced Micro Devices" in rest or "AMD/ATI" in rest or " AMD " in rest:
        vendor = GPUVendor.AMD
    else:
        return None

    model = rest
    if ":" in model:
        model = model.split(":", 1)[1]
    model = model.strip()
    model = re.sub(r"\s*\(rev [0-9a-fA-F]+\)\s*$", "", model)
    model = re.sub(r"\s*\[[0-9a-fA-F]{4}\]\s*", " ", model).strip()
    if not model:
        model = "unknown GPU"

    try:
        return GPUIdentity(vendor=vendor, model=model, pci_address=pci)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# HostInventory
# ---------------------------------------------------------------------------


class HostInventory:
    """Read-only host inventory collector.

    Parameters
    ----------
    runner:
        Any :class:`RunnerProtocol` implementation. Use :class:`Runner`
        in production and :class:`FakeRunner` (or a test-provided
        dispatcher) in tests.
    host_fs:
        Optional :class:`HostFs`. Defaults to :class:`RealHostFs`.
    modinfo_fallback_paths:
        Candidate absolute paths to try when ``modinfo`` is not on ``PATH``.
    nvcc_fallback_paths:
        Candidate absolute paths to try when ``nvcc`` is not on ``PATH``.
    clock:
        Optional clock returning a UTC-aware ``datetime``; used only for
        ``collected_at``. Injecting it makes reports deterministic in tests.
    """

    def __init__(
        self,
        runner: RunnerProtocol,
        *,
        host_fs: HostFs | None = None,
        modinfo_fallback_paths: Sequence[str] = (
            "/usr/sbin/modinfo",
            "/sbin/modinfo",
        ),
        nvcc_fallback_paths: Sequence[str] = (
            "/usr/local/cuda/bin/nvcc",
            "/usr/bin/nvcc",
        ),
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._runner = runner
        self._fs = host_fs if host_fs is not None else RealHostFs()
        self._modinfo_paths = tuple(modinfo_fallback_paths)
        self._nvcc_paths = tuple(nvcc_fallback_paths)
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # ---- public API ------------------------------------------------------

    def collect(self) -> InventoryReport:
        """Run all probes and return a consolidated report."""
        findings: list[ValidationFinding] = []

        os_release = self._read_os_release(findings)
        running_kernel = self._read_running_kernel(findings)
        secure_boot = self._read_secure_boot(findings)

        nvidia_gpus, nvidia_driver_version, nvidia_cuda_api = (
            self._read_nvidia_smi(findings)
        )
        lspci_gpus = self._read_lspci_gpus(findings)
        gpus = self._merge_gpus(nvidia_gpus, lspci_gpus)

        modinfo_version = self._read_modinfo_version(findings)
        dkms_lines, dkms_releases = self._read_dkms(findings)
        driver_version = nvidia_driver_version or modinfo_version
        if nvidia_driver_version and modinfo_version and nvidia_driver_version != modinfo_version:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="DRIVER_VERSION_MISMATCH",
                    message=(
                        f"nvidia-smi reports driver {nvidia_driver_version!r} "
                        f"but modinfo reports {modinfo_version!r}."
                    ),
                    context={
                        "nvidia_smi": nvidia_driver_version,
                        "modinfo": modinfo_version,
                    },
                )
            )
        dkms_releases_for_driver = self._filter_dkms_releases(
            dkms_lines, driver_version, findings
        )

        nvcc_version = self._read_nvcc_version(findings)

        kernel_configs = self._list_boot_configs()
        kernel_headers = self._list_kernel_headers()

        driver = self._build_driver_baseline(
            driver_version=driver_version,
            cuda_api_version=nvidia_cuda_api,
            cuda_toolkit_version=nvcc_version,
            dkms_builds=dkms_releases_for_driver,
            dkms_lines=dkms_lines,
            findings=findings,
        )

        if (
            running_kernel
            and kernel_headers
            and running_kernel not in kernel_headers
        ):
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="RUNNING_KERNEL_NO_HEADERS",
                    message=(
                        f"Running kernel {running_kernel!r} has no matching "
                        f"/lib/modules/{running_kernel}/build. Available: "
                        f"{list(kernel_headers)!r}"
                    ),
                    context={
                        "running_kernel": running_kernel,
                        "available_headers": list(kernel_headers),
                    },
                )
            )

        if any(
            g.vendor == GPUVendor.NVIDIA and g.compute_capability == "sm_70"
            for g in gpus
        ) and secure_boot == SecureBootState.UNKNOWN:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="SECUREBOOT_UNKNOWN_WITH_VOLTA",
                    message=(
                        "V100 (sm_70) present and Secure Boot state is "
                        "unknown. Install 'mokutil' or run "
                        "'mokutil --sb-state' before promotion."
                    ),
                )
            )

        collected_at = self._clock().astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        return InventoryReport(
            running_kernel=running_kernel,
            os_release=os_release,
            secure_boot=secure_boot,
            gpus=gpus,
            driver=driver,
            dkms_status_lines=dkms_lines,
            dkms_kernel_releases_for_driver=dkms_releases_for_driver,
            nvcc_version=nvcc_version,
            kernel_configs_available=kernel_configs,
            kernel_headers_available=kernel_headers,
            findings=tuple(findings),
            collected_at=collected_at,
        )

    # ---- exec helper -----------------------------------------------------

    def _exec(
        self, argv: tuple[str, ...], *, timeout: float = 30.0
    ) -> tuple[str | None, ValidationFinding | None]:
        """Execute ``argv`` and return ``(stdout, error_finding)``.

        Never raises for expected failures. Any of:
        * executable not found,
        * timeout,
        * nonzero returncode,
        * decoding failure,
        results in ``stdout=None`` and a finding describing what happened.
        """
        try:
            spec = CommandSpec(argv=argv, cwd=Path("/"), timeout_seconds=timeout)
            result: RunnerResult = self._runner.run(spec)
        except RunnerTimeout:
            return None, ValidationFinding(
                severity=Severity.WARNING,
                code="COMMAND_TIMEOUT",
                message=f"{argv[0]} timed out after {timeout}s",
                context={"argv": list(argv)},
            )
        except RunnerError as exc:
            return None, ValidationFinding(
                severity=Severity.INFO,
                code="COMMAND_UNAVAILABLE",
                message=f"{argv[0]}: {exc}",
                context={"argv": list(argv)},
            )
        if result.command.returncode != 0:
            return None, ValidationFinding(
                severity=Severity.INFO,
                code="COMMAND_FAILED",
                message=(
                    f"{argv[0]} exited with {result.command.returncode}"
                ),
                context={
                    "argv": list(argv),
                    "returncode": result.command.returncode,
                },
            )
        return (result.stdout or b"").decode("utf-8", errors="replace"), None

    def _try_candidates(
        self,
        candidates: Sequence[tuple[str, ...]],
        findings: list[ValidationFinding],
        *,
        absent_code: str,
        timeout: float = 15.0,
    ) -> str | None:
        last: ValidationFinding | None = None
        for argv in candidates:
            text, finding = self._exec(argv, timeout=timeout)
            if text is not None and text.strip():
                return text
            if finding is not None:
                last = finding
        findings.append(
            ValidationFinding(
                severity=Severity.INFO if last is None or last.severity == Severity.INFO else last.severity,
                code=absent_code,
                message=(
                    f"Could not obtain output from any of: "
                    f"{[c[0] for c in candidates]!r}"
                ),
                context={"candidates": [list(c) for c in candidates]},
            )
        )
        return None

    # ---- individual probes ----------------------------------------------

    def _read_os_release(self, findings: list[ValidationFinding]) -> dict[str, str]:
        text = self._fs.read_text(Path("/etc/os-release"))
        if text is None:
            findings.append(
                ValidationFinding(
                    severity=Severity.INFO,
                    code="OS_RELEASE_UNAVAILABLE",
                    message="/etc/os-release not readable.",
                )
            )
            return {}
        parsed: dict[str, str] = {}
        for raw in text.splitlines():
            m = _OS_RELEASE_LINE_RE.match(raw.strip())
            if m:
                parsed[m.group(1)] = m.group(2)
        return parsed

    def _read_running_kernel(self, findings: list[ValidationFinding]) -> str | None:
        text, finding = self._exec(("uname", "-r"), timeout=5.0)
        if text is None:
            if finding is not None:
                findings.append(
                    ValidationFinding(
                        severity=finding.severity,
                        code="UNAME_UNAVAILABLE",
                        message=finding.message,
                        context=finding.context,
                    )
                )
            return None
        return text.strip() or None

    def _read_secure_boot(self, findings: list[ValidationFinding]) -> SecureBootState:
        text, finding = self._exec(("mokutil", "--sb-state"), timeout=10.0)
        if text is None:
            if finding is not None:
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="SECUREBOOT_STATE_UNKNOWN",
                        message=(
                            "mokutil --sb-state unavailable; Secure Boot "
                            f"state treated as unknown ({finding.message})."
                        ),
                    )
                )
            return SecureBootState.UNKNOWN
        normalized = text.strip().lower()
        if "secureboot enabled" in normalized:
            return SecureBootState.ENABLED
        if "secureboot disabled" in normalized:
            return SecureBootState.DISABLED
        if "efi variables are not supported" in normalized:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="SECUREBOOT_EFIVARS_UNAVAILABLE",
                    message="EFI variables not mounted; Secure Boot state unknown.",
                )
            )
            return SecureBootState.UNKNOWN
        findings.append(
            ValidationFinding(
                severity=Severity.WARNING,
                code="SECUREBOOT_STATE_UNRECOGNIZED",
                message=f"Unrecognized mokutil output: {text.strip()!r}",
            )
        )
        return SecureBootState.UNKNOWN

    def _read_nvidia_smi(
        self, findings: list[ValidationFinding]
    ) -> tuple[tuple[GPUIdentity, ...], str | None, str | None]:
        """Return (gpus, driver_version, cuda_api_version_from_banner)."""
        query_stdout, query_finding = self._exec(
            (
                "nvidia-smi",
                "--query-gpu=name,uuid,pci.bus_id,compute_cap",
                "--format=csv,noheader",
            ),
            timeout=20.0,
        )
        if query_stdout is None:
            if query_finding is not None:
                findings.append(
                    ValidationFinding(
                        severity=query_finding.severity,
                        code="NVIDIA_SMI_UNAVAILABLE",
                        message=query_finding.message,
                        context=query_finding.context,
                    )
                )
            return (), None, None

        gpus: list[GPUIdentity] = []
        for line in query_stdout.splitlines():
            parsed = _parse_nvidia_smi_gpu_line(line)
            if parsed is None:
                continue
            name, uuid, pci, sm = parsed
            try:
                gpus.append(
                    GPUIdentity(
                        vendor=GPUVendor.NVIDIA,
                        model=name,
                        pci_address=pci,
                        uuid=uuid,
                        compute_capability=sm,
                    )
                )
            except ValueError as exc:
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="NVIDIA_GPU_ENTRY_INVALID",
                        message=f"Skipping invalid GPU entry {name!r}: {exc}",
                        context={"pci": pci, "uuid": uuid},
                    )
                )

        driver_stdout, driver_finding = self._exec(
            ("nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"),
            timeout=15.0,
        )
        driver_version: str | None = None
        if driver_stdout is not None:
            for line in driver_stdout.splitlines():
                candidate = _clean_field(line)
                if candidate:
                    driver_version = candidate
                    break
        elif driver_finding is not None:
            findings.append(
                ValidationFinding(
                    severity=driver_finding.severity,
                    code="NVIDIA_DRIVER_VERSION_UNAVAILABLE",
                    message=driver_finding.message,
                )
            )

        banner_stdout, banner_finding = self._exec(("nvidia-smi",), timeout=20.0)
        cuda_api: str | None = None
        if banner_stdout is not None:
            match = _CUDA_API_RE.search(banner_stdout)
            if match:
                cuda_api = match.group(1)
        elif banner_finding is not None:
            findings.append(
                ValidationFinding(
                    severity=banner_finding.severity,
                    code="NVIDIA_SMI_BANNER_UNAVAILABLE",
                    message=banner_finding.message,
                )
            )

        return tuple(gpus), driver_version, cuda_api

    def _read_lspci_gpus(
        self, findings: list[ValidationFinding]
    ) -> tuple[GPUIdentity, ...]:
        text, finding = self._exec(("lspci", "-nnk"), timeout=15.0)
        if text is None:
            if finding is not None:
                findings.append(
                    ValidationFinding(
                        severity=finding.severity,
                        code="LSPCI_UNAVAILABLE",
                        message=finding.message,
                    )
                )
            return ()
        gpus: list[GPUIdentity] = []
        for line in text.splitlines():
            gpu = _parse_lspci_line(line)
            if gpu is not None:
                gpus.append(gpu)
        return tuple(gpus)

    def _read_modinfo_version(
        self, findings: list[ValidationFinding]
    ) -> str | None:
        candidates: list[tuple[str, ...]] = [("modinfo", "-F", "version", "nvidia")]
        for path in self._modinfo_paths:
            candidates.append((path, "-F", "version", "nvidia"))
        for argv in candidates:
            text, _finding = self._exec(argv, timeout=5.0)
            if text is not None and text.strip():
                return text.strip()
        findings.append(
            ValidationFinding(
                severity=Severity.INFO,
                code="MODINFO_NVIDIA_UNAVAILABLE",
                message="Could not determine NVIDIA module version via modinfo.",
            )
        )
        return None

    def _read_dkms(
        self, findings: list[ValidationFinding]
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        text, finding = self._exec(("dkms", "status"), timeout=20.0)
        if text is None:
            if finding is not None:
                findings.append(
                    ValidationFinding(
                        severity=finding.severity,
                        code="DKMS_STATUS_UNAVAILABLE",
                        message=finding.message,
                    )
                )
            return (), ()
        lines = tuple(line for line in text.splitlines() if line.strip())
        releases: list[str] = []
        for line in lines:
            m = _DKMS_NVIDIA_RE.match(line)
            if m:
                kernel = m.group(2)
                if kernel not in releases:
                    releases.append(kernel)
        return lines, tuple(releases)

    def _filter_dkms_releases(
        self,
        dkms_lines: tuple[str, ...],
        driver_version: str | None,
        findings: list[ValidationFinding],
    ) -> tuple[str, ...]:
        if not driver_version:
            return ()
        matching: list[str] = []
        for line in dkms_lines:
            m = _DKMS_NVIDIA_RE.match(line)
            if not m:
                continue
            version, kernel = m.groups()
            if version == driver_version or version.startswith(f"{driver_version}-"):
                if kernel not in matching:
                    matching.append(kernel)
        if not matching and dkms_lines:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="DKMS_DRIVER_VERSION_MISMATCH",
                    message=(
                        f"No DKMS entry matches driver {driver_version!r}. "
                        "Recorded DKMS lines are retained for inspection."
                    ),
                    context={"dkms_status_lines": list(dkms_lines)},
                )
            )
        return tuple(matching)

    def _read_nvcc_version(
        self, findings: list[ValidationFinding]
    ) -> str | None:
        candidates: list[tuple[str, ...]] = [("nvcc", "--version")]
        for path in self._nvcc_paths:
            candidates.append((path, "--version"))
        for argv in candidates:
            text, _finding = self._exec(argv, timeout=10.0)
            if text is None:
                continue
            m = _NVCC_RELEASE_RE.search(text)
            if m:
                return m.group(1)
        findings.append(
            ValidationFinding(
                severity=Severity.INFO,
                code="NVCC_UNAVAILABLE",
                message="Could not determine CUDA Toolkit version via nvcc --version.",
            )
        )
        return None

    def _list_boot_configs(self) -> tuple[str, ...]:
        entries = self._fs.list_dir(Path("/boot"))
        names = []
        for entry in entries:
            name = Path(str(entry)).name
            if name.startswith("config-"):
                names.append(name[len("config-"):])
        return tuple(sorted(names))

    def _list_kernel_headers(self) -> tuple[str, ...]:
        modules_root = Path("/lib/modules")
        if not self._fs.exists(modules_root):
            return ()
        entries = self._fs.list_dir(modules_root)
        releases = []
        for entry in entries:
            name = Path(str(entry)).name
            if self._fs.exists(modules_root / name / "build"):
                releases.append(name)
        return tuple(sorted(releases))

    def _merge_gpus(
        self,
        nvidia_gpus: tuple[GPUIdentity, ...],
        lspci_gpus: tuple[GPUIdentity, ...],
    ) -> tuple[GPUIdentity, ...]:
        by_pci: dict[str, GPUIdentity] = {g.pci_address: g for g in lspci_gpus}
        for g in nvidia_gpus:
            by_pci[g.pci_address] = g
        return tuple(sorted(by_pci.values(), key=lambda g: g.pci_address))

    def _infer_flavor(
        self,
        driver_version: str,
        dkms_lines: tuple[str, ...],
        findings: list[ValidationFinding],
    ) -> ModuleFlavor:
        for line in dkms_lines:
            if "-open" in line.lower():
                findings.append(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="OPEN_MODULE_IN_DKMS",
                        message=(
                            "dkms status references an open NVIDIA module. "
                            "The open flavor is not compatible with Volta "
                            "(sm_70); confirm before proceeding with the V100."
                        ),
                        context={"dkms_line": line},
                    )
                )
                return ModuleFlavor.OPEN
        findings.append(
            ValidationFinding(
                severity=Severity.WARNING,
                code="MODULE_FLAVOR_INFERRED_PROPRIETARY",
                message=(
                    f"Driver {driver_version!r} inferred as proprietary "
                    "(R580 lineage). Verify with 'dkms status' or "
                    "'dpkg -l | grep nvidia' before promoting any build."
                ),
                context={"driver_version": driver_version},
            )
        )
        return ModuleFlavor.PROPRIETARY

    def _build_driver_baseline(
        self,
        *,
        driver_version: str | None,
        cuda_api_version: str | None,
        cuda_toolkit_version: str | None,
        dkms_builds: tuple[str, ...],
        dkms_lines: tuple[str, ...],
        findings: list[ValidationFinding],
    ) -> DriverBaseline | None:
        if not driver_version:
            return None
        flavor = self._infer_flavor(driver_version, dkms_lines, findings)
        return DriverBaseline(
            driver_version=driver_version,
            module_flavor=flavor,
            cuda_api_version=cuda_api_version,
            cuda_toolkit_version=cuda_toolkit_version,
            dkms_builds=dkms_builds,
        )


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def collect_inventory(
    runner: RunnerProtocol,
    *,
    host_fs: HostFs | None = None,
) -> InventoryReport:
    """One-shot convenience wrapper around :class:`HostInventory`."""
    return HostInventory(runner, host_fs=host_fs).collect()
