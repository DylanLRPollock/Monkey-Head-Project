"""Typed immutable models for the HueyOS kernel build framework.

Every model here is a ``frozen`` dataclass with ``slots=True``. Models
validate their own field shapes in ``__post_init__`` and expose
JSON-serializable ``to_dict()`` / ``from_dict()`` helpers.

Cross-field and profile-specific rules -- for example, "Tesla V100 must use
the proprietary NVIDIA module flavor" or "Secure Boot enabled plus unsigned
module equals not boot-ready" -- are enforced by ``huey.kernel_build.policy``
(Step 5), not by these models, so this module remains a pure, independently
testable description of data shapes.

Path conventions
----------------
* ``workspace`` and ``output_dir`` are *output* locations. They must be
  relative and must not contain ``..`` components.
* ``KernelSource.baseline_config`` is a *read-only input* path; it may be
  absolute (e.g. ``/boot/config-$(uname -r)``) or relative to the workspace.
* ``DriverBaseline.dkms_builds`` is a tuple of kernel release strings
  (e.g. ``("7.2.12+deb14-amd64", "7.2.15+deb14-amd64")``).
* ``DriverBaseline`` keeps three CUDA-adjacent values distinct:
  ``driver_version`` (the driver release, e.g. ``"580.196.07"``),
  ``cuda_api_version`` (the driver-advertised API, e.g. ``"13.0"`` as shown
  by ``nvidia-smi``), and ``cuda_toolkit_version`` (the installed ``nvcc``
  version). These are never conflated.
"""

from __future__ import annotations

import math
import re
from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

__all__ = [
    "ApprovalState",
    "ArtifactKind",
    "BuildArtifact",
    "BuildReport",
    "BuildStatus",
    "CommandResult",
    "DriverBaseline",
    "GPUIdentity",
    "GPUVendor",
    "KernelPlan",
    "KernelSource",
    "ModuleFlavor",
    "Severity",
    "SigningPolicy",
    "SourceType",
    "ValidationFinding",
]

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BuildStatus(StrEnum):
    PENDING = "pending"
    PLANNED = "planned"
    RUNNING = "running"
    BUILT = "built"
    VERIFIED = "verified"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_READY = "not_ready"


class ApprovalState(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NOT_REQUIRED = "not_required"


class SourceType(StrEnum):
    DEBIAN_LINUX_SOURCE = "debian-linux-source"
    UPSTREAM = "upstream"


class ModuleFlavor(StrEnum):
    PROPRIETARY = "proprietary"
    OPEN = "open"


class SigningPolicy(StrEnum):
    REQUIRED_IF_SECUREBOOT = "required_if_secureboot"
    REQUIRED = "required"


class GPUVendor(StrEnum):
    NVIDIA = "nvidia"
    AMD = "amd"


class ArtifactKind(StrEnum):
    KERNEL_IMAGE_DEB = "kernel-image-deb"
    KERNEL_HEADERS_DEB = "kernel-headers-deb"
    NVIDIA_MODULE = "nvidia-module"
    INITRAMFS = "initramfs"
    MANIFEST = "manifest"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SHA256_CHARS = frozenset("0123456789abcdef")
_PCI_BDF_RE = re.compile(r"^[0-9a-f]{1,8}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$")
_SM_RE = re.compile(r"^sm_[0-9]+$")
_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _is_sha256_hex(value: Any) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in _SHA256_CHARS for c in value))


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty str, got {value!r}")
    return value


def _require_relative_no_escape(value: Any, field_name: str) -> Path:
    """Accept str or Path; require relative with no ``..`` components."""
    if isinstance(value, Path):
        path = value
    elif isinstance(value, str):
        if not value.strip():
            raise ValueError(f"{field_name} must be non-empty")
        path = Path(value)
    else:
        raise TypeError(
            f"{field_name} must be str or Path, got {type(value).__name__}"
        )
    if path == Path(".") or "\x00" in str(path):
        raise ValueError(f"{field_name} must identify a non-empty destination")
    if path.is_absolute():
        raise ValueError(f"{field_name} must be relative, got {path!r}")
    if ".." in path.parts:
        raise ValueError(f"{field_name} must not contain '..': {path!r}")
    return path


