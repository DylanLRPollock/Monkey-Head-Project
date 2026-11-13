"""Adversarial tests for huey.kernel_build.policy (Step 5; Step 34 expands)."""

from __future__ import annotations

from pathlib import Path

import pytest

from huey.kernel_build.models import (
    ApprovalState,
    ArtifactKind,
    DriverBaseline,
    GPUIdentity,
    GPUVendor,
    KernelPlan,
    KernelSource,
    ModuleFlavor,
    Severity,
    SigningPolicy,
    SourceType,
)
from huey.kernel_build.policy import (
    ApprovalRequiredError,
    OperationKind,
    POLICY_V100_WORKSTATION,
    PolicyViolation,
    PROTECTED_HOST_PATHS,
    SecureBootState,
    VOLTA_COMPUTE_CAPABILITY,
    assert_allowed,
    check_cuda_compatibility_claim,
    check_kernel_release,
    check_module_flavor_for_volta,
    check_path_destination_safe,
    check_signing_readiness,
    check_source_resolved,
    check_url,
    evaluate_build_plan,
    evaluate_operation,
    redact_path,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _sha(c: str = "a") -> str:
    return c * 64


def _source_resolved() -> KernelSource:
    return KernelSource(
        source_type=SourceType.DEBIAN_LINUX_SOURCE,
        source="linux-source-7.2",
        version="7.2.15-1",
        checksum=_sha("b"),
    )


def _v100() -> GPUIdentity:
    return GPUIdentity(
        vendor=GPUVendor.NVIDIA,
        model="Tesla V100-PCIE-32GB",
        pci_address="00000000:01:00.0",
        compute_capability=VOLTA_COMPUTE_CAPABILITY,
    )


def _rx570() -> GPUIdentity:
    return GPUIdentity(
        vendor=GPUVendor.AMD,
        model="Radeon RX 570",
        pci_address="00000000:02:00.0",
    )


def _driver_proprietary() -> DriverBaseline:
    return DriverBaseline(
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        cuda_api_version="13.0",
        cuda_toolkit_version="12.9",
        dkms_builds=("7.2.15+deb14-amd64",),
    )


def _driver_open() -> DriverBaseline:
    return DriverBaseline(
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.OPEN,
    )


def _plan(
    *,
    driver: DriverBaseline | None = None,
    workspace: Path = Path("build/huey-kernel/workspace"),
    output_dir: Path = Path("build/huey-kernel/"),
    profile: str = POLICY_V100_WORKSTATION,
    signing_policy: SigningPolicy = SigningPolicy.REQUIRED_IF_SECUREBOOT,
) -> KernelPlan:
    return KernelPlan(
        profile=profile,
        source=_source_resolved(),
        driver=driver or _driver_proprietary(),
        workspace=workspace,
        output_dir=output_dir,
        build_jobs=4,
        signing_policy=signing_policy,
        target_release="7.2.15-huey1",
        intended_artifacts=(
            ArtifactKind.KERNEL_IMAGE_DEB,
            ArtifactKind.KERNEL_HEADERS_DEB,
            ArtifactKind.NVIDIA_MODULE,
        ),
    )


def _codes(findings) -> set[str]:
    return {f.code for f in findings}


def _has_severity(findings, severity: Severity) -> bool:
    return any(f.severity == severity for f in findings)


# ---------------------------------------------------------------------------
# check_source_resolved
# ---------------------------------------------------------------------------


def test_check_source_resolved_passes_when_pinned() -> None:
    assert check_source_resolved(_source_resolved()) == []


def test_check_source_resolved_rejects_unresolved() -> None:
    src = KernelSource(source_type=SourceType.DEBIAN_LINUX_SOURCE)
    findings = check_source_resolved(src)
    assert _codes(findings) == {"SOURCE_UNRESOLVED"}
    assert findings[0].severity == Severity.ERROR
    assert set(findings[0].context["missing"]) == {"source", "version", "checksum"}


def test_check_source_resolved_partial_pinning_still_fails() -> None:
    src = KernelSource(
        source_type=SourceType.DEBIAN_LINUX_SOURCE,
        source="linux-source-7.2",
        version="7.2.15-1",
        checksum=None,
    )
    findings = check_source_resolved(src)
    assert "SOURCE_UNRESOLVED" in _codes(findings)
    assert findings[0].context["missing"] == ["checksum"]


# ---------------------------------------------------------------------------
# check_module_flavor_for_volta
# ---------------------------------------------------------------------------


def test_module_flavor_proprietary_for_v100_is_accepted() -> None:
    findings = check_module_flavor_for_volta(
        _driver_proprietary(), [_v100(), _rx570()], profile=POLICY_V100_WORKSTATION
    )
    assert findings == []


def test_module_flavor_open_for_v100_is_critical() -> None:
    findings = check_module_flavor_for_volta(
        _driver_open(), [_v100(), _rx570()], profile=POLICY_V100_WORKSTATION
    )
    assert "OPEN_MODULE_FOR_VOLTA" in _codes(findings)
    assert findings[0].severity == Severity.CRITICAL
    assert findings[0].context["module_flavor"] == "open"


def test_module_flavor_open_ignored_without_volta_or_profile() -> None:
    """No V100 in identities, profile is not v100-workstation -> no finding."""
    findings = check_module_flavor_for_volta(
        _driver_open(), [_rx570()], profile="lab"
    )
    assert findings == []


def test_module_flavor_open_rejected_by_profile_even_without_enumeration() -> None:
    """Defensive: profile 'v100-workstation' implies Volta even if gpu list empty."""
    findings = check_module_flavor_for_volta(
        _driver_open(), [], profile=POLICY_V100_WORKSTATION
    )
    assert "OPEN_MODULE_FOR_VOLTA" in _codes(findings)


# ---------------------------------------------------------------------------
# check_kernel_release
# ---------------------------------------------------------------------------


def test_kernel_release_match_is_ok() -> None:
    assert check_kernel_release("7.2.15-huey1", "7.2.15-huey1") == []


def test_kernel_release_mismatch_is_error() -> None:
    findings = check_kernel_release("7.2.15-huey1", "7.2.12+deb14-amd64")
    assert _codes(findings) == {"KERNEL_RELEASE_MISMATCH"}
    assert findings[0].severity == Severity.ERROR
    assert findings[0].context == {
        "expected": "7.2.15-huey1",
        "actual": "7.2.12+deb14-amd64",
    }


def test_kernel_release_missing_expected() -> None:
    findings = check_kernel_release(None, "7.2.15-huey1")
    assert "EXPECTED_RELEASE_MISSING" in _codes(findings)
    assert findings[0].severity == Severity.ERROR


def test_kernel_release_missing_actual() -> None:
    findings = check_kernel_release("7.2.15-huey1", None)
    assert "ACTUAL_RELEASE_MISSING" in _codes(findings)


# ---------------------------------------------------------------------------
# check_path_destination_safe
# ---------------------------------------------------------------------------


def test_path_inside_workspace_is_ok(tmp_path: Path) -> None:
    findings = check_path_destination_safe(
        tmp_path / "build" / "huey-kernel" / "out.deb",
        workspace_root=tmp_path / "build" / "huey-kernel",
    )
    assert findings == []


def test_path_escape_dotdot_is_blocked(tmp_path: Path) -> None:
    """`../../` destination escapes the workspace root -> ERROR."""
    ws = tmp_path / "build" / "huey-kernel"
    ws.mkdir(parents=True)
    destination = ws / ".." / ".." / "etc" / "passwd"
    findings = check_path_destination_safe(destination, workspace_root=ws)
    assert "PATH_ESCAPES_WORKSPACE" in _codes(findings)
    assert any(f.severity == Severity.ERROR for f in findings)


def test_boot_write_is_critical(tmp_path: Path) -> None:
    """Even with no workspace root, /boot/* is rejected as CRITICAL."""
    findings = check_path_destination_safe("/boot/vmlinuz-huey-test")
    assert "PROTECTED_HOST_PATH" in _codes(findings)
    assert any(f.severity == Severity.CRITICAL for f in findings)


@pytest.mark.parametrize("protected", PROTECTED_HOST_PATHS)
def test_every_protected_host_path_is_blocked(protected: str) -> None:
    findings = check_path_destination_safe(f"{protected.rstrip('/')}/huey-test")
    assert "PROTECTED_HOST_PATH" in _codes(findings)


def test_protected_paths_override_for_tests(tmp_path: Path) -> None:
    """Callers can supply their own protected roots (used for testing)."""
    fake_etc = tmp_path / "etc"
    fake_etc.mkdir()
    findings = check_path_destination_safe(
        fake_etc / "passwd",
        protected_paths=(str(fake_etc),),
    )
    assert "PROTECTED_HOST_PATH" in _codes(findings)


def test_symlink_into_protected_path_is_blocked(tmp_path: Path) -> None:
    """A symlink whose target lies under a protected path is rejected."""
    fake_protected = tmp_path / "protected"
    fake_protected.mkdir()
    link = tmp_path / "link-to-protected"
    link.symlink_to(fake_protected)
    findings = check_path_destination_safe(
        link / "child",
        protected_paths=(str(fake_protected),),
    )
    assert "PROTECTED_HOST_PATH" in _codes(findings)


# ---------------------------------------------------------------------------
# check_url
# ---------------------------------------------------------------------------


def test_trusted_https_url_is_ok() -> None:
    assert check_url("https://deb.debian.org/debian/pool/main/l/linux/linux.orig.tar.xz") == []


def test_http_url_is_rejected() -> None:
    findings = check_url("http://deb.debian.org/debian/pool/main/l/linux/linux.orig.tar.xz")
    assert "URL_SCHEME_NOT_TRUSTED" in _codes(findings)


def test_file_url_is_rejected() -> None:
    findings = check_url("file:///tmp/linux.tar.xz")
    assert "URL_SCHEME_NOT_TRUSTED" in _codes(findings)


def test_untrusted_host_is_rejected() -> None:
    findings = check_url("https://example.com/linux.tar.xz")
    assert "URL_HOST_NOT_TRUSTED" in _codes(findings)


# ---------------------------------------------------------------------------
# check_signing_readiness
# ---------------------------------------------------------------------------


def test_signing_not_required_when_secureboot_off() -> None:
    plan = _plan()
    findings = check_signing_readiness(
        plan,
        secure_boot_state=SecureBootState.DISABLED,
        key_present=False,
        cert_present=False,
    )
    assert findings == []


def test_signing_required_when_secureboot_enabled() -> None:
    plan = _plan()
    findings = check_signing_readiness(
        plan,
        secure_boot_state=SecureBootState.ENABLED,
        key_present=False,
        cert_present=False,
    )
    codes = _codes(findings)
    assert "SIGNING_KEY_MISSING" in codes
    assert "SIGNING_CERT_MISSING" in codes


def test_signing_ready_when_keys_present_and_secureboot_enabled() -> None:
    plan = _plan()
    assert (
        check_signing_readiness(
            plan,
            secure_boot_state=SecureBootState.ENABLED,
            key_present=True,
            cert_present=True,
        )
        == []
    )


def test_signing_forced_by_policy_required_regardless_of_secureboot() -> None:
    plan = _plan(signing_policy=SigningPolicy.REQUIRED)
    findings = check_signing_readiness(
        plan,
        secure_boot_state=SecureBootState.DISABLED,
        key_present=False,
        cert_present=False,
    )
    assert "SIGNING_KEY_MISSING" in _codes(findings)


def test_secureboot_unknown_yields_warning() -> None:
    plan = _plan()
    findings = check_signing_readiness(
        plan,
        secure_boot_state=SecureBootState.UNKNOWN,
        key_present=False,
        cert_present=False,
    )
    assert "SECUREBOOT_STATE_UNKNOWN" in _codes(findings)
    assert findings[0].severity == Severity.WARNING


# ---------------------------------------------------------------------------
# check_cuda_compatibility_claim
# ---------------------------------------------------------------------------


def test_cuda_claim_ok_when_no_toolkit_claimed() -> None:
    assert check_cuda_compatibility_claim(installed_toolkit=None) == []


def test_cuda_claim_with_verification_source_is_ok() -> None:
    assert (
        check_cuda_compatibility_claim(
            installed_toolkit="12.9",
            verified_toolkit_via="nvcc --version",
        )
        == []
    )


def test_cuda_claim_without_verification_is_error() -> None:
    findings = check_cuda_compatibility_claim(installed_toolkit="13.0")
    assert "CUDA_TOOLKIT_UNVERIFIED" in _codes(findings)
    assert findings[0].severity == Severity.ERROR


# ---------------------------------------------------------------------------
# evaluate_operation
# ---------------------------------------------------------------------------


def test_read_only_operation_is_allowed() -> None:
    decision = evaluate_operation(OperationKind.READ_ONLY)
    assert decision.allowed is True
    assert decision.requires_approval is False
    assert "READ_ONLY_OPERATION" in _codes(decision.findings)


def test_staging_operation_is_allowed() -> None:
    decision = evaluate_operation(OperationKind.STAGING)
    assert decision.allowed is True
    assert "STAGING_OPERATION" in _codes(decision.findings)


def test_privileged_install_fails_closed_by_default() -> None:
    """Absent explicit approval, install must NOT be allowed."""
    decision = evaluate_operation(OperationKind.PRIVILEGED_INSTALL)
    assert decision.allowed is False
    assert decision.requires_approval is True
    assert "APPROVAL_REQUIRED" in _codes(decision.violations)


def test_privileged_install_allowed_after_explicit_approval() -> None:
    decision = evaluate_operation(
        OperationKind.PRIVILEGED_INSTALL,
        approval_state=ApprovalState.APPROVED,
    )
    assert decision.allowed is True
    assert decision.requires_approval is True
    assert decision.violations == ()


def test_privileged_install_with_secureboot_warns_signing_required() -> None:
    decision = evaluate_operation(
        OperationKind.PRIVILEGED_INSTALL,
        approval_state=ApprovalState.APPROVED,
        secure_boot_state=SecureBootState.ENABLED,
        signing_required=True,
    )
    assert "SECUREBOOT_SIGNING_REQUIRED" in _codes(decision.findings)


# ---------------------------------------------------------------------------
# evaluate_build_plan — full pipeline
# ---------------------------------------------------------------------------


def test_good_v100_plan_is_allowed(tmp_path: Path) -> None:
    plan = _plan()
    decision = evaluate_build_plan(
        plan,
        gpu_identities=[_v100(), _rx570()],
        secure_boot_state=SecureBootState.DISABLED,
        cwd=tmp_path,
    )
    assert decision.allowed is True, decision.violations
    assert decision.violations == ()
    # No V100 warning when V100 present
    assert "EXPECTED_V100_NOT_FOUND" not in _codes(decision.findings)


def test_plan_with_host_mutation_flag_is_rejected(tmp_path: Path) -> None:
    decision = evaluate_build_plan(
        _plan(),
        allow_host_mutation=True,
        gpu_identities=[_v100()],
        cwd=tmp_path,
    )
    assert decision.allowed is False
    assert "HOST_MUTATION_NOT_ALLOWED" in _codes(decision.violations)


def test_plan_with_root_build_flag_is_rejected(tmp_path: Path) -> None:
    decision = evaluate_build_plan(
        _plan(),
        allow_root_build=True,
        gpu_identities=[_v100()],
        cwd=tmp_path,
    )
    assert decision.allowed is False
    assert "ROOT_BUILD_NOT_ALLOWED" in _codes(decision.violations)


def test_plan_with_unresolved_source_is_rejected(tmp_path: Path) -> None:
    plan = KernelPlan(
        profile=POLICY_V100_WORKSTATION,
        source=KernelSource(source_type=SourceType.DEBIAN_LINUX_SOURCE),
        driver=_driver_proprietary(),
        workspace=Path("build/huey-kernel/workspace"),
        output_dir=Path("build/huey-kernel/"),
        build_jobs=4,
    )
    decision = evaluate_build_plan(
        plan, gpu_identities=[_v100()], cwd=tmp_path
    )
    assert decision.allowed is False
    assert "SOURCE_UNRESOLVED" in _codes(decision.violations)


def test_plan_with_open_flavor_for_v100_is_rejected(tmp_path: Path) -> None:
    plan = _plan(driver=_driver_open())
    decision = evaluate_build_plan(
        plan, gpu_identities=[_v100()], cwd=tmp_path
    )
    assert decision.allowed is False
    assert "OPEN_MODULE_FOR_VOLTA" in _codes(decision.violations)
    assert any(
        v.severity == Severity.CRITICAL for v in decision.violations
    )


def test_plan_with_workspace_escaping_cwd_is_rejected(tmp_path: Path) -> None:
    """A workspace that resolves outside the caller's cwd is rejected."""
    plan = _plan(
        workspace=Path("build/huey-kernel/workspace"),
        output_dir=Path("build/huey-kernel/"),
    )
    # Simulate a workspace subdirectory that resolves outside the safe root.
    other_cwd = tmp_path / "other-cwd"
    other_cwd.mkdir()
    (other_cwd / "build").symlink_to(tmp_path)
    decision = evaluate_build_plan(
        plan,
        gpu_identities=[_v100()],
        cwd=other_cwd,
    )
    assert decision.allowed is False
    assert "PATH_ESCAPES_WORKSPACE" in _codes(decision.violations)


def test_plan_with_protected_output_dir_is_critical(tmp_path: Path) -> None:
    # Model rejects absolute build destinations before policy evaluation.
    with pytest.raises(ValueError, match="relative"):
        _plan(output_dir=Path("/boot/huey"))
    # Symlink resolution is still enforced independently at the policy layer.
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "huey-kernel").symlink_to("/boot")
    decision = evaluate_build_plan(
        _plan(), gpu_identities=[_v100()], cwd=tmp_path
    )
    assert decision.allowed is False
    assert "PROTECTED_HOST_PATH" in _codes(decision.violations)


