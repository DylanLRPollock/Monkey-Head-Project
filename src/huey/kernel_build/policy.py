"""Central risk gates for the HueyOS kernel build framework.

Every destructive-adjacent decision the framework makes flows through this
module. It consumes the immutable models from :mod:`huey.kernel_build.models`
and returns :class:`PolicyDecision` values.

Design rules
------------
* **Fail closed.** Any blocking finding (``ERROR`` or ``CRITICAL``) forces
  ``allowed=False``. Approval-required operations default to ``allowed=False``
  until the caller supplies ``ApprovalState.APPROVED`` explicitly.
* **No host mutation by construction.** Destination paths that resolve into a
  protected host path (``/boot``, ``/lib/modules``, ``/etc``, ``/var/lib/dkms``,
  ``/sys``, ``/proc``, ``/dev``, …) are rejected as ``CRITICAL`` findings.
* **V100 requires the proprietary module flavor.** Volta (``sm_70``) is not
  supported by the NVIDIA open GPU kernel modules. Profiles that target
  ``v100-workstation`` are rejected if the driver baseline is ``open``.
* **`nvidia-smi`'s advertised CUDA API is not proof of an installed toolkit.**
  A claimed toolkit version must record how it was verified; otherwise it is
  rejected.
* **Exact kernel-release matching** is required for module and initramfs
  artifacts; missing or mismatched values block promotion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Sequence
from urllib.parse import urlparse

from huey.kernel_build.models import (
    ApprovalState,
    DriverBaseline,
    GPUIdentity,
    GPUVendor,
    KernelPlan,
    KernelSource,
    ModuleFlavor,
    Severity,
    SigningPolicy,
    ValidationFinding,
)

__all__ = [
    "ApprovalRequiredError",
    "OperationKind",
    "POLICY_V100_WORKSTATION",
    "PolicyDecision",
    "PolicyViolation",
    "PROTECTED_HOST_PATHS",
    "SecureBootState",
    "TRUSTED_SOURCE_HOSTS",
    "VOLTA_COMPUTE_CAPABILITY",
    "assert_allowed",
    "check_cuda_compatibility_claim",
    "check_kernel_release",
    "check_module_flavor_for_volta",
    "check_path_destination_safe",
    "check_signing_readiness",
    "check_source_resolved",
    "check_url",
    "evaluate_build_plan",
    "evaluate_operation",
]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

POLICY_V100_WORKSTATION = "v100-workstation"
VOLTA_COMPUTE_CAPABILITY = "sm_70"

# The framework never writes into these host locations during
# build/config/staging/verify. Install is a separate operation and is gated
# by :func:`evaluate_operation` with :data:`OperationKind.PRIVILEGED_INSTALL`.
PROTECTED_HOST_PATHS: tuple[str, ...] = (
    "/boot",
    "/lib/modules",
    "/lib/firmware",
    "/etc",
    "/usr/lib/modules",
    "/usr/lib/firmware",
    "/sys",
    "/proc",
    "/dev",
    "/var/lib/dkms",
    "/var/lib/apt",
    "/var/lib/dpkg",
)

# Trusted origins for kernel source. Case-insensitive exact host match.
TRUSTED_SOURCE_HOSTS: frozenset[str] = frozenset(
    {
        "deb.debian.org",
        "security.debian.org",
        "ftp.debian.org",
        "snapshot.debian.org",
        "kernel.org",
        "cdn.kernel.org",
    }
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SecureBootState(StrEnum):
    """Observed Secure Boot state. ``UNKNOWN`` is not treated as ``DISABLED``."""

    DISABLED = "disabled"
    ENABLED = "enabled"
    UNKNOWN = "unknown"


class OperationKind(StrEnum):
    """Distinguishes read-only inspection, staging, and privileged install."""

    READ_ONLY = "read_only"
    STAGING = "staging"
    PRIVILEGED_INSTALL = "privileged_install"


# ---------------------------------------------------------------------------
# Decision result
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Aggregate result of a policy evaluation.

    ``violations`` are always blocking findings (``ERROR`` or ``CRITICAL``).
    ``findings`` are non-blocking (``WARNING`` or ``INFO``).

    Invariant: ``allowed`` is ``False`` whenever ``violations`` is non-empty.
    ``requires_approval`` is ``True`` for privileged operations even when
    ``allowed`` is ``True`` (approval was granted).
    """

    allowed: bool
    requires_approval: bool
    violations: tuple[ValidationFinding, ...] = ()
    findings: tuple[ValidationFinding, ...] = ()

    def __post_init__(self) -> None:
        for name in ("violations", "findings"):
            value = getattr(self, name)
            if isinstance(value, list):
                object.__setattr__(self, name, tuple(value))
            if not isinstance(getattr(self, name), tuple):
                raise TypeError(f"PolicyDecision.{name} must be a tuple")
        if self.violations and self.allowed:
            object.__setattr__(self, "allowed", False)

    @property
    def blocking_codes(self) -> tuple[str, ...]:
        return tuple(v.code for v in self.violations)