def _value_to_jsonable(value: Any) -> Any:
    """Recursively convert a value to a JSON-serializable form."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {k: _value_to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_value_to_jsonable(v) for v in value]
    if is_dataclass(value) and not isinstance(value, type):
        return _dataclass_to_dict(value)
    raise TypeError(
        f"Cannot JSON-serialize value of type {type(value).__name__}: {value!r}"
    )


def _dataclass_to_dict(obj: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for f in fields(obj):
        result[f.name] = _value_to_jsonable(getattr(obj, f.name))
    return result


_REDACT_KEYWORDS = ("KEY", "TOKEN", "SECRET", "PASS", "PIN", "CREDENTIAL")


def _require_known_fields(data: Any, cls: type) -> None:
    """Reject unrecognized serialized fields rather than ignoring them silently."""
    if not isinstance(data, dict):
        raise TypeError(f"{cls.__name__}.from_dict expects a dict")
    known = {f.name for f in fields(cls)}
    if not all(isinstance(k, str) for k in data):
        raise TypeError(f"{cls.__name__}.from_dict keys must be strings")
    unknown = set(data) - known
    if unknown:
        raise ValueError(f"{cls.__name__}.from_dict unknown fields: {sorted(unknown)!r}")
    required = {
        f.name for f in fields(cls)
        if f.default is MISSING and f.default_factory is MISSING
    }
    missing = required - set(data)
    if missing:
        raise ValueError(f"{cls.__name__}.from_dict missing fields: {sorted(missing)!r}")


def _redact_env(env: dict[str, str]) -> dict[str, str]:
    """Replace values of environment variables whose names look sensitive."""
    redacted: dict[str, str] = {}
    for key, value in env.items():
        upper = key.upper()
        if any(kw in upper for kw in _REDACT_KEYWORDS):
            redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    return redacted


# ---------------------------------------------------------------------------
# KernelSource
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class KernelSource:
    """Pinned kernel source identity.

    Null fields mean "not yet pinned"; ``build-kernel`` must refuse to run
    while required fields are unresolved. ``checksum`` when present is the
    SHA-256 of the retrieved source artifact.
    """

    source_type: SourceType
    source: str | None = None
    version: str | None = None
    checksum: str | None = None
    localversion: str = "-huey1"
    baseline_config: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.source_type, str):
            try:
                object.__setattr__(self, "source_type", SourceType(self.source_type))
            except ValueError as exc:
                raise ValueError(
                    f"KernelSource.source_type={self.source_type!r} is not valid; "
                    f"expected one of {[s.value for s in SourceType]}"
                ) from exc
        if not isinstance(self.source_type, SourceType):
            raise TypeError("KernelSource.source_type must be a SourceType")
        for name in ("source", "version", "baseline_config"):
            value = getattr(self, name)
            if value is not None:
                _require_str(value, f"KernelSource.{name}")
        _require_str(self.localversion, "KernelSource.localversion")
        if self.checksum is not None and not _is_sha256_hex(self.checksum):
            raise ValueError(
                "KernelSource.checksum must be a 64-char lowercase hex SHA-256 "
                f"when set, got {self.checksum!r}"
            )

    @property
    def is_resolved(self) -> bool:
        return all(
            v is not None and v != ""
            for v in (self.source, self.version, self.checksum)
        )

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KernelSource:
        _require_known_fields(data, cls)
        if "source_type" not in data:
            raise ValueError("KernelSource.from_dict: missing required 'source_type'")
        return cls(
            source_type=data["source_type"],
            source=data.get("source"),
            version=data.get("version"),
            checksum=data.get("checksum"),
            localversion=data.get("localversion", "-huey1"),
            baseline_config=data.get("baseline_config"),
        )


# ---------------------------------------------------------------------------
# GPUIdentity
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class GPUIdentity:
    """Read-only identity of a GPU observed on the host."""

    vendor: GPUVendor
    model: str
    pci_address: str
    uuid: str | None = None
    compute_capability: str | None = None

    def __post_init__(self) -> None:
        if isinstance(self.vendor, str):
            try:
                object.__setattr__(self, "vendor", GPUVendor(self.vendor))
            except ValueError as exc:
                raise ValueError(
                    f"GPUIdentity.vendor={self.vendor!r} is not valid; "
                    f"expected one of {[v.value for v in GPUVendor]}"
                ) from exc
        if not isinstance(self.vendor, GPUVendor):
            raise TypeError("GPUIdentity.vendor must be a GPUVendor")
        if self.uuid is not None:
            _require_str(self.uuid, "GPUIdentity.uuid")
        _require_str(self.model, "GPUIdentity.model")
        _require_str(self.pci_address, "GPUIdentity.pci_address")
        if not _PCI_BDF_RE.match(self.pci_address):
            raise ValueError(
                "GPUIdentity.pci_address must be a PCI BDF such as "
                f"'00000000:01:00.0', got {self.pci_address!r}"
            )
        if self.compute_capability is not None:
            if self.vendor != GPUVendor.NVIDIA:
                raise ValueError(
                    f"GPUIdentity.compute_capability is only meaningful for NVIDIA "
                    f"GPUs, got vendor={self.vendor!r}"
                )
            if not _SM_RE.match(self.compute_capability):
                raise ValueError(
                    "GPUIdentity.compute_capability must be 'sm_<digits>' such as "
                    f"'sm_70', got {self.compute_capability!r}"
                )

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GPUIdentity:
        _require_known_fields(data, cls)
        return cls(
            vendor=data["vendor"],
            model=data["model"],
            pci_address=data["pci_address"],
            uuid=data.get("uuid"),
            compute_capability=data.get("compute_capability"),
        )


# ---------------------------------------------------------------------------
# DriverBaseline
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DriverBaseline:
    """Observed driver baseline.

    Three distinct versions are kept separate on purpose:

    * ``driver_version`` -- driver release, e.g. ``"580.196.07"``.
    * ``cuda_api_version`` -- API the driver advertises, e.g. ``"13.0"``.
    * ``cuda_toolkit_version`` -- installed ``nvcc`` version, e.g. ``"12.9"``.

    ``module_flavor`` accepts either flavor at the model level; which flavors
    are acceptable for a given profile is decided by ``policy.py``.
    """

    driver_version: str
    module_flavor: ModuleFlavor
    cuda_api_version: str | None = None
    cuda_toolkit_version: str | None = None
    dkms_builds: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_str(self.driver_version, "DriverBaseline.driver_version")
        if isinstance(self.module_flavor, str):
            try:
                object.__setattr__(
                    self, "module_flavor", ModuleFlavor(self.module_flavor)
                )
            except ValueError as exc:
                raise ValueError(
                    f"DriverBaseline.module_flavor={self.module_flavor!r} is not "
                    f"valid; expected one of {[m.value for m in ModuleFlavor]}"
                ) from exc
        if not isinstance(self.module_flavor, ModuleFlavor):
            raise TypeError("DriverBaseline.module_flavor must be a ModuleFlavor")
        for name in ("cuda_api_version", "cuda_toolkit_version"):
            value = getattr(self, name)
            if value is not None:
                _require_str(value, f"DriverBaseline.{name}")
        builds = self.dkms_builds
        if isinstance(builds, list):
            builds = tuple(builds)
            object.__setattr__(self, "dkms_builds", builds)
        if not isinstance(builds, tuple) or not all(isinstance(b, str) and b for b in builds):
            raise TypeError("DriverBaseline.dkms_builds must be tuple[str, ...]")

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DriverBaseline:
        _require_known_fields(data, cls)
        return cls(
            driver_version=data["driver_version"],
            module_flavor=data["module_flavor"],
            cuda_api_version=data.get("cuda_api_version"),
            cuda_toolkit_version=data.get("cuda_toolkit_version"),
            dkms_builds=tuple(data.get("dkms_builds", ())),
        )


# ---------------------------------------------------------------------------
# KernelPlan
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class KernelPlan:
    """A planned (not necessarily executed) kernel build."""

    profile: str
    source: KernelSource
    driver: DriverBaseline
    workspace: Path
    output_dir: Path
    build_jobs: int = 4
    signing_policy: SigningPolicy = SigningPolicy.REQUIRED_IF_SECUREBOOT
    target_release: str | None = None
    tool_versions: dict[str, str] = field(default_factory=dict)
    intended_artifacts: tuple[ArtifactKind, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_str(self.profile, "KernelPlan.profile")
        if type(self.build_jobs) is not int or self.build_jobs < 1:
            raise ValueError(
                f"KernelPlan.build_jobs must be a positive int, got {self.build_jobs!r}"
            )
        if isinstance(self.signing_policy, str):
            try:
                object.__setattr__(
                    self, "signing_policy", SigningPolicy(self.signing_policy)
                )
            except ValueError as exc:
                raise ValueError(
                    f"KernelPlan.signing_policy={self.signing_policy!r} is not "
                    f"valid; expected one of {[p.value for p in SigningPolicy]}"
                ) from exc
        object.__setattr__(
            self,
            "workspace",
            _require_relative_no_escape(self.workspace, "KernelPlan.workspace"),
        )
        object.__setattr__(
            self,
            "output_dir",
            _require_relative_no_escape(self.output_dir, "KernelPlan.output_dir"),
        )
        if not isinstance(self.source, KernelSource):
            raise TypeError("KernelPlan.source must be a KernelSource")
        if not isinstance(self.driver, DriverBaseline):
            raise TypeError("KernelPlan.driver must be a DriverBaseline")
        if self.target_release is not None:
            _require_str(self.target_release, "KernelPlan.target_release")
        if not isinstance(self.tool_versions, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in self.tool_versions.items()
        ):
            raise TypeError("KernelPlan.tool_versions must be dict[str, str]")
        kinds = self.intended_artifacts
        if isinstance(kinds, list):
            kinds = tuple(kinds)
            object.__setattr__(self, "intended_artifacts", kinds)
        if not isinstance(kinds, tuple) or not all(
            isinstance(k, ArtifactKind) for k in kinds
        ):
            raise TypeError(
                "KernelPlan.intended_artifacts must be tuple[ArtifactKind, ...]"
            )

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KernelPlan:
        _require_known_fields(data, cls)
        return cls(
            profile=data["profile"],
            source=KernelSource.from_dict(data["source"]),
            driver=DriverBaseline.from_dict(data["driver"]),
            workspace=Path(data["workspace"]),
            output_dir=Path(data["output_dir"]),
            build_jobs=data.get("build_jobs", 4),
            signing_policy=data.get("signing_policy", SigningPolicy.REQUIRED_IF_SECUREBOOT),
            target_release=data.get("target_release"),
            tool_versions=dict(data.get("tool_versions", {})),
            intended_artifacts=tuple(
                ArtifactKind(k) for k in data.get("intended_artifacts", ())
            ),
        )


# ---------------------------------------------------------------------------
# CommandResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Result of a single subprocess invocation.

    Environment metadata is redacted at construction: any variable whose name
    contains ``KEY``, ``TOKEN``, ``SECRET``, ``PASS``, ``PIN``, or
    ``CREDENTIAL`` has its value replaced with ``<redacted>``. Use
    :func:`redact_environment` if you need to build the dict yourself.
    """

    argv: tuple[str, ...]
    cwd: str
    returncode: int
    elapsed_seconds: float
    stdout_path: str | None = None
    stderr_path: str | None = None
    env_summary: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        argv = self.argv
        if isinstance(argv, list):
            argv = tuple(argv)
            object.__setattr__(self, "argv", argv)
        if not isinstance(argv, tuple) or not all(isinstance(a, str) for a in argv):
            raise TypeError("CommandResult.argv must be tuple[str, ...]")
        if not argv:
            raise ValueError("CommandResult.argv must be non-empty")
        _require_str(self.cwd, "CommandResult.cwd")
        if type(self.returncode) is not int:
            raise TypeError("CommandResult.returncode must be int")
        if type(self.elapsed_seconds) not in (int, float):
            raise TypeError("CommandResult.elapsed_seconds must be numeric")
        if not math.isfinite(self.elapsed_seconds) or self.elapsed_seconds < 0:
            raise ValueError("CommandResult.elapsed_seconds must be finite and nonnegative")
        for name in ("stdout_path", "stderr_path"):
            value = getattr(self, name)
            if value is not None:
                _require_str(value, f"CommandResult.{name}")
        if not isinstance(self.env_summary, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in self.env_summary.items()
        ):
            raise TypeError("CommandResult.env_summary must be dict[str, str]")
        object.__setattr__(self, "env_summary", _redact_env(self.env_summary))

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CommandResult:
        _require_known_fields(data, cls)
        return cls(
            argv=tuple(data["argv"]),
            cwd=data["cwd"],
            returncode=data["returncode"],
            elapsed_seconds=data["elapsed_seconds"],
            stdout_path=data.get("stdout_path"),
            stderr_path=data.get("stderr_path"),
            env_summary=dict(data.get("env_summary", {})),
        )


