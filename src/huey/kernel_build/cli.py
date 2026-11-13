"""Command-line interface for the HueyOS kernel build framework.

Read-only subcommands (``inventory``, ``doctor``, ``plan``, ``verify``) never
mutate host state. Build subcommands (``config``, ``build-kernel``,
``build-nvidia``, ``initramfs``, ``sign``, ``release``) write only to the
caller-supplied output or release directory and support ``--dry-run``.

There is deliberately no ``install`` or ``reboot`` subcommand. Deployment
and first-boot are handled by ``docs/runbooks/huey-kernel-upgrade.md``
(Step 29) with explicit human approval.

Every subcommand returns a :class:`CliResult` carrying a stable JSON shape
and a centralized :class:`ExitCode`. ``main()`` reads ``sys.argv`` and
returns an ``int`` (matching the launcher contract from Step 13); argparse
errors and ``--help`` propagate the standard SystemExit codes 0 and 2.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Sequence

from huey.kernel_build.models import (
    DriverBaseline,
    KernelPlan,
    KernelSource,
    ModuleFlavor,
    Severity,
    SigningPolicy,
    SourceType,
    ValidationFinding,
)
from huey.kernel_build.policy import (
    PolicyDecision,
    SecureBootState,
    assert_allowed,
    evaluate_build_plan,
)
from huey.kernel_build.runner import RunnerProtocol

__all__ = ["CliResult", "ExitCode", "main"]


# ---------------------------------------------------------------------------
# Exit codes (centralized)
# ---------------------------------------------------------------------------


class ExitCode(IntEnum):
    """Documented exit codes for ``huey-kernel``.

    ``0``  success
    ``2``  bad input or invalid policy
    ``3``  missing prerequisites (file not found, PyYAML absent, …)
    ``4``  build or validation failure
    ``5``  operator approval required (reserved; no subcommand triggers it yet)
    """

    SUCCESS = 0
    BAD_INPUT = 2
    MISSING_PREREQUISITES = 3
    BUILD_FAILURE = 4
    APPROVAL_REQUIRED = 5


class CliError(Exception):
    """Raised by subcommands to short-circuit with a specific exit code."""

    def __init__(self, code: ExitCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CliResult:
    subcommand: str
    status: str  # "ok" | "dry_run" | "error"
    exit_code: int
    message: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    findings: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "subcommand": self.subcommand,
            "status": self.status,
            "exit_code": self.exit_code,
            "message": self.message,
            "payload": self.payload,
            "findings": list(self.findings),
        }

    def to_text(self) -> str:
        lines = [f"{self.subcommand}: {self.status} (exit {self.exit_code})"]
        if self.message:
            lines.append(f"  {self.message}")
        for finding in self.findings:
            sev = str(finding.get("severity", "?")).upper()
            code = finding.get("code", "?")
            msg = finding.get("message", "")
            lines.append(f"  [{sev}] {code}: {msg}")
        if self.payload:
            lines.append("  payload:")
            lines.append(json.dumps(self.payload, indent=4, sort_keys=True))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# DI seam for tests
# ---------------------------------------------------------------------------


def _make_runner() -> RunnerProtocol:
    """Construct the default subprocess runner.

    Tests patch this function to return a fake runner so subcommands can be
    exercised without spawning real subprocesses.
    """
    from huey.kernel_build.runner import Runner

    return Runner()


# ---------------------------------------------------------------------------
# build.yaml loading
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BuildIntent:
    schema_version: int
    profile: str
    source_type: SourceType
    source: str | None
    version: str | None
    checksum: str | None
    localversion: str
    baseline_config: str | None
    nvidia_version: str
    nvidia_module_flavor: ModuleFlavor
    nvidia_source_kind: str
    nvidia_source_path: str | None
    jobs: int
    workspace: Path
    output: Path
    signing_required_policy: SigningPolicy
    signing_key_path: str | None
    signing_cert_path: str | None
    allow_host_mutation: bool
    allow_root_build: bool
    allow_network_fetch: bool


def _load_build_intent(path: Path) -> BuildIntent:
    """Load and validate ``build.yaml`` into a :class:`BuildIntent`."""
    try:
        import yaml  # type: ignore[import-not-found]
    except ImportError as exc:
        raise CliError(
            ExitCode.MISSING_PREREQUISITES,
            "PyYAML is not installed; install it (Step 31 of the handoff "
            "adds it to the project dependencies) or run 'pip install pyyaml'.",
        ) from exc

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CliError(
            ExitCode.MISSING_PREREQUISITES,
            f"Cannot read build intent {path}: {exc}",
        ) from exc

    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise CliError(
            ExitCode.BAD_INPUT,
            f"Invalid YAML in {path}: {exc}",
        ) from exc

    if not isinstance(raw, dict):
        raise CliError(
            ExitCode.BAD_INPUT,
            f"{path} must contain a YAML mapping at the top level.",
        )

    try:
        schema_version = int(raw["schema_version"])
    except (KeyError, TypeError, ValueError) as exc:
        raise CliError(
            ExitCode.BAD_INPUT, f"{path}: missing or invalid 'schema_version'."
        ) from exc
    if schema_version != 1:
        raise CliError(
            ExitCode.BAD_INPUT,
            f"{path}: unsupported schema_version {schema_version}; expected 1.",
        )

    try:
        profile = str(raw["profile"])
        kernel = raw["kernel"]
        nvidia = raw["nvidia"]
        build = raw["build"]
        paths = raw["paths"]
        signing = raw["signing"]
        safety = raw["safety"]
    except (KeyError, TypeError) as exc:
        raise CliError(
            ExitCode.BAD_INPUT, f"{path}: missing required section: {exc}"
        ) from exc

    try:
        source_type = SourceType(kernel["source_type"])
    except (KeyError, ValueError) as exc:
        raise CliError(
            ExitCode.BAD_INPUT,
            f"{path}: invalid kernel.source_type: {exc}",
        ) from exc

    try:
        module_flavor = ModuleFlavor(nvidia["module_flavor"])
    except (KeyError, ValueError) as exc:
        raise CliError(
            ExitCode.BAD_INPUT,
            f"{path}: invalid nvidia.module_flavor: {exc}",
        ) from exc

    try:
        signing_policy = SigningPolicy(signing["required_policy"])
    except (KeyError, ValueError) as exc:
        raise CliError(
            ExitCode.BAD_INPUT,
            f"{path}: invalid signing.required_policy: {exc}",
        ) from exc

    try:
        jobs = int(build.get("jobs", 4))
    except (TypeError, ValueError) as exc:
        raise CliError(
            ExitCode.BAD_INPUT, f"{path}: invalid build.jobs: {exc}"
        ) from exc
    if jobs < 1:
        raise CliError(ExitCode.BAD_INPUT, f"{path}: build.jobs must be >= 1.")

    return BuildIntent(
        schema_version=schema_version,
        profile=profile,
        source_type=source_type,
        source=kernel.get("source"),
        version=kernel.get("version"),
        checksum=kernel.get("checksum"),
        localversion=str(kernel.get("localversion", "-huey1")),
        baseline_config=kernel.get("baseline_config"),
        nvidia_version=str(nvidia["version"]),
        nvidia_module_flavor=module_flavor,
        nvidia_source_kind=str(nvidia.get("source_kind", "dkms-local")),
        nvidia_source_path=nvidia.get("source_path"),
        jobs=jobs,
        workspace=Path(paths["workspace"]),
        output=Path(paths["output"]),
        signing_required_policy=signing_policy,
        signing_key_path=signing.get("key_path"),
        signing_cert_path=signing.get("cert_path"),
        allow_host_mutation=bool(safety.get("allow_host_mutation", False)),
        allow_root_build=bool(safety.get("allow_root_build", False)),
        allow_network_fetch=bool(safety.get("allow_network_fetch", False)),
    )


def _intent_to_kernel_plan(intent: BuildIntent) -> KernelPlan:
    """Convert a :class:`BuildIntent` into a :class:`KernelPlan`."""
    source = KernelSource(
        source_type=intent.source_type,
        source=intent.source,
        version=intent.version,
        checksum=intent.checksum,
        localversion=intent.localversion,
        baseline_config=intent.baseline_config,
    )
    driver = DriverBaseline(
        driver_version=intent.nvidia_version,
        module_flavor=intent.nvidia_module_flavor,
    )
    return KernelPlan(
        profile=intent.profile,
        source=source,
        driver=driver,
        workspace=intent.workspace,
        output_dir=intent.output,
        build_jobs=intent.jobs,
        signing_policy=intent.signing_required_policy,
    )


def _findings_from_decision(
    decision: PolicyDecision,
) -> tuple[dict[str, Any], ...]:
    combined: list[ValidationFinding] = [
        *decision.violations,
        *decision.findings,
    ]
    return tuple(f.to_dict() for f in combined)


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------


def _cmd_inventory(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.inventory import HostInventory

    report = HostInventory(_make_runner()).collect()
    return CliResult(
        subcommand="inventory",
        status="ok",
        exit_code=int(ExitCode.SUCCESS),
        message=(
            f"kernel={report.running_kernel or 'unknown'} "
            f"secureboot={report.secure_boot.value} "
            f"gpus={len(report.gpus)}"
        ),
        payload=report.to_dict(),
        findings=tuple(f.to_dict() for f in report.findings),
    )


def _cmd_doctor(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.inventory import HostInventory

    report = HostInventory(_make_runner()).collect()
    advice = _doctor_advice(report)
    return CliResult(
        subcommand="doctor",
        status="ok",
        exit_code=int(ExitCode.SUCCESS),
        message=f"{len(advice)} diagnostic item(s)",
        payload={
            "report": report.to_dict(),
            "advice": advice,
        },
        findings=tuple(f.to_dict() for f in report.findings),
    )


def _doctor_advice(report: Any) -> list[str]:
    """Return human-readable next-step advice based on the inventory."""
    advice: list[str] = []
    if report.secure_boot == SecureBootState.UNKNOWN:
        advice.append(
            "Install 'mokutil' or ensure EFI variables are mounted to "
            "determine Secure Boot state before planning a build."
        )
    if report.running_kernel and report.running_kernel not in report.kernel_headers_available:
        advice.append(
            f"Install linux-headers-{report.running_kernel} to enable "
            "out-of-tree module builds for the running kernel."
        )
    if report.driver is None:
        advice.append(
            "No NVIDIA driver detected. Load the proprietary 580.x driver "
            "on the host if you want the inventory to confirm the baseline."
        )
    elif report.driver.module_flavor == ModuleFlavor.OPEN:
        advice.append(
            "The open NVIDIA module flavor is not compatible with the "
            "Tesla V100 (sm_70). Switch to the proprietary 580.196.07 branch."
        )
    if not any(g.compute_capability == "sm_70" for g in report.gpus):
        advice.append(
            "No Tesla V100 (sm_70) was identified. Verify 'lspci -nnk' and "
            "'nvidia-smi -L' if the V100 is expected on this host."
        )
    if not advice:
        advice.append("Environment appears ready for a v100-workstation plan.")
    return advice


def _cmd_plan(args: argparse.Namespace) -> CliResult:
    intent = _load_build_intent(args.config)
    plan = _intent_to_kernel_plan(intent)

    gpus: Sequence[Any] = ()
    secure_boot_state = SecureBootState.UNKNOWN
    if args.with_inventory:
        from huey.kernel_build.inventory import HostInventory

        report = HostInventory(_make_runner()).collect()
        gpus = report.gpus
        secure_boot_state = report.secure_boot

    key_present = bool(
        intent.signing_key_path and Path(intent.signing_key_path).is_file()
    )
    cert_present = bool(
        intent.signing_cert_path and Path(intent.signing_cert_path).is_file()
    )

    decision = evaluate_build_plan(
        plan,
        allow_host_mutation=intent.allow_host_mutation,
        allow_root_build=intent.allow_root_build,
        gpu_identities=tuple(gpus),
        secure_boot_state=secure_boot_state,
        key_present=key_present,
        cert_present=cert_present,
        cwd=Path.cwd(),
    )

    exit_code = int(ExitCode.SUCCESS) if decision.allowed else int(ExitCode.BAD_INPUT)
    status = "ok" if decision.allowed else "error"
    return CliResult(
        subcommand="plan",
        status=status,
        exit_code=exit_code,
        message=(
            f"Plan {'allowed' if decision.allowed else 'blocked'}"
            + ("" if args.with_inventory else " (static; --with-inventory for deep check)")
        ),
        payload={
            "allowed": decision.allowed,
            "requires_approval": decision.requires_approval,
            "profile": plan.profile,
            "source": plan.source.to_dict(),
            "driver": plan.driver.to_dict(),
            "workspace": str(plan.workspace),
            "output_dir": str(plan.output_dir),
            "build_jobs": plan.build_jobs,
            "signing_policy": plan.signing_policy.value,
        },
        findings=_findings_from_decision(decision),
    )


def _cmd_config(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.config_builder import ConfigBuilder

    intent = _load_build_intent(args.config)
    result = ConfigBuilder(_make_runner()).build(
        source_dir=args.source_dir,
        base_config_path=args.base_config,
        fragments=tuple(args.fragment),
        output_dir=args.output_dir,
        profile=intent.profile,
        dry_run=args.dry_run,
    )
    if result.has_errors():
        return _component_error(
            subcommand="config",
            findings=result.findings,
            payload={
                "effective_config_path": (
                    str(result.effective_config_path)
                    if result.effective_config_path
                    else None
                ),
            },
        )
    return CliResult(
        subcommand="config",
        status="dry_run" if result.dry_run else "ok",
        exit_code=int(ExitCode.SUCCESS),
        message=(
            f"Effective .config at {result.effective_config_path}"
            if result.effective_config_path
            else "dry run planned"
        ),
        payload={
            "effective_config_path": (
                str(result.effective_config_path)
                if result.effective_config_path
                else None
            ),
            "delta_report_path": (
                str(result.delta_report_path) if result.delta_report_path else None
            ),
            "added": [list(a) for a in result.delta.added],
            "removed": [list(a) for a in result.delta.removed],
            "changed": [list(a) for a in result.delta.changed],
            "overrides": [o.symbol for o in result.overrides],
            "dry_run": result.dry_run,
        },
        findings=tuple(f.to_dict() for f in result.findings),
    )


def _cmd_build_kernel(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.kernel_builder import KernelBuilder

    intent = _load_build_intent(args.config)
    localversion = args.localversion or intent.localversion
    jobs = args.jobs if args.jobs is not None else intent.jobs

    result = KernelBuilder(_make_runner()).build(
        source_dir=args.source_dir,
        config_path=args.effective_config,
        output_dir=args.output_dir,
        localversion=localversion,
        jobs=jobs,
        source_date_epoch=args.source_date_epoch,
        dry_run=args.dry_run,
    )

    payload: dict[str, Any] = {
        "kernel_release": result.kernel_release,
        "image_deb": result.image_deb.to_dict() if result.image_deb else None,
        "headers_deb": result.headers_deb.to_dict() if result.headers_deb else None,
        "dry_run": result.dry_run,
    }

    # Write breadcrumb for later subcommands (only on real success).
    if not result.dry_run and not result.has_errors() and result.kernel_release:
        breadcrumb = args.output_dir / "kernel-release.json"
        try:
            breadcrumb.parent.mkdir(parents=True, exist_ok=True)
            breadcrumb.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            payload["breadcrumb_path"] = str(breadcrumb)
        except OSError as exc:
            return _component_error(
                subcommand="build-kernel",
                findings=(
                    ValidationFinding(
                        severity=Severity.WARNING,
                        code="BREADCRUMB_WRITE_FAILED",
                        message=f"Could not write {breadcrumb}: {exc}",
                    ),
                ),
                payload=payload,
            )

    if result.has_errors():
        return _component_error(
            subcommand="build-kernel",
            findings=result.findings,
            payload=payload,
        )
    return CliResult(
        subcommand="build-kernel",
        status="dry_run" if result.dry_run else "ok",
        exit_code=int(ExitCode.SUCCESS),
        message=(
            f"kernel_release={result.kernel_release}"
            if result.kernel_release
            else "dry run planned"
        ),
        payload=payload,
        findings=tuple(f.to_dict() for f in result.findings),
    )


def _cmd_build_nvidia(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.nvidia_builder import NvidiaBuilder

    intent = _load_build_intent(args.config)
    result = NvidiaBuilder(_make_runner()).build(
        kernel_release=args.kernel_release,
        driver_version=intent.nvidia_version,
        module_flavor=intent.nvidia_module_flavor,
        headers_dir=args.headers_dir,
        output_dir=args.output_dir,
        dkms_source_dir=args.dkms_source_dir,
        allow_system_dkms_discovery=args.allow_system_dkms_discovery,
        secure_boot_enabled=args.secure_boot_enabled,
        dry_run=args.dry_run,
    )
    payload: dict[str, Any] = {
        "kernel_release": result.kernel_release,
        "driver_version": result.driver_version,
        "module_flavor": result.module_flavor.value,
        "modules": {
            name: art.to_dict() for name, art in result.module_artifacts.items()
        },
        "dry_run": result.dry_run,
    }
    if not result.dry_run and not result.has_errors():
        breadcrumb = args.output_dir / "nvidia-build.json"
        try:
            breadcrumb.parent.mkdir(parents=True, exist_ok=True)
            breadcrumb.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            payload["breadcrumb_path"] = str(breadcrumb)
        except OSError:
            pass  # non-fatal

    if result.has_errors():
        return _component_error(
            subcommand="build-nvidia",
            findings=result.findings,
            payload=payload,
        )
    return CliResult(
        subcommand="build-nvidia",
        status="dry_run" if result.dry_run else "ok",
        exit_code=int(ExitCode.SUCCESS),
        message=(
            f"staged {len(result.module_artifacts)} module(s) for "
            f"{result.kernel_release}"
        ),
        payload=payload,
        findings=tuple(f.to_dict() for f in result.findings),
    )


def _cmd_initramfs(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.initramfs_builder import InitramfsBuilder

    intent = _load_build_intent(args.config)
    result = InitramfsBuilder(_make_runner()).build(
        kernel_release=args.kernel_release,
        module_tree=args.module_tree,
        modules_list_path=args.modules_list,
        modprobe_conf_path=args.modprobe_conf,
        output_dir=args.output_dir,
        include_modprobe_hook=not args.no_modprobe_hook,
        dry_run=args.dry_run,
    )
    payload: dict[str, Any] = {
        "kernel_release": result.kernel_release,
        "initramfs_path": str(result.initramfs_path) if result.initramfs_path else None,
        "initramfs_sha256": result.initramfs_sha256,
        "modules_requested": list(result.modules_requested),
        "modules_present": list(result.modules_present),
        "modules_missing": list(result.modules_missing),
        "dry_run": result.dry_run,
    }
    if result.has_errors():
        return _component_error(
            subcommand="initramfs", findings=result.findings, payload=payload,
        )
    return CliResult(
        subcommand="initramfs",
        status="dry_run" if result.dry_run else "ok",
        exit_code=int(ExitCode.SUCCESS),
        message=(
            f"built {result.initramfs_path.name}"
            if result.initramfs_path
            else "dry run planned"
        ),
        payload=payload,
        findings=tuple(f.to_dict() for f in result.findings),
    )


def _cmd_sign(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.models import ArtifactKind, BuildArtifact
    from huey.kernel_build.signing import (
        SecureBootDetector,
        Signer,
        SigningMaterial,
        evaluate_readiness,
    )

    intent = _load_build_intent(args.config)
    material = SigningMaterial(
        key_path=args.key,
        cert_path=args.cert,
        pin_env_var=args.pin_env_var,
    )
    pin = os.environ.get(args.pin_env_var) if args.use_env_pin else None

    # Discover modules and build their artifacts.
    ko_paths = sorted(args.modules_dir.glob("*.ko"))
    modules: dict[str, BuildArtifact] = {}
    for ko in ko_paths:
        try:
            sha = _sha256_file(ko)
            modules[ko.stem] = BuildArtifact(
                kind=ArtifactKind.NVIDIA_MODULE,
                path=ko.name,
                sha256=sha,
                size_bytes=ko.stat().st_size,
                kernel_release=args.kernel_release or "",
            )
        except OSError as exc:
            return _component_error(
                subcommand="sign",
                findings=(
                    ValidationFinding(
                        severity=Severity.ERROR,
                        code="MODULE_READ_FAILED",
                        message=f"Could not read {ko}: {exc}",
                    ),
                ),
                payload={"modules_dir": str(args.modules_dir)},
            )

    if not modules:
        return CliResult(
            subcommand="sign",
            status="error",
            exit_code=int(ExitCode.BAD_INPUT),
            message=f"No .ko files found in {args.modules_dir}",
            payload={},
            findings=(),
        )

    signer = Signer(_make_runner())
    signed, findings, ok = signer.sign_modules(
        modules=modules,
        module_dir=args.modules_dir,
        material=material,
        headers_dir=args.headers_dir,
        output_dir=args.output_dir,
        pin=pin,
        dry_run=args.dry_run,
    )

    # Detect Secure Boot state only if we were asked to.
    sb_state = SecureBootState.UNKNOWN
    if args.detect_secure_boot:
        sb_state, sb_finding = SecureBootDetector(_make_runner()).detect()
        if sb_finding:
            findings.append(sb_finding)

    ready, readiness_findings = evaluate_readiness(
        secure_boot=sb_state,
        signing_required=intent.signing_required_policy == SigningPolicy.REQUIRED,
        material=material if signed else None,
        signed_modules=signed,
        required_modules=tuple(modules.keys()),
        signed_kernel_image=None,
        kernel_image_required=False,
        module_findings=tuple(findings),
    )
    if readiness_findings:
        findings.extend(readiness_findings)

    payload = {
        "signed_modules": {n: a.to_dict() for n, a in signed.items()},
        "boot_ready": ready,
        "secure_boot": sb_state.value,
        "dry_run": args.dry_run,
    }
    if not ok or not ready:
        return _component_error(
            subcommand="sign",
            findings=tuple(findings),
            payload=payload,
        )
    return CliResult(
        subcommand="sign",
        status="dry_run" if args.dry_run else "ok",
        exit_code=int(ExitCode.SUCCESS),
        message=f"signed {len(signed)} module(s); boot_ready={ready}",
        payload=payload,
        findings=tuple(f.to_dict() for f in findings),
    )


def _cmd_verify(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.verifier import ReleaseVerifier, VerificationContext

    rd = args.release_dir
    if not rd.is_dir():
        raise CliError(
            ExitCode.MISSING_PREREQUISITES,
            f"release_dir not found: {rd}",
        )

    # Infer or accept explicit kernel_release / driver_version.
    kr = args.kernel_release or _infer_kernel_release(rd)
    drv = args.driver_version or _infer_driver_version(rd)

    ctx = VerificationContext(
        release_dir=rd,
        kernel_release=kr,
        driver_version=drv,
        secure_boot_state=args.secure_boot_state,
    )
    result = ReleaseVerifier(_make_runner()).verify_release(ctx, dry_run=args.verify_dry_run)
    status = "ok" if result.boot_ready else "error"
    exit_code = (
        int(ExitCode.SUCCESS) if result.boot_ready else int(ExitCode.BUILD_FAILURE)
    )
    return CliResult(
        subcommand="verify",
        status=status,
        exit_code=exit_code,
        message=(
            f"boot_ready={result.boot_ready} "
            f"static_checks_passed={result.static_checks_passed} "
            f"findings={len(result.findings)}"
        ),
        payload={
            "kernel_release": kr,
            "driver_version": drv,
            "boot_ready": result.boot_ready,
            "static_checks_passed": result.static_checks_passed,
            "host_checks_required": list(result.host_checks_required),
            "dry_run": result.dry_run,
        },
        findings=tuple(f.to_dict() for f in result.findings),
    )


def _cmd_release(args: argparse.Namespace) -> CliResult:
    from huey.kernel_build.release import (
        ReleaseAssembler,
        ReleaseContext,
    )
    from huey.kernel_build.verifier import ReleaseVerifier, VerificationContext

    intent = _load_build_intent(args.config)

    # Run verification internally to guarantee freshness.
    vr_ctx = VerificationContext(
        release_dir=args.release_dir,
        kernel_release=args.kernel_release,
        driver_version=intent.nvidia_version,
        secure_boot_state=SecureBootState.UNKNOWN,
    )
    verification = ReleaseVerifier(_make_runner()).verify_release(vr_ctx)
    if not verification.boot_ready or verification.has_errors():
        return CliResult(
            subcommand="release",
            status="error",
            exit_code=int(ExitCode.BUILD_FAILURE),
            message="Verification failed; release not assembled.",
            payload={"boot_ready": verification.boot_ready},
            findings=tuple(f.to_dict() for f in verification.findings),
        )

    ctx = ReleaseContext(
        release_dir=args.release_dir,
        kernel_release=args.kernel_release,
        driver_version=intent.nvidia_version,
        profile=intent.profile,
        verification=verification,
        kernel_image_deb=args.kernel_image_deb,
        kernel_headers_deb=args.kernel_headers_deb,
        nvidia_modules_dir=args.nvidia_modules_dir,
        initramfs=args.initramfs,
        config_path=args.config_path,
        source_lock_path=args.source_lock_path,
        rollback_notes=args.rollback_notes,
    )
    result = ReleaseAssembler().build_release(
        ctx, force=args.force, dry_run=args.dry_run
    )
    payload = {
        "release_dir": str(result.release_dir) if result.release_dir else None,
        "manifest_path": str(result.manifest_path) if result.manifest_path else None,
        "checksums_path": str(result.checksums_path) if result.checksums_path else None,
        "artifacts_count": len(result.artifacts),
        "distribution_restricted": result.distribution_restricted,
        "dry_run": result.dry_run,
    }
    if result.has_errors():
        return _component_error(
            subcommand="release", findings=result.findings, payload=payload,
        )
    return CliResult(
        subcommand="release",
        status="dry_run" if result.dry_run else "ok",
        exit_code=int(ExitCode.SUCCESS),
        message=(
            f"release ready at {result.release_dir}"
            if result.release_dir
            else "dry run planned"
        ),
        payload=payload,
        findings=tuple(f.to_dict() for f in result.findings),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _component_error(
    *,
    subcommand: str,
    findings: Sequence[ValidationFinding],
    payload: dict[str, Any],
) -> CliResult:
    """Return a CliResult for a component that reported ERROR/CRITICAL findings."""
    return CliResult(
        subcommand=subcommand,
        status="error",
        exit_code=int(ExitCode.BUILD_FAILURE),
        message=f"{len(findings)} finding(s); see details",
        payload=payload,
        findings=tuple(f.to_dict() for f in findings),
    )


def _sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _infer_kernel_release(release_dir: Path) -> str:
    """Best-effort inference of kernel_release from release_dir contents."""
    import re

    for deb in release_dir.rglob("linux-image-*.deb"):
        m = re.match(r"linux-image-(.+?)_", deb.name)
        if m:
            return m.group(1)
    raise CliError(
        ExitCode.MISSING_PREREQUISITES,
        "Could not infer kernel_release from release_dir; pass "
        "--kernel-release explicitly.",
    )


def _infer_driver_version(release_dir: Path) -> str:
    """Best-effort inference of driver_version from nvidia-*-<kr>/ dirs."""
    import re

    for candidate in release_dir.glob("nvidia-*-*"):
        if candidate.is_dir():
            m = re.match(r"nvidia-([0-9][0-9A-Za-z.\-]*?)-", candidate.name)
            if m:
                return m.group(1)
    raise CliError(
        ExitCode.MISSING_PREREQUISITES,
        "Could not infer driver_version from release_dir; pass "
        "--driver-version explicitly.",
    )


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="huey-kernel",
        description=(
            "HueyOS custom kernel builder. Read-only subcommands never mutate "
            "host state; build subcommands write only to caller-supplied paths."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="subcommand", required=True, metavar="SUBCOMMAND")

    # ---- read-only --------------------------------------------------
    p = sub.add_parser("inventory", help="Read-only host snapshot")
    p.add_argument("--json", action="store_true", help="Machine-readable output")
    p.set_defaults(func=_cmd_inventory)

    p = sub.add_parser("doctor", help="Diagnose environment and suggest next steps")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_doctor)

    p = sub.add_parser("plan", help="Print the build plan")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--with-inventory",
        action="store_true",
        help="Run inventory probes to make the plan check GPU and Secure Boot",
    )
    p.set_defaults(func=_cmd_plan)

    p = sub.add_parser("verify", help="Offline verification of a release dir")
    p.add_argument("--release-dir", type=Path, required=True)
    p.add_argument("--kernel-release", type=str, default=None)
    p.add_argument("--driver-version", type=str, default=None)
    p.add_argument(
        "--secure-boot-state",
        type=lambda s: SecureBootState(s.lower()),
        default=SecureBootState.UNKNOWN,
        choices=[s.value for s in SecureBootState],
    )
    p.add_argument("--verify-dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_verify)

    # ---- build ------------------------------------------------------
    p = sub.add_parser("config", help="Build the effective .config")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--base-config", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument(
        "--fragment",
        type=Path,
        action="append",
        default=[],
        help="Repeatable; later fragments win over earlier ones",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_config)

    p = sub.add_parser("build-kernel", help="Build kernel image+headers .debs")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--source-dir", type=Path, required=True)
    p.add_argument("--effective-config", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--jobs", type=int, default=None)
    p.add_argument("--localversion", default=None)
    p.add_argument(
        "--source-date-epoch", type=int, default=0,
        help="Reproducible-build timestamp (default 0 = Unix epoch)",
    )
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_build_kernel)

    p = sub.add_parser("build-nvidia", help="Build NVIDIA modules for a target release")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--kernel-release", type=str, required=True)
    p.add_argument("--headers-dir", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--dkms-source-dir", type=Path, default=None)
    p.add_argument("--allow-system-dkms-discovery", action="store_true")
    p.add_argument("--secure-boot-enabled", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_build_nvidia)

    p = sub.add_parser("initramfs", help="Build a target-version initramfs")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--kernel-release", type=str, required=True)
    p.add_argument("--module-tree", type=Path, required=True)
    p.add_argument("--modules-list", type=Path, required=True)
    p.add_argument("--modprobe-conf", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--no-modprobe-hook", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_initramfs)

    p = sub.add_parser("sign", help="Sign staged modules with a MOK certificate")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--modules-dir", type=Path, required=True)
    p.add_argument("--headers-dir", type=Path, required=True)
    p.add_argument("--key", type=Path, required=True)
    p.add_argument("--cert", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--kernel-release", type=str, default=None)
    p.add_argument("--pin-env-var", type=str, default="KBUILD_SIGN_PIN")
    p.add_argument(
        "--use-env-pin",
        action="store_true",
        help="Read the passphrase from $<pin-env-var> instead of prompting",
    )
    p.add_argument("--detect-secure-boot", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_sign)

    p = sub.add_parser("release", help="Assemble a validated release directory")
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--release-dir", type=Path, required=True)
    p.add_argument("--kernel-release", type=str, required=True)
    p.add_argument("--kernel-image-deb", type=Path, required=True)
    p.add_argument("--kernel-headers-deb", type=Path, required=True)
    p.add_argument("--nvidia-modules-dir", type=Path, default=None)
    p.add_argument("--initramfs", type=Path, default=None)
    p.add_argument("--config-path", type=Path, default=None)
    p.add_argument("--source-lock-path", type=Path, default=None)
    p.add_argument("--rollback-notes", type=str, default=None)
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_release)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    """Parse argv, dispatch, print, and return the exit code."""
    parser = _build_parser()
    try:
        args = parser.parse_args()
    except SystemExit as exc:
        # argparse --help -> 0; parse errors -> 2.
        return int(exc.code) if exc.code is not None else 0

    try:
        result = args.func(args)
    except CliError as exc:
        result = CliResult(
            subcommand=args.subcommand,
            status="error",
            exit_code=int(exc.code),
            message=exc.message,
            payload={"error": exc.message},
            findings=(),
        )
    except Exception as exc:  # noqa: BLE001 - CLI must never leak a raw trace
        traceback.print_exc()
        result = CliResult(
            subcommand=args.subcommand,
            status="error",
            exit_code=int(ExitCode.BUILD_FAILURE),
            message=f"internal error: {exc}",
            payload={"error": str(exc)},
            findings=(),
        )

    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    else:
        print(result.to_text())
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
