"""Tests for huey.kernel_build.models (Step 4; Step 33 will expand)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from huey.kernel_build.models import (
    ApprovalState,
    ArtifactKind,
    BuildArtifact,
    BuildReport,
    BuildStatus,
    CommandResult,
    DriverBaseline,
    GPUIdentity,
    GPUVendor,
    KernelPlan,
    KernelSource,
    ModuleFlavor,
    Severity,
    SigningPolicy,
    SourceType,
    ValidationFinding,
    redact_environment,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _sha(c: str = "a") -> str:
    return c * 64


def _source(**overrides) -> KernelSource:
    base = dict(
        source_type=SourceType.DEBIAN_LINUX_SOURCE,
        source="linux-source-7.2",
        version="7.2.15-1",
        checksum=_sha("b"),
        localversion="-huey1",
        baseline_config=None,
    )
    base.update(overrides)
    return KernelSource(**base)


def _driver(**overrides) -> DriverBaseline:
    base = dict(
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        cuda_api_version="13.0",
        cuda_toolkit_version="12.9",
        dkms_builds=("7.2.12+deb14-amd64", "7.2.15+deb14-amd64"),
    )
    base.update(overrides)
    return DriverBaseline(**base)


def _plan(**overrides) -> KernelPlan:
    base = dict(
        profile="v100-workstation",
        source=_source(),
        driver=_driver(),
        workspace=Path("build/huey-kernel/workspace"),
        output_dir=Path("build/huey-kernel/"),
        build_jobs=4,
        signing_policy=SigningPolicy.REQUIRED_IF_SECUREBOOT,
        target_release="7.2.15-huey1",
        tool_versions={"cc": "gcc-14.2.0", "make": "4.4.1"},
        intended_artifacts=(
            ArtifactKind.KERNEL_IMAGE_DEB,
            ArtifactKind.KERNEL_HEADERS_DEB,
            ArtifactKind.NVIDIA_MODULE,
            ArtifactKind.INITRAMFS,
        ),
    )
    base.update(overrides)
    return KernelPlan(**base)


# ---------------------------------------------------------------------------
# KernelSource
# ---------------------------------------------------------------------------


def test_kernel_source_round_trip() -> None:
    src = _source()
    data = src.to_dict()
    assert json.dumps(data)  # JSON-serializable
    assert KernelSource.from_dict(data) == src


def test_kernel_source_unresolved_state_is_valid() -> None:
    src = KernelSource(source_type=SourceType.DEBIAN_LINUX_SOURCE)
    assert src.is_resolved is False
    assert KernelSource.from_dict(src.to_dict()) == src


def test_kernel_source_rejects_bad_checksum() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        KernelSource(
            source_type=SourceType.DEBIAN_LINUX_SOURCE,
            checksum="not-a-hash",
        )


def test_kernel_source_rejects_uppercase_checksum() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        KernelSource(
            source_type=SourceType.DEBIAN_LINUX_SOURCE,
            checksum="A" * 64,
        )


def test_kernel_source_rejects_unknown_source_type() -> None:
    with pytest.raises(ValueError, match="source_type"):
        KernelSource(source_type="ftp-mirror")  # type: ignore[arg-type]


def test_kernel_source_from_dict_requires_source_type() -> None:
    with pytest.raises(ValueError, match="source_type"):
        KernelSource.from_dict({"source": "x"})


# ---------------------------------------------------------------------------
# GPUIdentity
# ---------------------------------------------------------------------------


def test_gpu_identity_v100_round_trip() -> None:
    gpu = GPUIdentity(
        vendor=GPUVendor.NVIDIA,
        model="Tesla V100-PCIE-32GB",
        pci_address="00000000:01:00.0",
        uuid="GPU-12345678-1234-1234-1234-123456789abc",
        compute_capability="sm_70",
    )
    data = gpu.to_dict()
    assert json.dumps(data)
    assert GPUIdentity.from_dict(data) == gpu


def test_gpu_identity_rx570_round_trip() -> None:
    gpu = GPUIdentity(
        vendor=GPUVendor.AMD,
        model="Radeon RX 570",
        pci_address="00000000:02:00.0",
    )
    assert GPUIdentity.from_dict(gpu.to_dict()) == gpu


def test_gpu_identity_rejects_bad_pci_address() -> None:
    with pytest.raises(ValueError, match="PCI BDF"):
        GPUIdentity(vendor=GPUVendor.NVIDIA, model="X", pci_address="01:00.0")


def test_gpu_identity_rejects_compute_capability_on_amd() -> None:
    with pytest.raises(ValueError, match="NVIDIA"):
        GPUIdentity(
            vendor=GPUVendor.AMD,
            model="RX 570",
            pci_address="00000000:02:00.0",
            compute_capability="sm_70",
        )


def test_gpu_identity_rejects_bad_compute_capability() -> None:
    with pytest.raises(ValueError, match="sm_"):
        GPUIdentity(
            vendor=GPUVendor.NVIDIA,
            model="V100",
            pci_address="00000000:01:00.0",
            compute_capability="70",
        )


# ---------------------------------------------------------------------------
# DriverBaseline -- version distinction
# ---------------------------------------------------------------------------


def test_driver_baseline_keeps_three_versions_distinct() -> None:
    d = _driver()
    assert d.driver_version == "580.196.07"
    assert d.cuda_api_version == "13.0"
    assert d.cuda_toolkit_version == "12.9"
    # All three are distinct values.
    assert len({d.driver_version, d.cuda_api_version, d.cuda_toolkit_version}) == 3


def test_driver_baseline_round_trip_preserves_versions() -> None:
    d = _driver()
    back = DriverBaseline.from_dict(d.to_dict())
    assert back == d
    assert back.cuda_api_version == "13.0"
    assert back.cuda_toolkit_version == "12.9"


def test_driver_baseline_accepts_list_for_dkms_builds() -> None:
    d = DriverBaseline(
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        dkms_builds=["7.2.15+deb14-amd64"],  # type: ignore[arg-type]
    )
    assert isinstance(d.dkms_builds, tuple)
    assert d.dkms_builds == ("7.2.15+deb14-amd64",)


def test_driver_baseline_rejects_unknown_flavor() -> None:
    with pytest.raises(ValueError, match="module_flavor"):
        DriverBaseline(driver_version="580.196.07", module_flavor="hybrid")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# KernelPlan
# ---------------------------------------------------------------------------


def test_kernel_plan_round_trip() -> None:
    p = _plan()
    data = p.to_dict()
    assert json.dumps(data)
    assert KernelPlan.from_dict(data) == p


def test_kernel_plan_rejects_absolute_workspace() -> None:
    with pytest.raises(ValueError, match="relative"):
        _plan(workspace=Path("/opt/build"))


def test_kernel_plan_rejects_absolute_output_dir() -> None:
    with pytest.raises(ValueError, match="relative"):
        _plan(output_dir=Path("/var/out"))


def test_kernel_plan_rejects_dotdot_in_workspace() -> None:
    with pytest.raises(ValueError, match="\\.\\."):
        _plan(workspace=Path("build/../etc"))


def test_kernel_plan_rejects_dotdot_in_output_dir() -> None:
    with pytest.raises(ValueError, match="\\.\\."):
        _plan(output_dir=Path("build/../../etc"))


def test_kernel_plan_rejects_nonpositive_jobs() -> None:
    with pytest.raises(ValueError, match="positive int"):
        _plan(build_jobs=0)


def test_kernel_plan_rejects_unknown_signing_policy() -> None:
    with pytest.raises(ValueError, match="signing_policy"):
        _plan(signing_policy="disabled")  # type: ignore[arg-type]


def test_kernel_plan_rejects_wrong_source_type() -> None:
    with pytest.raises(TypeError, match="KernelSource"):
        _plan(source="not-a-source")  # type: ignore[arg-type]


def test_kernel_plan_rejects_wrong_artifact_kind() -> None:
    with pytest.raises(TypeError, match="ArtifactKind"):
        _plan(intended_artifacts=("nonsense",))  # type: ignore[arg-type]


def test_kernel_plan_accepts_string_signing_policy() -> None:
    p = _plan(signing_policy="required")  # type: ignore[arg-type]
    assert p.signing_policy is SigningPolicy.REQUIRED


# ---------------------------------------------------------------------------
# CommandResult
# ---------------------------------------------------------------------------


def test_command_result_round_trip() -> None:
    r = CommandResult(
        argv=("make", "-j4", "bindeb-pkg"),
        cwd="/home/builder",
        returncode=0,
        elapsed_seconds=42.5,
        stdout_path="build/logs/make.out",
        stderr_path="build/logs/make.err",
        env_summary={"PATH": "/usr/bin", "GPG_KEY": "<redacted>"},
    )
    assert json.dumps(r.to_dict())
    assert CommandResult.from_dict(r.to_dict()) == r


def test_command_result_rejects_empty_argv() -> None:
    with pytest.raises(ValueError, match="argv"):
        CommandResult(argv=(), cwd="/tmp", returncode=0, elapsed_seconds=0.0)


def test_command_result_preserves_shell_metacharacters_verbatim() -> None:
    r = CommandResult(
        argv=("echo", "a b ; rm -rf /"),
        cwd="/tmp",
        returncode=0,
        elapsed_seconds=0.0,
    )
    assert r.argv[1] == "a b ; rm -rf /"


def test_redact_environment_masks_sensitive_names() -> None:
    env = {
        "PATH": "/usr/bin",
        "GPG_KEY": "abc",
        "SSH_TOKEN": "xyz",
        "DB_PASSWORD": "hunter2",
        "MOK_PIN": "1234",
        "AWS_CREDENTIAL": "secret",
        "NOT_SECRET": "visible",
    }
    redacted = redact_environment(env)
    assert redacted["PATH"] == "/usr/bin"
    assert redacted["NOT_SECRET"] == "<redacted>"  # conservative by design
    for key in ("GPG_KEY", "SSH_TOKEN", "DB_PASSWORD", "MOK_PIN", "AWS_CREDENTIAL"):
        assert redacted[key] == "<redacted>"


# ---------------------------------------------------------------------------
# BuildArtifact
# ---------------------------------------------------------------------------


def test_build_artifact_round_trip() -> None:
    a = BuildArtifact(
        kind=ArtifactKind.KERNEL_IMAGE_DEB,
        path="release/7.2.15-huey1/linux-image-7.2.15-huey1_amd64.deb",
        sha256=_sha("c"),
        size_bytes=52_000_000,
        kernel_release="7.2.15-huey1",
    )
    assert json.dumps(a.to_dict())
    assert BuildArtifact.from_dict(a.to_dict()) == a


def test_build_artifact_rejects_absolute_path() -> None:
    with pytest.raises(ValueError, match="relative"):
        BuildArtifact(
            kind=ArtifactKind.KERNEL_IMAGE_DEB,
            path="/etc/passwd",
            sha256=_sha(),
            size_bytes=1,
            kernel_release="7.2.15-huey1",
        )


def test_build_artifact_rejects_dotdot_escape() -> None:
    with pytest.raises(ValueError, match="\\.\\."):
        BuildArtifact(
            kind=ArtifactKind.KERNEL_IMAGE_DEB,
            path="release/../../../etc/passwd",
            sha256=_sha(),
            size_bytes=1,
            kernel_release="7.2.15-huey1",
        )


def test_build_artifact_rejects_bad_sha() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        BuildArtifact(
            kind=ArtifactKind.INITRAMFS,
            path="release/initramfs.img",
            sha256="deadbeef",
            size_bytes=1,
            kernel_release="7.2.15-huey1",
        )


def test_build_artifact_rejects_negative_size() -> None:
    with pytest.raises(ValueError, match="size_bytes"):
        BuildArtifact(
            kind=ArtifactKind.INITRAMFS,
            path="release/initramfs.img",
            sha256=_sha(),
            size_bytes=-1,
            kernel_release="7.2.15-huey1",
        )


# ---------------------------------------------------------------------------
# ValidationFinding
# ---------------------------------------------------------------------------


def test_validation_finding_round_trip() -> None:
    f = ValidationFinding(
        severity=Severity.ERROR,
        code="NV_MODULE_VERMAGIC_MISMATCH",
        message="staged nvidia.ko vermagic does not contain target release",
        context={"expected": "7.2.15-huey1", "got": "7.2.12+deb14-amd64"},
    )
    assert json.dumps(f.to_dict())
    assert ValidationFinding.from_dict(f.to_dict()) == f


def test_validation_finding_rejects_unknown_severity() -> None:
    with pytest.raises(ValueError, match="severity"):
        ValidationFinding(severity="fatal", code="X", message="y")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# BuildReport
# ---------------------------------------------------------------------------


def _artifact() -> BuildArtifact:
    return BuildArtifact(
        kind=ArtifactKind.KERNEL_IMAGE_DEB,
        path="release/7.2.15-huey1/linux-image.deb",
        sha256=_sha("d"),
        size_bytes=100,
        kernel_release="7.2.15-huey1",
    )


def _finding() -> ValidationFinding:
    return ValidationFinding(severity=Severity.INFO, code="OK", message="all good")


def test_build_report_round_trip() -> None:
    report = BuildReport(
        plan=_plan(),
        artifacts=(_artifact(),),
        findings=(_finding(),),
        status=BuildStatus.BUILT,
        approval=ApprovalState.PENDING,
        generated_at="2026-11-12T08:00:00Z",
    )
    data = report.to_dict()
    assert json.dumps(data)
    assert BuildReport.from_dict(data) == report


def test_build_report_rejects_bad_timestamp() -> None:
    with pytest.raises(ValueError, match="ISO 8601"):
        BuildReport(
            plan=_plan(),
            artifacts=(),
            findings=(),
            status=BuildStatus.BUILT,
            approval=ApprovalState.PENDING,
            generated_at="yesterday",
        )


def test_build_report_rejects_wrong_status_type() -> None:
    with pytest.raises(ValueError, match="status"):
        BuildReport(
            plan=_plan(),
            artifacts=(),
            findings=(),
            status="done",  # type: ignore[arg-type]
            approval=ApprovalState.PENDING,
            generated_at="2026-11-12T08:00:00Z",
        )


# ---------------------------------------------------------------------------
# Cross-model invariants
# ---------------------------------------------------------------------------


def test_all_models_are_frozen() -> None:
    src = _source()
    with pytest.raises(Exception):
        src.source = "mutated"  # type: ignore[misc]


def test_to_dict_output_is_deterministic() -> None:
    """Repeated to_dict calls produce the same JSON serialization."""
    p = _plan()
    a = json.dumps(p.to_dict(), sort_keys=True)
    b = json.dumps(p.to_dict(), sort_keys=True)
    assert a == b


# ---------------------------------------------------------------------------
# Additional fail-closed checks for Step 4
# ---------------------------------------------------------------------------


def test_command_result_redacts_environment_on_construction() -> None:
    result = CommandResult(
        argv=("make",), cwd="/tmp", returncode=0, elapsed_seconds=0.1,
        env_summary={"PATH": "/usr/bin", "API_TOKEN": "unsafe-value"},
    )
    assert result.env_summary["API_TOKEN"] == "<redacted>"
    assert "unsafe-value" not in json.dumps(result.to_dict())
    assert CommandResult.from_dict(result.to_dict()) == result


@pytest.mark.parametrize("key", ["workspace", "output_dir"])
@pytest.mark.parametrize("path", ["", ".", " ", "build/\x00invalid"])
def test_kernel_plan_rejects_empty_or_null_destinations(key: str, path: str) -> None:
    with pytest.raises(ValueError):
        _plan(**{key: path})


def test_build_artifact_rejects_project_root_as_output() -> None:
    with pytest.raises(ValueError):
        BuildArtifact(
            kind=ArtifactKind.MANIFEST, path=".", sha256=_sha(),
            size_bytes=1, kernel_release="7.2.15-huey1",
        )


@pytest.mark.parametrize("value", [True, "4", 0, -1])
def test_kernel_plan_rejects_bad_build_jobs(value: object) -> None:
    with pytest.raises(ValueError):
        _plan(build_jobs=value)


def test_build_artifact_rejects_bool_size() -> None:
    with pytest.raises(ValueError):
        BuildArtifact(kind=ArtifactKind.MANIFEST, path="release/manifest.json",
                      sha256=_sha(), size_bytes=True, kernel_release="7.2.15-huey1")


@pytest.mark.parametrize("model,payload", [
    (KernelSource, {"source_type": "upstream", "unrecognized": "x"}),
    (GPUIdentity, {"vendor": "nvidia", "model": "V100", "pci_address": "00000000:01:00.0", "unrecognized": "x"}),
    (DriverBaseline, {"driver_version": "580.196.07", "module_flavor": "proprietary", "unrecognized": "x"}),
])
def test_from_dict_rejects_unknown_fields(model: type, payload: dict) -> None:
    with pytest.raises(ValueError, match="unknown fields"):
        model.from_dict(payload)


def test_from_dict_rejects_coercion_of_build_jobs() -> None:
    data = _plan().to_dict()
    data["build_jobs"] = "4"
    with pytest.raises(ValueError, match="build_jobs"):
        KernelPlan.from_dict(data)


@pytest.mark.parametrize("name,kwargs", [
    ("source_type", {"source_type": 3}),
    ("checksum", {"checksum": 42}),
    ("version", {"version": 42}),
])
def test_kernel_source_rejects_wrong_field_shapes(name: str, kwargs: dict) -> None:
    with pytest.raises((TypeError, ValueError), match=name):
        _source(**kwargs)


def test_gpu_identity_rejects_non_enum_vendor() -> None:
    with pytest.raises(TypeError, match="vendor"):
        GPUIdentity(vendor=42, model="V100", pci_address="00000000:01:00.0")


def test_driver_baseline_rejects_non_enum_flavor() -> None:
    with pytest.raises(TypeError, match="module_flavor"):
        _driver(module_flavor=42)


def test_build_artifact_rejects_non_enum_kind() -> None:
    with pytest.raises(TypeError, match="kind"):
        BuildArtifact(kind=42, path="release/file", sha256=_sha(),
                      size_bytes=1, kernel_release="7.2.15-huey1")


def test_validation_finding_rejects_non_enum_severity() -> None:
    with pytest.raises(TypeError, match="severity"):
        ValidationFinding(severity=42, code="BAD", message="wrong type")


def test_from_dict_rejects_missing_required_field() -> None:
    with pytest.raises(ValueError, match="missing fields"):
        GPUIdentity.from_dict({"vendor": "nvidia", "model": "V100"})


def test_from_dict_rejects_nonstring_object_key() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        KernelSource.from_dict({"source_type": "upstream", 1: "bad"})


@pytest.mark.parametrize("seconds", [float("nan"), float("inf"), -1.0])
def test_command_result_rejects_nonfinite_or_negative_time(seconds: float) -> None:
    with pytest.raises(ValueError, match="elapsed_seconds"):
        CommandResult(argv=("make",), cwd="/tmp", returncode=0, elapsed_seconds=seconds)


def test_build_report_rejects_impossible_date() -> None:
    with pytest.raises(ValueError, match="ISO 8601"):
        BuildReport(
            plan=_plan(), artifacts=(), findings=(), status=BuildStatus.BUILT,
            approval=ApprovalState.PENDING, generated_at="2026-02-30T08:00:00Z",
        )