def redact_environment(env: dict[str, str]) -> dict[str, str]:
    """Public helper for callers building ``CommandResult.env_summary``."""
    return _redact_env(env)


# ---------------------------------------------------------------------------
# BuildArtifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BuildArtifact:
    """A produced file, identified by kind, relative path, and SHA-256."""

    kind: ArtifactKind
    path: str
    sha256: str
    size_bytes: int
    kernel_release: str

    def __post_init__(self) -> None:
        if isinstance(self.kind, str):
            try:
                object.__setattr__(self, "kind", ArtifactKind(self.kind))
            except ValueError as exc:
                raise ValueError(
                    f"BuildArtifact.kind={self.kind!r} is not valid; expected one "
                    f"of {[k.value for k in ArtifactKind]}"
                ) from exc
        if not isinstance(self.kind, ArtifactKind):
            raise TypeError("BuildArtifact.kind must be an ArtifactKind")
        _require_relative_no_escape(self.path, "BuildArtifact.path")
        if not _is_sha256_hex(self.sha256):
            raise ValueError(
                "BuildArtifact.sha256 must be a 64-char lowercase hex SHA-256, "
                f"got {self.sha256!r}"
            )
        if type(self.size_bytes) is not int or self.size_bytes < 0:
            raise ValueError(
                f"BuildArtifact.size_bytes must be a non-negative int, got "
                f"{self.size_bytes!r}"
            )
        _require_str(self.kernel_release, "BuildArtifact.kernel_release")

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BuildArtifact:
        _require_known_fields(data, cls)
        return cls(
            kind=data["kind"],
            path=data["path"],
            sha256=data["sha256"],
            size_bytes=data["size_bytes"],
            kernel_release=data["kernel_release"],
        )