class PolicyViolation(Exception):
    """Raised by :func:`assert_allowed` when a decision blocks execution."""

    def __init__(self, decision: PolicyDecision) -> None:
        self.decision = decision
        detail = "; ".join(v.message for v in decision.violations) or "no detail"
        super().__init__(f"policy violation(s): {detail}")


class ApprovalRequiredError(PolicyViolation):
    """Raised when an operation requires approval that has not been granted."""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_blocking(finding: ValidationFinding) -> bool:
    return finding.severity in (Severity.ERROR, Severity.CRITICAL)


def _make_decision(
    violations: list[ValidationFinding],
    findings: list[ValidationFinding],
    *,
    requires_approval: bool,
) -> PolicyDecision:
    blocking = any(_is_blocking(v) for v in violations)
    return PolicyDecision(
        allowed=not blocking and not requires_approval,
        requires_approval=requires_approval,
        violations=tuple(violations),
        findings=tuple(findings),
    )


def redact_path(path: str | Path) -> str:
    """Return a path string with the user's home directory prefix elided."""
    p = Path(path)
    try:
        home = Path.home()
    except (RuntimeError, OSError):
        return str(p)
    try:
        rel = p.relative_to(home)
    except ValueError:
        return str(p)
    rel_str = str(rel)
    return "~" if rel_str == "." else f"~/{rel_str}"


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_source_resolved(source: KernelSource) -> list[ValidationFinding]:
    """Return a blocking finding if the kernel source is not fully pinned."""
    if source.is_resolved:
        return []
    missing = [
        name
        for name in ("source", "version", "checksum")
        if getattr(source, name) in (None, "")
    ]
    return [
        ValidationFinding(
            severity=Severity.ERROR,
            code="SOURCE_UNRESOLVED",
            message=(
                "Kernel source is not fully pinned; missing "
                f"{missing}. Resolve via source_manager.py and record the pin "
                "in kernel/huey-linux/source.lock.json before build-kernel."
            ),
            context={"missing": missing},
        )
    ]


def check_module_flavor_for_volta(
    driver: DriverBaseline,
    gpu_identities: Sequence[GPUIdentity],
    *,
    profile: str | None = None,
) -> list[ValidationFinding]:
    """Reject the NVIDIA open module flavor when a Volta GPU is in play.

    The check triggers when either:

    * a GPU with ``vendor == nvidia`` and ``compute_capability == sm_70`` is
      present in ``gpu_identities``, or
    * the plan profile is ``v100-workstation`` (defensive: even if the GPU
      has not been enumerated yet, the profile implies Volta).

    In either case, ``driver.module_flavor`` must be
    :attr:`ModuleFlavor.PROPRIETARY`.
    """
    volta = [
        g
        for g in gpu_identities
        if g.vendor == GPUVendor.NVIDIA
        and g.compute_capability == VOLTA_COMPUTE_CAPABILITY
    ]
    profile_implies_volta = profile == POLICY_V100_WORKSTATION
    if not volta and not profile_implies_volta:
        return []
    if driver.module_flavor == ModuleFlavor.PROPRIETARY:
        return []
    return [
        ValidationFinding(
            severity=Severity.CRITICAL,
            code="OPEN_MODULE_FOR_VOLTA",
            message=(
                "Tesla V100 (Volta, sm_70) requires the proprietary NVIDIA "
                "module flavor; the open GPU kernel modules are not "
                "compatible with Volta. Set nvidia.module_flavor=proprietary."
            ),
            context={
                "driver_version": driver.driver_version,
                "module_flavor": driver.module_flavor.value,
                "profile": profile,
                "volta_gpus": [g.pci_address for g in volta],
            },
        )
    ]