def test_plan_under_secureboot_without_keys_is_rejected(tmp_path: Path) -> None:
    decision = evaluate_build_plan(
        _plan(),
        gpu_identities=[_v100()],
        secure_boot_state=SecureBootState.ENABLED,
        key_present=False,
        cert_present=False,
        cwd=tmp_path,
    )
    assert decision.allowed is False
    codes = _codes(decision.violations)
    assert {"SIGNING_KEY_MISSING", "SIGNING_CERT_MISSING"} <= codes


def test_plan_with_verified_toolkit_and_no_api_claim_is_warned_not_blocked(
    tmp_path: Path,
) -> None:
    """Installed toolkit with verification source: no block, no warning."""
    decision = evaluate_build_plan(
        _plan(),
        gpu_identities=[_v100()],
        installed_toolkit="12.9",
        verified_toolkit_via="nvcc --version",
        cwd=tmp_path,
    )
    assert decision.allowed is True


def test_plan_with_unverified_toolkit_claim_is_rejected(tmp_path: Path) -> None:
    decision = evaluate_build_plan(
        _plan(),
        gpu_identities=[_v100()],
        installed_toolkit="13.0",
        # no verified_toolkit_via
        cwd=tmp_path,
    )
    assert decision.allowed is False
    assert "CUDA_TOOLKIT_UNVERIFIED" in _codes(decision.violations)