# ---------------------------------------------------------------------------
# ValidationFinding
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ValidationFinding:
    """A single observation produced by verification or inspection."""

    severity: Severity
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.severity, str):
            try:
                object.__setattr__(self, "severity", Severity(self.severity))
            except ValueError as exc:
                raise ValueError(
                    f"ValidationFinding.severity={self.severity!r} is not valid; "
                    f"expected one of {[s.value for s in Severity]}"
                ) from exc
        if not isinstance(self.severity, Severity):
            raise TypeError("ValidationFinding.severity must be a Severity")
        _require_str(self.code, "ValidationFinding.code")
        _require_str(self.message, "ValidationFinding.message")
        if not isinstance(self.context, dict) or not all(
            isinstance(k, str) for k in self.context
        ):
            raise TypeError("ValidationFinding.context must be dict[str, JSON] ")
        _value_to_jsonable(self.context)

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ValidationFinding:
        _require_known_fields(data, cls)
        return cls(
            severity=data["severity"],
            code=data["code"],
            message=data["message"],
            context=dict(data.get("context", {})),
        )


# ---------------------------------------------------------------------------
# BuildReport
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BuildReport:
    """Assembled result of a build and its verification passes."""

    plan: KernelPlan
    artifacts: tuple[BuildArtifact, ...]
    findings: tuple[ValidationFinding, ...]
    status: BuildStatus
    approval: ApprovalState
    generated_at: str  # ISO 8601

    def __post_init__(self) -> None:
        if not isinstance(self.plan, KernelPlan):
            raise TypeError("BuildReport.plan must be a KernelPlan")
        arts = self.artifacts
        if isinstance(arts, list):
            arts = tuple(arts)
            object.__setattr__(self, "artifacts", arts)
        if not isinstance(arts, tuple) or not all(
            isinstance(a, BuildArtifact) for a in arts
        ):
            raise TypeError("BuildReport.artifacts must be tuple[BuildArtifact, ...]")
        fnds = self.findings
        if isinstance(fnds, list):
            fnds = tuple(fnds)
            object.__setattr__(self, "findings", fnds)
        if not isinstance(fnds, tuple) or not all(
            isinstance(f, ValidationFinding) for f in fnds
        ):
            raise TypeError(
                "BuildReport.findings must be tuple[ValidationFinding, ...]"
            )
        if isinstance(self.status, str):
            try:
                object.__setattr__(self, "status", BuildStatus(self.status))
            except ValueError as exc:
                raise ValueError(f"BuildReport.status is invalid: {self.status!r}") from exc
        if isinstance(self.approval, str):
            try:
                object.__setattr__(self, "approval", ApprovalState(self.approval))
            except ValueError as exc:
                raise ValueError(f"BuildReport.approval is invalid: {self.approval!r}") from exc
        if not isinstance(self.status, BuildStatus):
            raise TypeError("BuildReport.status must be a BuildStatus")
        if not isinstance(self.approval, ApprovalState):
            raise TypeError("BuildReport.approval must be an ApprovalState")
        _require_str(self.generated_at, "BuildReport.generated_at")
        if not _ISO8601_RE.match(self.generated_at):
            raise ValueError(
                "BuildReport.generated_at must be ISO 8601 "
                f"(e.g. '2026-11-12T08:00:00Z'), got {self.generated_at!r}"
            )
        try:
            datetime.fromisoformat(self.generated_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("BuildReport.generated_at is not a valid ISO 8601 timestamp") from exc

    def to_dict(self) -> dict[str, Any]:
        return _dataclass_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BuildReport:
        _require_known_fields(data, cls)
        return cls(
            plan=KernelPlan.from_dict(data["plan"]),
            artifacts=tuple(BuildArtifact.from_dict(a) for a in data["artifacts"]),
            findings=tuple(
                ValidationFinding.from_dict(f) for f in data.get("findings", ())
            ),
            status=data["status"],
            approval=data["approval"],
            generated_at=data["generated_at"],
        )