def check_kernel_release(
    expected: str | None,
    actual: str | None,
) -> list[ValidationFinding]:
    """Require exact ``KERNELRELEASE`` matching between plan and artifact."""
    findings: list[ValidationFinding] = []
    if not expected:
        findings.append(
            ValidationFinding(
                severity=Severity.ERROR,
                code="EXPECTED_RELEASE_MISSING",
                message=(
                    "Expected kernel release is missing; the plan must record "
                    "'make -s kernelrelease' before artifacts can be verified."
                ),
            )
        )
    if not actual:
        findings.append(
            ValidationFinding(
                severity=Severity.ERROR,
                code="ACTUAL_RELEASE_MISSING",
                message=(
                    "Actual kernel release is missing from the artifact under "
                    "inspection; modinfo -F vermagic reports nothing usable."
                ),
            )
        )
    if expected and actual and expected != actual:
        findings.append(
            ValidationFinding(
                severity=Severity.ERROR,
                code="KERNEL_RELEASE_MISMATCH",
                message=(
                    f"Kernel release mismatch: expected {expected!r}, "
                    f"got {actual!r}. Modules and initramfs must match the "
                    "target KERNELRELEASE exactly."
                ),
                context={"expected": expected, "actual": actual},
            )
        )
    return findings


def check_path_destination_safe(
    path: str | Path,
    *,
    workspace_root: str | Path | None = None,
    protected_paths: Sequence[str | Path] | None = None,
) -> list[ValidationFinding]:
    """Reject destinations that escape the workspace or land on protected paths.

    The check is symlink-aware in both directions:

    * A destination that *resolves into* a protected path is rejected even if
      the input string does not literally begin with that path.
    * A destination under a path that *resolves to* a protected path (for
      example, if ``/boot`` were a symlink) is also rejected.
    """
    findings: list[ValidationFinding] = []
    p = Path(path)
    if not str(path).strip() or ".." in p.parts or "\x00" in str(p):
        return [ValidationFinding(
            severity=Severity.ERROR,
            code="PATH_ESCAPES_WORKSPACE",
            message=f"Unsafe destination path: {redact_path(p)}",
            context={"path": redact_path(p)},
        )]
    # All relative locations are rooted in the selected workspace, never in
    # the process working directory (which may be unrelated, e.g. under CI).
    base = Path(workspace_root) if workspace_root is not None else Path.cwd()
    candidate_path = p if p.is_absolute() else base / p
    try:
        resolved = candidate_path.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        return [
            ValidationFinding(
                severity=Severity.ERROR,
                code="PATH_UNRESOLVABLE",
                message=f"Could not resolve destination {redact_path(p)}: {exc}",
                context={"path": redact_path(p)},
            )
        ]

    protected = tuple(protected_paths) if protected_paths is not None else PROTECTED_HOST_PATHS
    protected_roots: list[Path] = []
    for entry in protected:
        entry_path = Path(entry)
        protected_roots.append(entry_path)
        try:
            protected_roots.append(entry_path.resolve(strict=False))
        except (OSError, RuntimeError):
            continue

    candidates = (candidate_path, resolved)
    for candidate in candidates:
        for root in protected_roots:
            try:
                candidate.relative_to(root)
            except (ValueError, TypeError):
                continue
            findings.append(
                ValidationFinding(
                    severity=Severity.CRITICAL,
                    code="PROTECTED_HOST_PATH",
                    message=(
                        f"Destination {redact_path(p)} resolves inside "
                        f"protected host path {redact_path(root)}. The "
                        "framework never writes here during build, config, "
                        "staging, or verify."
                    ),
                    context={
                        "path": redact_path(p),
                        "resolved": redact_path(resolved),
                        "protected": redact_path(root),
                    },
                )
            )
            return findings

    if workspace_root is not None:
        try:
            root = Path(workspace_root).resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            return findings + [
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="WORKSPACE_UNRESOLVABLE",
                    message=f"Could not resolve workspace root {workspace_root}: {exc}",
                    context={"workspace": str(workspace_root)},
                )
            ]
        try:
            resolved.relative_to(root)
        except ValueError:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="PATH_ESCAPES_WORKSPACE",
                    message=(
                        f"Destination {redact_path(p)} resolves outside "
                        f"workspace root {redact_path(root)}."
                    ),
                    context={
                        "path": redact_path(p),
                        "resolved": redact_path(resolved),
                        "workspace": redact_path(root),
                    },
                )
            )

    return findings


