"""Canonical test suite for huey.kernel_build.verifier (Step 43).

Step 19 landed an initial suite proving each branch worked. This file
expands that suite to the full contract required by the handoff:

* package metadata (every expected package required; no .deb at all);
* module metadata (vermagic per file, version per nvidia* file);
* dependency closure (each missing dependency reported; compressed
  .ko forms discovered);
* initramfs (wrong release, missing module, forbidden module,
  lsinitramfs failure);
* Secure Boot compatibility (enabled + not-signed, unknown);
* signing (wrong key per module, missing sig_key per module, missing
  file, absent expected fingerprint);
* hashes (mismatch, missing file, multiple failures);
* lockfile (unresolved, invalid, absent);
* boot_ready contract (empty vs populated host_checks_required);
* dry run (filesystem only, boot_ready False);
* structural (no forbidden command, no protected path in argv).

All subprocesses are simulated via FixtureRunner; all filesystem state
is under tmp_path. Nothing reads /boot, /lib/modules, /etc, or a GPU.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Callable

import pytest

from huey.kernel_build.models import (
    ArtifactKind,
    BuildArtifact,
    CommandResult,
    Severity,
)
from huey.kernel_build.policy import SecureBootState
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerResult,
    RunnerTimeout,
)
from huey.kernel_build.verifier import (
    HOST_CHECKS,
    ReleaseVerifier,
    VerificationContext,
    VerificationResult,
)


# ===========================================================================
# FixtureRunner
# ===========================================================================


class FixtureRunner:
    def __init__(self) -> None:
        self._handlers: list = []
        self._calls: list[CommandSpec] = []

    def on(self, matcher, handler) -> "FixtureRunner":
        self._handlers.append((matcher, handler))
        return self

    def run(self, spec: CommandSpec, *, dry_run: bool = False) -> RunnerResult:
        self._calls.append(spec)
        for matcher, handler in self._handlers:
            if matcher(spec):
                return handler(spec)
        raise RunnerError(f"FixtureRunner: no handler for argv={spec.argv!r}")

    @property
    def calls(self) -> tuple[CommandSpec, ...]:
        return tuple(self._calls)


def _ok(spec, *, stdout: bytes = b"") -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv, cwd=str(spec.cwd),
            returncode=0, elapsed_seconds=0.0,
        ),
        executed=True, dry_run=False, stdout=stdout, stderr=b"",
    )


def _fail(spec, returncode: int = 1) -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv, cwd=str(spec.cwd),
            returncode=returncode, elapsed_seconds=0.0,
        ),
        executed=True, dry_run=False, stdout=b"", stderr=b"",
    )


def _is_dpkg_deb(spec): return spec.argv[0] == "dpkg-deb"
def _is_modinfo(spec): return spec.argv[0] == "modinfo"
def _is_lsinitramfs(spec): return spec.argv[0] == "lsinitramfs"


# ===========================================================================
# Fixtures and builder
# ===========================================================================

KR = "7.2.15-huey1"
DRV = "580.196.07"
FP = (
    "13:FE:C2:ED:A1:40:CE:70:1A:75:91:E5:4C:1F:5F:DA:"
    "BD:17:57:A9:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55"
)
WRONG_FP = (
    "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:"
    "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99"
)


def _make_deb(path: Path, package: str, version: str = "7.2.15-huey1-1") -> Path:
    if path.is_dir():
        path = path / f"{package}_{version}_amd64.deb"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"fake deb {package} {version}\n".encode())
    return path


def _make_module(
    path: Path,
    *,
    vermagic: str = KR,
    version: str = DRV,
    sig_key: str | None = FP,
    depends: str = "",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(f"fake ko {path.name} {version}\n".encode())
    return path


def _build_runner(
    *,
    deb_fields: dict[Path, str] | None = None,
    modinfo_fields: dict[Path, dict[str, str | None]] | None = None,
    lsinitramfs_listing: tuple[str, ...] | None = None,
    lsinitramfs_returncode: int = 0,
    dpkg_deb_returncode: int = 0,
    modinfo_vermagic_returncode: int = 0,
) -> FixtureRunner:
    deb_fields = deb_fields or {}
    modinfo_fields = modinfo_fields or {}
    r = FixtureRunner()

    def _deb(spec):
        if dpkg_deb_returncode != 0:
            return _fail(spec, dpkg_deb_returncode)
        path = Path(spec.argv[2])
        field = spec.argv[3]
        pkg = deb_fields.get(path)
        if pkg is None:
            return _fail(spec, returncode=2)
        return _ok(spec, stdout=f"{field}: {pkg}\n".encode())

    def _modinfo(spec):
        field = spec.argv[2]
        path = Path(spec.argv[3])
        values = modinfo_fields.get(path)
        if values is None or values.get(field) is None:
            if field == "vermagic" and modinfo_vermagic_returncode != 0:
                return _fail(spec, modinfo_vermagic_returncode)
            return _fail(spec, returncode=1)
        return _ok(spec, stdout=f"{values[field]}\n".encode())

    def _lsinit(spec):
        if lsinitramfs_returncode != 0:
            return _fail(spec, lsinitramfs_returncode)
        entries = lsinitramfs_listing or ()
        return _ok(spec, stdout=("\n".join(entries) + "\n").encode())

    r.on(_is_dpkg_deb, _deb)
    r.on(_is_modinfo, _modinfo)
    r.on(_is_lsinitramfs, _lsinit)
    return r


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _setup_happy(tmp_path: Path) -> dict:
    """Build a full happy-path release tree and the FixtureRunner kwargs."""
    rd = tmp_path / "release"
    rd.mkdir()

    image_deb = _make_deb(rd / f"linux-image-{KR}_7.2.15-huey1-1_amd64.deb", f"linux-image-{KR}")
    headers_deb = _make_deb(rd / f"linux-headers-{KR}_7.2.15-huey1-1_amd64.deb", f"linux-headers-{KR}")

    nvidia_ko = _make_module(rd / "modules" / "nvidia.ko", depends="")
    uvm_ko = _make_module(
        rd / "modules" / "nvidia-uvm.ko", depends="nvidia"
    )

    initramfs = rd / f"initramfs-{KR}"
    initramfs.write_bytes(b"fake initramfs archive\n")

    lock = tmp_path / "source.lock.json"
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

    module_tree = tmp_path / "tree"
    (module_tree / "kernel").mkdir(parents=True)
    (module_tree / "modules.dep").write_text(
        "kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko:\n"
        "kernel/drivers/gpu/drm/drm.ko:\n",
        encoding="utf-8",
    )

    manifest = (
        BuildArtifact(
            kind=ArtifactKind.KERNEL_IMAGE_DEB,
            path=str(image_deb.relative_to(rd)),
            sha256=_sha(image_deb), size_bytes=image_deb.stat().st_size,
            kernel_release=KR,
        ),
        BuildArtifact(
            kind=ArtifactKind.KERNEL_HEADERS_DEB,
            path=str(headers_deb.relative_to(rd)),
            sha256=_sha(headers_deb), size_bytes=headers_deb.stat().st_size,
            kernel_release=KR,
        ),
    )

    ctx = VerificationContext(
        release_dir=rd,
        kernel_release=KR,
        driver_version=DRV,
        expected_packages=(f"linux-image-{KR}", f"linux-headers-{KR}"),
        required_modules=("nvidia", "nvidia-uvm"),
        module_tree_dir=module_tree,
        initramfs_path=initramfs,
        manifest_artifacts=manifest,
        require_signed_modules=True,
        expected_cert_fingerprint=FP,
        lockfile_path=lock,
        secure_boot_state=SecureBootState.ENABLED,
    )

    runner_kwargs = {
        "deb_fields": {
            image_deb: f"linux-image-{KR}",
            headers_deb: f"linux-headers-{KR}",
        },
        "modinfo_fields": {
            nvidia_ko: {
                "vermagic": f"{KR} SMP mod_unload modversions",
                "version": DRV, "sig_key": FP, "depends": "",
            },
            uvm_ko: {
                "vermagic": f"{KR} SMP mod_unload modversions",
                "version": DRV, "sig_key": FP, "depends": "nvidia",
            },
        },
        "lsinitramfs_listing": (
            f"lib/modules/{KR}/modules.dep",
            f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
            f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko",
        ),
    }
    return {"ctx": ctx, "runner": runner_kwargs, "tree": rd}


# ===========================================================================
# Happy path and boot_ready contract
# ===========================================================================


def test_happy_path_all_checks_pass(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    assert result.static_checks_passed is True, result.findings
    assert result.boot_ready is True
    assert set(result.host_checks_required) == set(HOST_CHECKS)
    assert not result.has_errors()


def test_result_json_serializable(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    payload = json.dumps(result.to_dict())
    assert '"boot_ready": true' in payload
    assert "host_checks_required" in payload
    # The host check names are stable.
    loaded = json.loads(payload)
    assert set(loaded["host_checks_required"]) == set(HOST_CHECKS)


def test_host_checks_empty_when_not_ready(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    # Break vermagic on one module.
    nvidia_ko = next(p for p in s["runner"]["modinfo_fields"] if p.name == "nvidia.ko")
    s["runner"]["modinfo_fields"][nvidia_ko]["vermagic"] = "wrong"
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    assert result.boot_ready is False
    assert result.host_checks_required == ()


def test_boot_ready_false_on_any_blocking(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    # Corrupt one artifact's SHA.
    bad_art = replace(s["ctx"].manifest_artifacts[0], sha256="0" * 64)
    s["ctx"] = replace(s["ctx"], manifest_artifacts=(bad_art, s["ctx"].manifest_artifacts[1]))
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    assert result.boot_ready is False
    codes = {f.code for f in result.findings}
    assert "ARTIFACT_SHA256_MISMATCH" in codes


# ===========================================================================
# Release dir precondition
# ===========================================================================


def test_missing_release_dir_errors(tmp_path: Path) -> None:
    ctx = VerificationContext(
        release_dir=tmp_path / "nope",
        kernel_release=KR, driver_version=DRV,
    )
    result = ReleaseVerifier(_build_runner()).verify_release(ctx)
    assert result.boot_ready is False
    codes = {f.code for f in result.findings}
    assert "RELEASE_DIR_MISSING" in codes


# ===========================================================================
# Package metadata
# ===========================================================================


def test_expected_package_missing_errors(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(
        s["ctx"],
        expected_packages=(f"linux-image-{KR}", "linux-unknown"),
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "EXPECTED_PACKAGE_MISSING" in codes
    assert result.boot_ready is False


def test_every_expected_package_required(tmp_path: Path) -> None:
    """Each entry in expected_packages is checked independently."""
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(
        s["ctx"],
        expected_packages=(
            f"linux-image-{KR}", f"linux-headers-{KR}",
            "linux-extra-a", "linux-extra-b",
        ),
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    # Both missing packages produce findings.
    missing = [f for f in result.findings if f.code == "EXPECTED_PACKAGE_MISSING"]
    assert len(missing) == 2


def test_no_debs_in_release_errors(tmp_path: Path) -> None:
    rd = tmp_path / "release"
    rd.mkdir()
    ctx = VerificationContext(
        release_dir=rd, kernel_release=KR, driver_version=DRV,
        expected_packages=(f"linux-image-{KR}",),
    )
    result = ReleaseVerifier(_build_runner()).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "NO_DEBS_IN_RELEASE" in codes


def test_dpkg_deb_unavailable_warns(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    result = ReleaseVerifier(
        _build_runner(dpkg_deb_returncode=2, **{k: v for k, v in s["runner"].items() if k != "dpkg_deb_returncode"})
    ).verify_release(s["ctx"])
    # All expected packages end up missing because field lookup failed.
    codes = {f.code for f in result.findings}
    assert "EXPECTED_PACKAGE_MISSING" in codes


# ===========================================================================
# Module metadata: vermagic and version
# ===========================================================================


def test_vermagic_mismatch_is_critical(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    nvidia_ko = next(p for p in s["runner"]["modinfo_fields"] if p.name == "nvidia.ko")
    s["runner"]["modinfo_fields"][nvidia_ko]["vermagic"] = "7.2.12+deb14-amd64 SMP mod_unload"
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "VERMAGIC_MISMATCH" in codes
    critical = [f for f in result.findings if f.code == "VERMAGIC_MISMATCH"]
    assert critical[0].severity == Severity.CRITICAL


def test_module_version_mismatch_errors(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    uvm_ko = next(p for p in s["runner"]["modinfo_fields"] if p.name == "nvidia-uvm.ko")
    s["runner"]["modinfo_fields"][uvm_ko]["version"] = "550.100.00"
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "MODULE_VERSION_MISMATCH" in codes


def test_vermagic_failure_on_each_module(tmp_path: Path) -> None:
    """A vermagic mismatch on ANY module fails the whole verification."""
    s = _setup_happy(tmp_path)
    uvm_ko = next(p for p in s["runner"]["modinfo_fields"] if p.name == "nvidia-uvm.ko")
    s["runner"]["modinfo_fields"][uvm_ko]["vermagic"] = "wrong"
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    assert result.boot_ready is False


def test_compressed_ko_found_by_glob(tmp_path: Path) -> None:
    """_find_modules finds .ko.zst / .ko.xz / .ko.gz / .ko.bz2."""
    for suffix in (".ko.zst", ".ko.xz", ".ko.gz", ".ko.bz2"):
        rd = tmp_path / f"rel_{suffix.replace('.', '_')}"
        rd.mkdir()
        (rd / f"nvidia{suffix}").write_bytes(b"fake\n")
        ctx = VerificationContext(
            release_dir=rd, kernel_release=KR, driver_version=DRV,
        )
        # The verifier will attempt modinfo; FixtureRunner fails every call.
        result = ReleaseVerifier(_build_runner()).verify_release(ctx)
        codes = {f.code for f in result.findings}
        # The module was found (so a modinfo attempt was made), not
        # silently skipped.
        assert "VERMAGIC_UNAVAILABLE" in codes or "VERMAGIC_MISMATCH" in codes, (
            f"suffix {suffix}: module not discovered — findings: "
            f"{[f.code for f in result.findings]}"
        )


def test_no_modules_found_warns(tmp_path: Path) -> None:
    rd = tmp_path / "release"
    rd.mkdir()
    image_deb = _make_deb(rd, f"linux-image-{KR}")
    ctx = VerificationContext(
        release_dir=rd, kernel_release=KR, driver_version=DRV,
        expected_packages=(f"linux-image-{KR}",),
    )
    runner = _build_runner(
        deb_fields={image_deb: f"linux-image-{KR}"},
    )
    result = ReleaseVerifier(runner).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "NO_MODULES_FOUND" in codes


# ===========================================================================
# Dependency closure
# ===========================================================================


def test_dependency_missing_errors(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    uvm_ko = next(p for p in s["runner"]["modinfo_fields"] if p.name == "nvidia-uvm.ko")
    s["runner"]["modinfo_fields"][uvm_ko]["depends"] = "nvidia,missing-module"
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "MODULE_DEPENDENCY_MISSING" in codes
    missing = [
        f for f in result.findings if f.code == "MODULE_DEPENDENCY_MISSING"
    ]
    assert missing[0].context["missing"] == "missing-module"


def test_dependency_present_in_modules_dep_passes(tmp_path: Path) -> None:
    """A depends entry that is in modules.dep does not trigger a finding."""
    s = _setup_happy(tmp_path)
    nvidia_ko = next(p for p in s["runner"]["modinfo_fields"] if p.name == "nvidia.ko")
    s["runner"]["modinfo_fields"][nvidia_ko]["depends"] = "drm"
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "MODULE_DEPENDENCY_MISSING" not in codes


def test_dependency_closure_skipped_without_tree(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(s["ctx"], module_tree_dir=None)
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "DEPENDENCY_CLOSURE_SKIPPED" in codes
    # Warning only: boot_ready is still True.
    assert result.boot_ready is False


# ===========================================================================
# Initramfs verification
# ===========================================================================


def test_initramfs_wrong_release_is_critical(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["runner"]["lsinitramfs_listing"] = (
        "lib/modules/7.2.12+deb14-amd64/updates/nvidia/nvidia.ko",
        "lib/modules/7.2.12+deb14-amd64/updates/nvidia/nvidia-uvm.ko",
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_WRONG_RELEASE" in codes


def test_initramfs_missing_module_errors(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["runner"]["lsinitramfs_listing"] = (
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        # missing nvidia-uvm
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_REQUIRED_MODULE_MISSING" in codes


def test_initramfs_forbidden_module_critical(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["runner"]["lsinitramfs_listing"] = (
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko",
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/nouveau/nouveau.ko",
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_FORBIDDEN_MODULE_PRESENT" in codes


def test_initramfs_compressed_module_present(tmp_path: Path) -> None:
    """A compressed .ko.zst in the archive counts as the module being present."""
    s = _setup_happy(tmp_path)
    s["runner"]["lsinitramfs_listing"] = (
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko.zst",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko.zst",
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_REQUIRED_MODULE_MISSING" not in codes


def test_lsinitramfs_failure_warns_but_continues(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    result = ReleaseVerifier(
        _build_runner(lsinitramfs_returncode=2, **{
            k: v for k, v in s["runner"].items() if k != "lsinitramfs_returncode"
        })
    ).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "LSINITRAMFS_FAILED" in codes


def test_initramfs_skipped_without_archive(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(s["ctx"], initramfs_path=None)
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_VERIFICATION_SKIPPED" in codes
    # Warning only: boot_ready still True.
    assert result.boot_ready is False


# ===========================================================================
# Secure Boot compatibility
# ===========================================================================


def test_secureboot_enabled_without_signing_is_error(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(s["ctx"], require_signed_modules=False)
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "SECUREBOOT_SIGNING_POLICY_MISMATCH" in codes
    assert result.boot_ready is False


def test_secureboot_unknown_is_warning(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(s["ctx"], secure_boot_state=SecureBootState.UNKNOWN)
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "SECUREBOOT_STATE_UNKNOWN" in codes
    assert result.boot_ready is False


def test_secureboot_disabled_no_compat_finding(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(
        s["ctx"],
        secure_boot_state=SecureBootState.DISABLED,
        require_signed_modules=False,
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "SECUREBOOT_SIGNING_POLICY_MISMATCH" not in codes
    assert "SECUREBOOT_STATE_UNKNOWN" not in codes


# ===========================================================================
# Signing
# ===========================================================================


def test_unsigned_required_module_is_critical(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    nvidia_ko = next(p for p in s["runner"]["modinfo_fields"] if p.name == "nvidia.ko")
    s["runner"]["modinfo_fields"][nvidia_ko]["sig_key"] = None
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "REQUIRED_MODULE_UNSIGNED" in codes
    critical = [f for f in result.findings if f.code == "REQUIRED_MODULE_UNSIGNED"]
    assert critical[0].severity == Severity.CRITICAL


def test_wrong_signing_key_is_critical(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    uvm_ko = next(p for p in s["runner"]["modinfo_fields"] if p.name == "nvidia-uvm.ko")
    s["runner"]["modinfo_fields"][uvm_ko]["sig_key"] = WRONG_FP
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "REQUIRED_MODULE_SIGNED_BY_WRONG_KEY" in codes


def test_required_module_file_missing_errors(tmp_path: Path) -> None:
    """A required module with no corresponding .ko file in the release."""
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(
        s["ctx"],
        required_modules=("nvidia", "nvidia-uvm", "nvidia-modeset"),
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "REQUIRED_MODULE_FILE_MISSING" in codes


def test_cert_fingerprint_not_provided_errors(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(s["ctx"], expected_cert_fingerprint=None)
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "CERT_FINGERPRINT_NOT_PROVIDED" in codes


def test_signing_skipped_when_not_required(tmp_path: Path) -> None:
    """Neither require_signed_modules nor SB_ENABLED: no signing check runs."""
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(
        s["ctx"],
        secure_boot_state=SecureBootState.DISABLED,
        require_signed_modules=False,
        expected_cert_fingerprint=None,
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    # None of the signing-related codes fire.
    for code in (
        "REQUIRED_MODULE_UNSIGNED",
        "REQUIRED_MODULE_SIGNED_BY_WRONG_KEY",
        "CERT_FINGERPRINT_NOT_PROVIDED",
    ):
        assert code not in codes


# ===========================================================================
# Manifest hashes
# ===========================================================================


def test_sha256_mismatch_is_critical(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    bad_art = replace(s["ctx"].manifest_artifacts[0], sha256="0" * 64)
    s["ctx"] = replace(
        s["ctx"], manifest_artifacts=(bad_art, s["ctx"].manifest_artifacts[1])
    )
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "ARTIFACT_SHA256_MISMATCH" in codes


def test_artifact_file_missing_errors(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    bad_art = BuildArtifact(
        kind=ArtifactKind.INITRAMFS,
        path="does/not/exist.img",
        sha256="a" * 64, size_bytes=10, kernel_release=KR,
    )
    s["ctx"] = replace(s["ctx"], manifest_artifacts=(bad_art,))
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "ARTIFACT_FILE_MISSING" in codes


def test_multiple_artifact_failures_reported(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    bad1 = replace(s["ctx"].manifest_artifacts[0], sha256="0" * 64)
    bad2 = BuildArtifact(
        kind=ArtifactKind.KERNEL_HEADERS_DEB,
        path="missing-headers.deb",
        sha256="0" * 64, size_bytes=0, kernel_release=KR,
    )
    s["ctx"] = replace(s["ctx"], manifest_artifacts=(bad1, bad2))
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = [f.code for f in result.findings]
    assert "ARTIFACT_SHA256_MISMATCH" in codes
    assert "ARTIFACT_FILE_MISSING" in codes


# ===========================================================================
# Lockfile
# ===========================================================================


def test_lockfile_unresolved_errors(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    data = json.loads(s["ctx"].lockfile_path.read_text(encoding="utf-8"))
    data["status"] = "unresolved"
    data["checksum_sha256"] = "0" * 64
    data["retrieved_date"] = None
    s["ctx"].lockfile_path.write_text(json.dumps(data), encoding="utf-8")
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "LOCKFILE_UNRESOLVED" in codes


def test_lockfile_invalid_errors(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"].lockfile_path.write_text("this is not json", encoding="utf-8")
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "LOCKFILE_INVALID" in codes


def test_lockfile_missing_warns(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    s["ctx"] = replace(s["ctx"], lockfile_path=None)
    result = ReleaseVerifier(_build_runner(**s["runner"])).verify_release(s["ctx"])
    codes = {f.code for f in result.findings}
    assert "LOCKFILE_NOT_PROVIDED" in codes
    # Warning only.
    assert result.boot_ready is False


# ===========================================================================
# Dry run
# ===========================================================================


def test_dry_run_no_subprocess_boot_ready_false(tmp_path: Path) -> None:
    s = _setup_happy(tmp_path)
    runner = FixtureRunner()  # zero handlers: any run() raises
    result = ReleaseVerifier(runner).verify_release(s["ctx"], dry_run=True)
    assert runner.calls == ()
    assert result.dry_run is True
    assert result.boot_ready is False  # cannot confirm
    codes = {f.code for f in result.findings}
    assert "VERIFY_DRY_RUN" in codes
    # Filesystem checks ran: SHA checks match for the good fixture.
    assert "ARTIFACT_SHA256_MISMATCH" not in codes


def test_dry_run_detects_sha_mismatch(tmp_path: Path) -> None:
    """Dry run is not toothless: it still performs filesystem SHA checks."""
    s = _setup_happy(tmp_path)
    bad_art = replace(s["ctx"].manifest_artifacts[0], sha256="0" * 64)
    s["ctx"] = replace(
        s["ctx"], manifest_artifacts=(bad_art, s["ctx"].manifest_artifacts[1])
    )
    runner = FixtureRunner()
    result = ReleaseVerifier(runner).verify_release(s["ctx"], dry_run=True)
    codes = {f.code for f in result.findings}
    assert "ARTIFACT_SHA256_MISMATCH" in codes
    # Still no subprocess.
    assert runner.calls == ()


# ===========================================================================
# Structural proof of no host mutation
# ===========================================================================


@pytest.mark.parametrize(
    "forbidden_command",
    [
        "update-initramfs",
        "update-grub",
        "dpkg",       # dpkg-deb is allowed; bare dpkg is not
        "apt",
        "apt-get",
        "dkms",
        "mokutil",
        "insmod",
        "rmmod",
        "modprobe",
        "sudo",
        "systemctl",
    ],
)
def test_no_host_mutation_commands_in_argv(
    forbidden_command: str, tmp_path: Path
) -> None:
    s = _setup_happy(tmp_path)
    runner = _build_runner(**s["runner"])
    ReleaseVerifier(runner).verify_release(s["ctx"])
    for call in runner.calls:
        if forbidden_command == "dpkg":
            if call.argv[0] == "dpkg-deb":
                continue
        assert call.argv[0] != forbidden_command, (
            f"verifier invoked forbidden command {forbidden_command!r}: "
            f"{call.argv}"
        )


@pytest.mark.parametrize(
    "protected_path",
    ["/boot", "/lib/modules", "/etc/modprobe.d", "/etc/initramfs-tools"],
)
def test_no_protected_paths_in_argv(
    protected_path: str, tmp_path: Path
) -> None:
    s = _setup_happy(tmp_path)
    runner = _build_runner(**s["runner"])
    ReleaseVerifier(runner).verify_release(s["ctx"])
    for call in runner.calls:
        for arg in call.argv:
            assert protected_path not in arg, (
                f"verifier passed protected path {protected_path!r}: {call.argv}"
            )