def test_plan_without_v100_identity_warns_expected_v100_not_found(
    tmp_path: Path,
) -> None:
    decision = evaluate_build_plan(
        _plan(),
        gpu_identities=[_rx570()],
        cwd=tmp_path,
    )
    # Still allowed, but the warning is recorded.
    assert decision.allowed is True
    assert "EXPECTED_V100_NOT_FOUND" in _codes(decision.findings)


# ---------------------------------------------------------------------------
# assert_allowed
# ---------------------------------------------------------------------------


def test_assert_allowed_passes_on_ok() -> None:
    decision = evaluate_operation(OperationKind.READ_ONLY)
    assert_allowed(decision)  # should not raise


def test_assert_allowed_raises_approval_required_for_install() -> None:
    decision = evaluate_operation(OperationKind.PRIVILEGED_INSTALL)
    with pytest.raises(ApprovalRequiredError) as excinfo:
        assert_allowed(decision)
    assert isinstance(excinfo.value, PolicyViolation)
    assert "APPROVAL_REQUIRED" in excinfo.value.decision.blocking_codes


def test_assert_allowed_raises_policy_violation_for_plan(tmp_path: Path) -> None:
    decision = evaluate_build_plan(
        _plan(),
        allow_host_mutation=True,
        gpu_identities=[_v100()],
        cwd=tmp_path,
    )
    with pytest.raises(PolicyViolation):
        assert_allowed(decision)


# ---------------------------------------------------------------------------
# redact_path and PolicyDecision invariants
# ---------------------------------------------------------------------------


def test_redact_path_replaces_home_prefix() -> None:
    home = Path.home()
    assert redact_path(home / "projects" / "x") == "~/projects/x"
    assert redact_path(home) == "~"


def test_redact_path_leaves_absolute_outside_home_alone() -> None:
    assert redact_path("/boot/vmlinuz") == "/boot/vmlinuz"


def test_decision_forced_disallowed_when_violations_present() -> None:
    """PolicyDecision.__post_init__ enforces the fail-closed invariant."""
    from huey.kernel_build.models import ValidationFinding

    v = ValidationFinding(severity=Severity.ERROR, code="X", message="x")
    from huey.kernel_build.policy import PolicyDecision

    decision = PolicyDecision(allowed=True, requires_approval=False, violations=(v,))
    assert decision.allowed is False