def check_url(url: str) -> list[ValidationFinding]:
    """Require HTTPS and a trusted source host for kernel source URLs."""
    findings: list[ValidationFinding] = []
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        return [
            ValidationFinding(
                severity=Severity.ERROR,
                code="URL_UNPARSEABLE",
                message=f"Could not parse source URL: {exc}",
                context={"url": url},
            )
        ]
    if parsed.scheme != "https":
        findings.append(
            ValidationFinding(
                severity=Severity.ERROR,
                code="URL_SCHEME_NOT_TRUSTED",
                message=(
                    f"Kernel source URL must use https; got scheme "
                    f"{parsed.scheme!r}. Plain http, ftp, and file origins are "
                    "not trusted for kernel source retrieval."
                ),
                context={"url": url, "scheme": parsed.scheme},
            )
        )
    host = (parsed.hostname or "").lower()
    if host not in TRUSTED_SOURCE_HOSTS:
        findings.append(
            ValidationFinding(
                severity=Severity.ERROR,
                code="URL_HOST_NOT_TRUSTED",
                message=(
                    f"Kernel source URL host {host!r} is not in the trusted "
                    "set. Add it to TRUSTED_SOURCE_HOSTS after review, or "
                    "use an approved offline cache."
                ),
                context={"url": url, "host": host},
            )
        )
    return findings


def check_signing_readiness(
    plan: KernelPlan,
    *,
    secure_boot_state: SecureBootState = SecureBootState.UNKNOWN,
    key_present: bool = False,
    cert_present: bool = False,
) -> list[ValidationFinding]:
    """Require signing key and certificate when the policy or Secure Boot demands it."""
    findings: list[ValidationFinding] = []

    need_signing = False
    reason = ""
    if plan.signing_policy == SigningPolicy.REQUIRED:
        need_signing = True
        reason = "signing.required_policy=required"
    elif (
        plan.signing_policy == SigningPolicy.REQUIRED_IF_SECUREBOOT
        and secure_boot_state == SecureBootState.ENABLED
    ):
        need_signing = True
        reason = (
            "Secure Boot enabled and "
            "signing.required_policy=required_if_secureboot"
        )

    if need_signing:
        if not key_present:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="SIGNING_KEY_MISSING",
                    message=(
                        f"Signing is required ({reason}) but no private key "
                        "was provided. Keys live outside the repository; "
                        "configure signing.key_path in the operator environment."
                    ),
                )
            )
        if not cert_present:
            findings.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="SIGNING_CERT_MISSING",
                    message=(
                        f"Signing is required ({reason}) but no certificate "
                        "was provided. Configure signing.cert_path."
                    ),
                )
            )
    elif secure_boot_state == SecureBootState.UNKNOWN:
        findings.append(
            ValidationFinding(
                severity=Severity.WARNING,
                code="SECUREBOOT_STATE_UNKNOWN",
                message=(
                    "Secure Boot state is unknown. Run 'mokutil --sb-state' "
                    "before promoting any release to boot-ready."
                ),
            )
        )

    return findings


