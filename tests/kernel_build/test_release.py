"""Tests for huey.kernel_build.release (Step 20; Step 44 expands)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from huey.kernel_build.models import (
    ApprovalState,
    Severity,
    ValidationFinding,
)
from huey.kernel_build.release import (
    ReleaseAssembler,
    ReleaseContext,
    ReleaseResult,
)
from huey.kernel_build.verifier import VerificationResult


KR = "7.2.15-huey1"
DRV = "580.196.07"


def _verification(
    *,
    boot_ready: bool = True,
    dry_run: bool = False,
    findings: tuple[ValidationFinding, ...] = (),
    static_checks_passed: bool = True,
) -> VerificationResult:
    return VerificationResult(
        findings=findings,
        boot_ready=boot_ready,
        static_checks_passed=static_checks_passed,
        host_checks_required=("boot_and_storage", "nvidia_module_load") if boot_ready else (),
        dry_run=dry_run,
    )


def _setup(tmp_path: Path) -> dict:
    """Construct a complete, valid set of inputs for release assembly."""
    stage = tmp_path / "stage"
    if stage.exists():
        # Reusing a fixture must not resurrect artifacts a test removed.
        return {
            "stage": stage,
            "image": stage / f"linux-image-{KR}_7.2.15-huey1-1_amd64.deb",
            "headers": stage / f"linux-headers-{KR}_7.2.15-huey1-1_amd64.deb",
            "nvidia_dir": stage / f"nvidia-{DRV}-{KR}",
            "initramfs": stage / f"initramfs-{KR}",
            "config": stage / "config",
            "lock": stage / "source.lock.json",
        }
    stage.mkdir()

    image = stage / f"linux-image-{KR}_7.2.15-huey1-1_amd64.deb"
    image.write_bytes(b"fake image deb\n")
    headers = stage / f"linux-headers-{KR}_7.2.15-huey1-1_amd64.deb"
    headers.write_bytes(b"fake headers deb\n")

    nvidia_dir = stage / f"nvidia-{DRV}-{KR}"
    nvidia_dir.mkdir()
    (nvidia_dir / "nvidia.ko").write_bytes(b"fake nvidia.ko\n")
    (nvidia_dir / "nvidia-uvm.ko").write_bytes(b"fake nvidia-uvm.ko\n")

    initramfs = stage / f"initramfs-{KR}"
    initramfs.write_bytes(b"fake initramfs\n")

    config = stage / "config"
    config.write_text("CONFIG_MODULES=y\n", encoding="utf-8")

    lock = stage / "source.lock.json"
    lock.write_text(
        json.dumps({
            "schema_version": 1, "status": "pinned",
            "source_type": "debian-linux-source",
            "package_name": "linux-source-7.2",
            "version": "7.2.15-1",
            "archive_filename": "linux-source-7.2.deb",
            "origin_url": "https://deb.debian.org/x",
            "checksum_sha256": "a" * 64,
            "retrieved_date": "2026-11-12",
            "license": "GPL-2.0-only",
            "profile_revision": 1, "notes": "",
        }),
        encoding="utf-8",
    )

    return {
        "stage": stage,
        "image": image,
        "headers": headers,
        "nvidia_dir": nvidia_dir,
        "initramfs": initramfs,
        "config": config,
        "lock": lock,
    }


def _context(tmp_path: Path, **overrides) -> ReleaseContext:
    s = _setup(tmp_path)
    base = ReleaseContext(
        release_dir=tmp_path / "release",
        kernel_release=KR,
        driver_version=DRV,
        profile="v100-workstation",
        verification=_verification(),
        kernel_image_deb=s["image"],
        kernel_headers_deb=s["headers"],
        nvidia_modules_dir=s["nvidia_dir"],
        initramfs=s["initramfs"],
        config_path=s["config"],
        source_lock_path=s["lock"],
        tool_versions={"gcc": "14.2.0", "make": "4.4.1"},
        approval_state=ApprovalState.PENDING,
        rollback_notes="Rollback: boot the previous kernel via GRUB.",
    )
    return replace(base, **overrides) if overrides else base


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_assembles_release(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)

    assert result.has_errors() is False, result.findings
    assert result.dry_run is False
    assert result.release_dir == ctx.release_dir
    assert result.manifest_path is not None and result.manifest_path.is_file()
    assert result.checksums_path is not None and result.checksums_path.is_file()
    assert result.distribution_restricted is True

    # Every artifact file landed in the release directory.
    for art in result.artifacts:
        assert (ctx.release_dir / art.build_artifact.path).is_file()
    # Both NVIDIA modules are restricted.
    restricted = [a for a in result.artifacts if a.redistribution == "restricted"]
    assert {a.name for a in restricted} >= {
        f"nvidia-{DRV}-{KR}/nvidia.ko",
        f"nvidia-{DRV}-{KR}/nvidia-uvm.ko",
    }
    # Initramfs is restricted because it accompanies proprietary modules.
    initramfs_rec = next(
        a for a in result.artifacts if a.build_artifact.path == f"initramfs-{KR}"
    )
    assert initramfs_rec.redistribution == "restricted"
    # Kernel .debs are public.
    image_rec = next(
        a for a in result.artifacts if a.build_artifact.path == ctx.kernel_image_deb.name
    )
    assert image_rec.redistribution == "public"


def test_manifest_contains_expected_fields(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)
    assert result.manifest_path is not None
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["kernel_release"] == KR
    assert manifest["driver_version"] == DRV
    assert manifest["profile"] == "v100-workstation"
    assert manifest["approval_state"] == "pending"
    assert manifest["boot_ready"] is True
    assert manifest["distribution_restricted"] is True
    assert "NVIDIA proprietary" in manifest["distribution_warning"]
    assert manifest["host_checks_required"] == [
        "boot_and_storage", "nvidia_module_load",
    ]
    assert manifest["checks_summary"]["boot_ready"] is True
    assert manifest["tool_versions"]["gcc"] == "14.2.0"
    assert manifest["source_lock"]["status"] == "pinned"
    assert manifest["rollback_notes"] is not None
    assert any(
        a["name"] == f"nvidia-{DRV}-{KR}/nvidia.ko"
        and a["redistribution"] == "restricted"
        and a["provenance"] == "nvidia-proprietary"
        for a in manifest["artifacts"]
    )


def test_manifest_sha256_matches_disk(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["artifacts"]:
        full = ctx.release_dir / entry["path"]
        actual = hashlib.sha256(full.read_bytes()).hexdigest()
        assert actual == entry["sha256"], entry["path"]


def test_checksums_file_matches_disk(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)
    lines = result.checksums_path.read_text(encoding="utf-8").splitlines()
    assert lines
    for line in lines:
        sha, name = line.split("  ", 1)
        full = ctx.release_dir / name
        assert hashlib.sha256(full.read_bytes()).hexdigest() == sha


def test_rollback_notes_file_written(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)
    notes = ctx.release_dir / "rollback-notes.md"
    assert notes.is_file()
    assert "Rollback" in notes.read_text(encoding="utf-8")
    assert any(a.name == "rollback-notes.md" for a in result.artifacts)


def test_result_json_serializable(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)
    payload = json.dumps(result.to_dict())
    assert KR in payload
    assert '"distribution_restricted": true' in payload


# ---------------------------------------------------------------------------
# Fail-closed: verification gate
# ---------------------------------------------------------------------------


def test_refuses_when_verification_boot_ready_false(tmp_path: Path) -> None:
    ctx = _context(
        tmp_path, verification=_verification(boot_ready=False)
    )
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "VERIFICATION_NOT_READY" in codes
    assert result.release_dir is None
    assert not ctx.release_dir.exists() or not any(ctx.release_dir.iterdir())


def test_refuses_dry_run_verification(tmp_path: Path) -> None:
    ctx = _context(tmp_path, verification=_verification(dry_run=True))
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "VERIFICATION_DRY_RUN" in codes


def test_refuses_error_findings_in_verification(tmp_path: Path) -> None:
    finding = ValidationFinding(severity=Severity.ERROR, code="X", message="y")
    ctx = _context(
        tmp_path, verification=_verification(findings=(finding,))
    )
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "VERIFICATION_NOT_READY" in codes


# ---------------------------------------------------------------------------
# Fail-closed: protected release_dir
# ---------------------------------------------------------------------------


def test_refuses_boot_release_dir(tmp_path: Path) -> None:
    ctx = _context(tmp_path, release_dir=Path("/boot/huey-release"))
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "RELEASE_DIR_PROTECTED" in codes


def test_refuses_root_release_dir(tmp_path: Path) -> None:
    ctx = _context(tmp_path, release_dir=Path("/"))
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "RELEASE_DIR_PROTECTED" in codes


def test_refuses_etc_subdir(tmp_path: Path) -> None:
    ctx = _context(tmp_path, release_dir=Path("/etc/huey"))
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "RELEASE_DIR_PROTECTED" in codes


# ---------------------------------------------------------------------------
# Fail-closed: missing artifacts
# ---------------------------------------------------------------------------


def test_missing_kernel_image_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    s["image"].unlink()
    ctx = _context(tmp_path, kernel_image_deb=s["image"])
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "ARTIFACT_MISSING" in codes


def test_missing_kernel_headers_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    s["headers"].unlink()
    ctx = _context(tmp_path, kernel_headers_deb=s["headers"])
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "ARTIFACT_MISSING" in codes


def test_v100_profile_without_nvidia_modules_errors(tmp_path: Path) -> None:
    ctx = _context(tmp_path, nvidia_modules_dir=None)
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "NVIDIA_MODULES_REQUIRED" in codes


def test_empty_nvidia_modules_dir_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    empty = tmp_path / "empty-nvidia"
    empty.mkdir()
    ctx = _context(tmp_path, nvidia_modules_dir=empty)
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "NVIDIA_MODULES_EMPTY" in codes


# ---------------------------------------------------------------------------
# Fail-closed: secret detection
# ---------------------------------------------------------------------------


def test_refuses_secret_in_rollback_notes(tmp_path: Path) -> None:
    ctx = _context(
        tmp_path,
        rollback_notes="MOK_PIN=hunter2",
    )
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "SECRET_DETECTED" in codes
    assert result.release_dir is None


def test_refuses_pem_private_key_in_extra_text(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    secret = tmp_path / "leak.txt"
    secret.write_text(
        "-----BEGIN RSA PRIVATE KEY-----\nAAAA\n-----END RSA PRIVATE KEY-----\n",
        encoding="utf-8",
    )
    ctx = _context(tmp_path, extra_text_files=(secret,))
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "SECRET_DETECTED" in codes


def test_refuses_forbidden_priv_extension(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    priv = tmp_path / "key.priv"
    priv.write_bytes(b"looks like a private key")
    ctx = _context(tmp_path, extra_text_files=(priv,))
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "FORBIDDEN_FILENAME" in codes


def test_refuses_id_rsa_filename(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    key = tmp_path / "id_rsa"
    key.write_bytes(b"ssh key")
    ctx = _context(tmp_path, extra_text_files=(key,))
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "FORBIDDEN_FILENAME" in codes


def test_refuses_env_file(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    env = tmp_path / ".env"
    env.write_text("GITHUB_TOKEN=xyz\n", encoding="utf-8")
    ctx = _context(tmp_path, extra_text_files=(env,))
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "FORBIDDEN_FILENAME" in codes


# ---------------------------------------------------------------------------
# Existing directory handling
# ---------------------------------------------------------------------------


def test_refuses_non_empty_release_dir_without_force(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    ctx.release_dir.mkdir(parents=True)
    (ctx.release_dir / "existing.txt").write_text("keep", encoding="utf-8")
    result = ReleaseAssembler().build_release(ctx)
    codes = {f.code for f in result.findings}
    assert "RELEASE_DIR_NOT_EMPTY" in codes


def test_force_clears_release_dir(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    ctx.release_dir.mkdir(parents=True)
    stale = ctx.release_dir / "stale.txt"
    stale.write_text("old", encoding="utf-8")
    result = ReleaseAssembler().build_release(ctx, force=True)
    assert not stale.exists()
    assert result.has_errors() is False


def test_empty_release_dir_ok(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    ctx.release_dir.mkdir(parents=True)
    result = ReleaseAssembler().build_release(ctx)
    assert result.has_errors() is False


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


def test_dry_run_no_io(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx, dry_run=True)
    assert result.dry_run is True
    assert result.release_dir is None
    assert result.manifest_path is None
    assert not ctx.release_dir.exists()
    codes = {f.code for f in result.findings}
    assert "RELEASE_DRY_RUN" in codes


# ---------------------------------------------------------------------------
# Distribution restriction
# ---------------------------------------------------------------------------


def test_distribution_restricted_warning_present(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)
    warning = [f for f in result.findings if f.code == "DISTRIBUTION_RESTRICTED"]
    assert warning
    assert warning[0].severity == Severity.WARNING
    assert "NVIDIA proprietary" in warning[0].message


def test_public_release_not_restricted(tmp_path: Path) -> None:
    """A hypothetical profile without proprietary modules should be public."""
    ctx = _context(
        tmp_path,
        profile="lab",
        nvidia_modules_dir=None,
        initramfs=None,  # initramfs restriction depends on nvidia presence
    )
    result = ReleaseAssembler().build_release(ctx)
    assert result.distribution_restricted is False


# ---------------------------------------------------------------------------
# Approval state
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "state", [ApprovalState.PENDING, ApprovalState.APPROVED, ApprovalState.NOT_REQUIRED]
)
def test_approval_state_recorded(tmp_path: Path, state: ApprovalState) -> None:
    ctx = _context(tmp_path, approval_state=state)
    result = ReleaseAssembler().build_release(ctx)
    assert result.approval_state == state
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["approval_state"] == state.value


# ---------------------------------------------------------------------------
# Source lock passthrough
# ---------------------------------------------------------------------------


def test_source_lock_metadata_recorded(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_lock"]["status"] == "pinned"
    assert manifest["source_lock"]["version"] == "7.2.15-1"
    assert len(manifest["source_lock"]["sha256"]) == 64


# Release assembly must refuse unresolved locks and overlapping staged inputs.
def test_unresolved_lock_cannot_be_bypassed_by_ready_result(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    lock = json.loads(ctx.source_lock_path.read_text(encoding="utf-8"))
    lock["status"] = "unresolved"
    lock["checksum_sha256"] = "0" * 64
    ctx.source_lock_path.write_text(json.dumps(lock), encoding="utf-8")
    result = ReleaseAssembler().build_release(ctx)
    assert result.has_errors()
    assert "SOURCE_LOCK_UNRESOLVED" in {f.code for f in result.findings}
    assert not ctx.release_dir.exists()


def test_force_must_not_delete_source_staging_directory(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    stage = ctx.kernel_image_deb.parent
    ctx = replace(ctx, release_dir=stage)
    original = ctx.kernel_image_deb.read_bytes()
    result = ReleaseAssembler().build_release(ctx, force=True)
    assert "RELEASE_OVERLAPS_INPUT" in {f.code for f in result.findings}
    assert ctx.kernel_image_deb.read_bytes() == original


def test_refuse_duplicate_release_artifact_path(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    extra = tmp_path / ctx.kernel_image_deb.name
    extra.write_bytes(b"not the image",)
    ctx = replace(ctx, extra_text_files=(extra,))
    result = ReleaseAssembler().build_release(ctx)
    assert "ARTIFACT_PATH_COLLISION" in {f.code for f in result.findings}
    assert not ctx.release_dir.exists()


def test_refuse_release_artifact_symlink(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    link = tmp_path / "something.txt"
    link.symlink_to(ctx.config_path)
    ctx = replace(ctx, extra_text_files=(link,))
    result = ReleaseAssembler().build_release(ctx)
    assert "ARTIFACT_SYMLINK_REFUSED" in {f.code for f in result.findings}
    assert not ctx.release_dir.exists()


# Step 44: additional canonical release-assembler adversarial checks.

def test_release_refuses_unknown_source_lock(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    lock = ctx.source_lock_path
    assert lock is not None
    lock.write_text("not json", encoding="utf-8")
    result = ReleaseAssembler().build_release(ctx)
    assert result.has_errors()
    assert "SOURCE_LOCK_INVALID" in {f.code for f in result.findings}
    assert not ctx.release_dir.exists()


def test_release_requires_source_lock(tmp_path: Path) -> None:
    ctx = _context(tmp_path, source_lock_path=None)
    result = ReleaseAssembler().build_release(ctx)
    assert result.has_errors()
    assert "SOURCE_LOCK_REQUIRED" in {f.code for f in result.findings}
    assert not ctx.release_dir.exists()


def test_release_rejects_zero_hash_as_pinned_source(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    doc = json.loads(ctx.source_lock_path.read_text())
    doc["checksum_sha256"] = "0" * 64
    ctx.source_lock_path.write_text(json.dumps(doc))
    result = ReleaseAssembler().build_release(ctx)
    assert "SOURCE_LOCK_UNRESOLVED" in {f.code for f in result.findings}
    assert not ctx.release_dir.exists()


def test_release_refuses_symlinked_extra_file(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    link = tmp_path / "extra.txt"
    link.symlink_to(ctx.config_path)
    result = ReleaseAssembler().build_release(replace(ctx, extra_text_files=(link,)))
    assert "ARTIFACT_SYMLINK_REFUSED" in {f.code for f in result.findings}
    assert not ctx.release_dir.exists()


def test_release_dry_run_is_no_write_with_nonempty_release(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    ctx.release_dir.mkdir()
    marker = ctx.release_dir / "operator-data.txt"
    marker.write_bytes(b"preserve")
    result = ReleaseAssembler().build_release(ctx, force=True, dry_run=True)
    assert result.dry_run
    assert marker.read_bytes() == b"preserve"
    assert not (ctx.release_dir / "MANIFEST.json").exists()


def test_release_hashes_cover_every_declared_artifact(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    result = ReleaseAssembler().build_release(ctx)
    assert not result.has_errors(), result.findings
    manifest = json.loads(result.manifest_path.read_text())
    entries = manifest["artifacts"]
    assert entries
    assert len({a["path"] for a in entries}) == len(entries)
    for item in entries:
        assert not Path(item["path"]).is_absolute()
        assert ".." not in Path(item["path"]).parts
        actual = ctx.release_dir / item["path"]
        assert actual.is_file()
        assert hashlib.sha256(actual.read_bytes()).hexdigest() == item["sha256"]


def test_release_refuses_critical_verification_even_if_boot_ready_flag(tmp_path: Path) -> None:
    critical = ValidationFinding(
        severity=Severity.CRITICAL, code="WRONG_KERNEL", message="bad ABI",
    )
    ctx = _context(tmp_path, verification=_verification(
        boot_ready=True, findings=(critical,),
    ))
    result = ReleaseAssembler().build_release(ctx)
    assert result.has_errors()
    assert not ctx.release_dir.exists()


def test_release_never_mutates_staging_inputs(tmp_path: Path) -> None:
    ctx = _context(tmp_path)
    source_files = (
        ctx.kernel_image_deb, ctx.kernel_headers_deb, ctx.initramfs,
        ctx.config_path, ctx.source_lock_path,
    )
    before = {p: (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
              for p in source_files}
    result = ReleaseAssembler().build_release(ctx)
    assert not result.has_errors(), result.findings
    after = {p: (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
             for p in source_files}
    assert after == before


def test_release_disallows_protected_host_mutation_under_etc(tmp_path: Path) -> None:
    ctx = _context(tmp_path, release_dir=Path("/etc/huey-kernel-release"))
    result = ReleaseAssembler().build_release(ctx)
    assert result.has_errors()
    assert "RELEASE_DIR_PROTECTED" in {f.code for f in result.findings}