def check_cuda_compatibility_claim(
    *,
    installed_toolkit: str | None = None,
    verified_toolkit_via: str | None = None,
) -> list[ValidationFinding]:
    """Reject compatibility claims derived from ``nvidia-smi`` alone.

    If a caller records an installed CUDA Toolkit version, it must also record
    how that version was verified (for example ``"nvcc --version"``). The
    driver's advertised API version reported by ``nvidia-smi`` is not proof
    that a toolkit of that version is installed, nor that every Volta ``sm_70``
    workload is supported.
    """
    findings: list[ValidationFinding] = []
    if installed_toolkit and not verified_toolkit_via:
        findings.append(
            ValidationFinding(
                severity=Severity.ERROR,
                code="CUDA_TOOLKIT_UNVERIFIED",
                message=(
                    "cuda_toolkit_version is set but no verification source "
                    "is recorded. Verify on the target host with "
                    "'nvcc --version' (or an explicit equivalent) before "
                    "treating this version as installed."
                ),
                context={"installed_toolkit": installed_toolkit},
            )
        )
    return findings


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------


def evaluate_operation(
    kind: OperationKind,
    *,
    approval_state: ApprovalState = ApprovalState.PENDING,
    secure_boot_state: SecureBootState = SecureBootState.UNKNOWN,
    signing_required: bool = False,
) -> PolicyDecision:
    """Decide whether an operation of ``kind`` may proceed.

    * ``READ_ONLY`` and ``STAGING`` are always allowed (staging is bounded to
      the configured output directory by other checks).
    * ``PRIVILEGED_INSTALL`` requires explicit approval and fails closed by
      default. When Secure Boot is enabled and signing is required, an
      informational warning is attached, but the caller must still supply
      ``approval_state=APPROVED`` to proceed.
    """
    violations: list[ValidationFinding] = []
    findings: list[ValidationFinding] = []

    if kind == OperationKind.PRIVILEGED_INSTALL:
        if approval_state != ApprovalState.APPROVED:
            violations.append(
                ValidationFinding(
                    severity=Severity.ERROR,
                    code="APPROVAL_REQUIRED",
                    message=(
                        "Privileged install requires explicit operator "
                        "approval. Pass approval_state=APPROVED only after "
                        "docs/runbooks/huey-kernel-upgrade.md has been "
                        "reviewed and rollback is confirmed."
                    ),
                    context={"approval_state": approval_state.value},
                )
            )
        if secure_boot_state == SecureBootState.ENABLED and signing_required:
            findings.append(
                ValidationFinding(
                    severity=Severity.WARNING,
                    code="SECUREBOOT_SIGNING_REQUIRED",
                    message=(
                        "Secure Boot is enabled. Signed modules and a "
                        "completed MOK enrollment are required before install "
                        "takes effect."
                    ),
                )
            )
    elif kind == OperationKind.READ_ONLY:
        findings.append(
            ValidationFinding(
                severity=Severity.INFO,
                code="READ_ONLY_OPERATION",
                message="Read-only operation; no host mutation is permitted.",
            )
        )
    elif kind == OperationKind.STAGING:
        findings.append(
            ValidationFinding(
                severity=Severity.INFO,
                code="STAGING_OPERATION",
                message=(
                    "Staging writes are permitted under the approved output "
                    "directory only."
                ),
            )
        )

    requires_approval = kind == OperationKind.PRIVILEGED_INSTALL
    blocking = any(_is_blocking(v) for v in violations)
    return PolicyDecision(
        allowed=not blocking and (not requires_approval or approval_state == ApprovalState.APPROVED),
        requires_approval=requires_approval,
        violations=tuple(violations),
        findings=tuple(findings),
    )


def evaluate_build_plan(
    plan: KernelPlan,
    *,
    allow_host_mutation: bool = False,
    allow_root_build: bool = False,
    gpu_identities: Sequence[GPUIdentity] = (),
    secure_boot_state: SecureBootState = SecureBootState.UNKNOWN,
    key_present: bool = False,
    cert_present: bool = False,
    installed_toolkit: str | None = None,
    verified_toolkit_via: str | None = None,
    cwd: Path | None = None,
) -> PolicyDecision:
    """Run all plan-time policy checks and return a consolidated decision.

    The plan is *not* an execution. ``allowed=True`` means the plan is safe to
    submit to ``build-kernel`` / ``build-nvidia`` / ``initramfs``. Installing
    the result onto the host is a separate ``PRIVILEGED_INSTALL`` operation
    that requires explicit human approval.
    """
    violations: list[ValidationFinding] = []
    findings: list[ValidationFinding] = []

    if allow_host_mutation:
        violations.append(
            ValidationFinding(
                severity=Severity.CRITICAL,
                code="HOST_MUTATION_NOT_ALLOWED",
                message=(
                    "allow_host_mutation=true is prohibited by policy. The "
                    "framework refuses to mutate /boot, /lib/modules, /etc, "
                    "apt, DKMS, systemd, MOK, or GRUB from build/config/verify."
                ),
            )
        )
    if allow_root_build:
        violations.append(
            ValidationFinding(
                severity=Severity.CRITICAL,
                code="ROOT_BUILD_NOT_ALLOWED",
                message=(
                    "allow_root_build=true is prohibited by policy. Kernel "
                    "compilation must run as a non-root build user."
                ),
            )
        )

    violations.extend(check_source_resolved(plan.source))
    violations.extend(
        check_module_flavor_for_volta(
            plan.driver, gpu_identities, profile=plan.profile
        )
    )
    for finding in check_signing_readiness(
        plan,
        secure_boot_state=secure_boot_state,
        key_present=key_present,
        cert_present=cert_present,
    ):
        (violations if _is_blocking(finding) else findings).append(finding)

    root = (cwd if cwd is not None else Path.cwd()).resolve(strict=False)
    for destination in (plan.workspace, plan.output_dir):
        for finding in check_path_destination_safe(destination, workspace_root=root):
            (violations if _is_blocking(finding) else findings).append(finding)

    for finding in check_cuda_compatibility_claim(
        installed_toolkit=installed_toolkit,
        verified_toolkit_via=verified_toolkit_via,
    ):
        (violations if _is_blocking(finding) else findings).append(finding)

    if plan.profile == POLICY_V100_WORKSTATION and not any(
        g.vendor == GPUVendor.NVIDIA
        and g.compute_capability == VOLTA_COMPUTE_CAPABILITY
        for g in gpu_identities
    ):
        findings.append(
            ValidationFinding(
                severity=Severity.WARNING,
                code="EXPECTED_V100_NOT_FOUND",
                message=(
                    "Profile 'v100-workstation' was requested but no Tesla "
                    "V100 (sm_70) GPU was identified in the supplied "
                    "identities. Confirm 'lspci -nnk' and 'nvidia-smi -L'."
                ),
            )
        )

    blocking = any(_is_blocking(v) for v in violations)
    return PolicyDecision(
        allowed=not blocking,
        requires_approval=False,
        violations=tuple(violations),
        findings=tuple(findings),
    )


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------


def assert_allowed(decision: PolicyDecision) -> None:
    """Raise :class:`ApprovalRequiredError` or :class:`PolicyViolation` if blocked."""
    if decision.allowed:
        return
    if decision.requires_approval and all(
        v.code == "APPROVAL_REQUIRED" for v in decision.violations
    ):
        raise ApprovalRequiredError(decision)
    raise PolicyViolation(decision)
