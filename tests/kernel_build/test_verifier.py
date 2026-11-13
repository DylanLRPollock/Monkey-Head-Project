"""Tests for huey.kernel_build.verifier (Step 19; Step 43 expands).

All tests offline. ``dpkg-deb``, ``modinfo``, and ``lsinitramfs`` are
simulated via ``FixtureRunner``. Every test builds a small release tree
under ``tmp_path`` so SHA-256 checks are genuine and fast.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

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


# ---------------------------------------------------------------------------
# FixtureRunner
# ---------------------------------------------------------------------------


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
        raise RunnerError(f"no handler for argv={spec.argv!r}")

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


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------

KR = "7.2.15-huey1"
DRV = "580.196.07"
FP = "13:FE:C2:ED:A1:40:CE:70:1A:75:91:E5:4C:1F:5F:DA:BD:17:57:A9:AA:BB:CC:DD:EE:FF:00:11:22:33:44:55"


def _make_deb(path: Path, package: str, version: str = "7.2.15-huey1-1") -> Path:
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
) -> FixtureRunner:
    """Build a FixtureRunner with configurable responses keyed by path."""
    deb_fields = deb_fields or {}
    modinfo_fields = modinfo_fields or {}
    r = FixtureRunner()

    def _deb(spec):
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


def _setup_happy(tmp_path: Path) -> tuple[VerificationContext, dict]:
    """Build a complete release tree and the matching FixtureRunner."""
    rd = tmp_path / "release"
    rd.mkdir()

    image_deb = _make_deb(rd / f"linux-image-{KR}_1_amd64.deb", f"linux-image-{KR}")
    headers_deb = _make_deb(rd / f"linux-headers-{KR}_1_amd64.deb", f"linux-headers-{KR}")

    nvidia_ko = _make_module(rd / "modules" / "nvidia.ko", depends="")
    uvm_ko = _make_module(rd / "modules" / "nvidia-uvm.ko", depends="nvidia")

    initramfs = rd / f"initramfs-{KR}"
    initramfs.write_bytes(b"fake initramfs archive\n")

    lock = tmp_path / "source.lock.json"
    import json as _json
    lock.write_text(_json.dumps({
        "schema_version": 1, "status": "pinned",
        "source_type": "debian-linux-source", "package_name": "linux-source-7.2",
        "version": "7.2.15-1", "archive_filename": "linux-source-7.2.deb",
        "origin_url": "https://deb.debian.org/x", "checksum_sha256": "a" * 64,
        "retrieved_date": "2026-11-12", "license": "GPL-2.0-only",
        "profile_revision": 1, "notes": "",
    }), encoding="utf-8")

    module_tree = tmp_path / "tree"
    (module_tree / "kernel").mkdir(parents=True)
    (module_tree / "modules.dep").write_text(
        "kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko:\n"
        "kernel/drivers/gpu/drm/drm.ko:\n",
        encoding="utf-8",
    )

    def _sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

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
        expected_packages=(
            f"linux-image-{KR}",
            f"linux-headers-{KR}",
        ),
        required_modules=("nvidia", "nvidia-uvm"),
        module_tree_dir=module_tree,
        initramfs_path=initramfs,
        manifest_artifacts=manifest,
        require_signed_modules=True,
        expected_cert_fingerprint=FP,
        lockfile_path=lock,
        secure_boot_state=SecureBootState.ENABLED,
    )

    deb_fields = {
        image_deb: f"linux-image-{KR}",
        headers_deb: f"linux-headers-{KR}",
    }
    modinfo_fields = {
        nvidia_ko: {
            "vermagic": f"{KR} SMP mod_unload modversions",
            "version": DRV, "sig_key": FP, "depends": "",
        },
        uvm_ko: {
            "vermagic": f"{KR} SMP mod_unload modversions",
            "version": DRV, "sig_key": FP, "depends": "nvidia",
        },
    }
    listing = (
        f"lib/modules/{KR}/modules.dep",
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko",
    )
    runner_kwargs = {
        "deb_fields": deb_fields,
        "modinfo_fields": modinfo_fields,
        "lsinitramfs_listing": listing,
    }
    return ctx, runner_kwargs


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_all_checks_pass(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    assert result.static_checks_passed is True, result.findings
    assert result.boot_ready is True
    assert set(result.host_checks_required) == set(HOST_CHECKS)
    assert not result.has_errors()


def test_result_is_json_serializable(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    payload = json.dumps(result.to_dict())
    assert '"boot_ready": true' in payload
    assert "host_checks" in payload or "host_checks_required" in payload


def test_missing_release_dir_errors(tmp_path: Path) -> None:
    ctx = VerificationContext(
        release_dir=tmp_path / "does-not-exist",
        kernel_release=KR, driver_version=DRV,
    )
    result = ReleaseVerifier(_build_runner()).verify_release(ctx)
    assert result.boot_ready is False
    codes = {f.code for f in result.findings}
    assert "RELEASE_DIR_MISSING" in codes


# ---------------------------------------------------------------------------
# Package verification
# ---------------------------------------------------------------------------


def test_missing_expected_package_errors(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    runner_kwargs["deb_fields"] = {
        k: v for k, v in runner_kwargs["deb_fields"].items()
    }
    # Clear one package so it can't be matched
    ctx = VerificationContext(
        **{**ctx.__dict__,
           "expected_packages": (
               f"linux-image-{KR}", f"linux-headers-{KR}", "linux-unknown",
           )},
    ) if hasattr(ctx, "__dict__") else ctx
    # Use dataclasses.replace for immutability
    from dataclasses import replace
    ctx = replace(ctx, expected_packages=(
        f"linux-image-{KR}", f"linux-headers-{KR}", "linux-unknown",
    ))
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "EXPECTED_PACKAGE_MISSING" in codes
    assert result.boot_ready is False


def test_no_debs_in_release_errors(tmp_path: Path) -> None:
    rd = tmp_path / "release"; rd.mkdir()
    ctx = VerificationContext(
        release_dir=rd, kernel_release=KR, driver_version=DRV,
        expected_packages=(f"linux-image-{KR}",),
    )
    result = ReleaseVerifier(_build_runner()).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "NO_DEBS_IN_RELEASE" in codes


# ---------------------------------------------------------------------------
# Module metadata
# ---------------------------------------------------------------------------


def test_vermagic_mismatch_is_critical(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    # Override one module's vermagic
    nvidia_ko = next(p for p in runner_kwargs["modinfo_fields"] if p.name == "nvidia.ko")
    runner_kwargs["modinfo_fields"][nvidia_ko]["vermagic"] = (
        "7.2.12+deb14-amd64 SMP mod_unload modversions"
    )
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "VERMAGIC_MISMATCH" in codes
    critical = [f for f in result.findings if f.code == "VERMAGIC_MISMATCH"]
    assert critical[0].severity == Severity.CRITICAL


def test_module_version_mismatch_errors(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    uvm_ko = next(p for p in runner_kwargs["modinfo_fields"] if p.name == "nvidia-uvm.ko")
    runner_kwargs["modinfo_fields"][uvm_ko]["version"] = "550.100.00"
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "MODULE_VERSION_MISMATCH" in codes
    assert result.boot_ready is False


# ---------------------------------------------------------------------------
# Dependency closure
# ---------------------------------------------------------------------------


def test_dependency_missing_errors(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    uvm_ko = next(p for p in runner_kwargs["modinfo_fields"] if p.name == "nvidia-uvm.ko")
    runner_kwargs["modinfo_fields"][uvm_ko]["depends"] = "nvidia,missing-module"
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "MODULE_DEPENDENCY_MISSING" in codes


def test_dependency_closure_skipped_without_tree(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    from dataclasses import replace
    ctx = replace(ctx, module_tree_dir=None)
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "DEPENDENCY_CLOSURE_SKIPPED" in codes
    # Missing dependency closure must block release promotion.
    assert result.boot_ready is False


# ---------------------------------------------------------------------------
# Initramfs
# ---------------------------------------------------------------------------


def test_initramfs_wrong_release_is_critical(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    runner_kwargs["lsinitramfs_listing"] = (
        "lib/modules/7.2.12+deb14-amd64/updates/nvidia/nvidia.ko",
        "lib/modules/7.2.12+deb14-amd64/updates/nvidia/nvidia-uvm.ko",
    )
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_WRONG_RELEASE" in codes


def test_initramfs_missing_module_errors(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    runner_kwargs["lsinitramfs_listing"] = (
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        # missing nvidia-uvm
    )
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_REQUIRED_MODULE_MISSING" in codes


def test_initramfs_forbidden_module_critical(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    runner_kwargs["lsinitramfs_listing"] = (
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko",
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/nouveau/nouveau.ko",
    )
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_FORBIDDEN_MODULE_PRESENT" in codes


# ---------------------------------------------------------------------------
# Secure Boot
# ---------------------------------------------------------------------------


def test_secureboot_enabled_without_signing_is_error(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    from dataclasses import replace
    ctx = replace(ctx, require_signed_modules=False)
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "SECUREBOOT_SIGNING_POLICY_MISMATCH" in codes
    assert result.boot_ready is False


def test_secureboot_unknown_is_warning(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    from dataclasses import replace
    ctx = replace(ctx, secure_boot_state=SecureBootState.UNKNOWN)
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "SECUREBOOT_STATE_UNKNOWN" in codes
    assert result.boot_ready is False  # unknown boot state cannot be promoted


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------


def test_unsigned_required_module_is_critical(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    nvidia_ko = next(p for p in runner_kwargs["modinfo_fields"] if p.name == "nvidia.ko")
    runner_kwargs["modinfo_fields"][nvidia_ko]["sig_key"] = None
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "REQUIRED_MODULE_UNSIGNED" in codes
    critical = [f for f in result.findings if f.code == "REQUIRED_MODULE_UNSIGNED"]
    assert critical[0].severity == Severity.CRITICAL


def test_wrong_signing_key_is_critical(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    uvm_ko = next(p for p in runner_kwargs["modinfo_fields"] if p.name == "nvidia-uvm.ko")
    runner_kwargs["modinfo_fields"][uvm_ko]["sig_key"] = (
        "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99:"
        "AA:BB:CC:DD:EE:FF:00:11:22:33:44:55:66:77:88:99"
    )
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "REQUIRED_MODULE_SIGNED_BY_WRONG_KEY" in codes


# ---------------------------------------------------------------------------
# Manifest hashes
# ---------------------------------------------------------------------------


def test_sha256_mismatch_critical(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    from dataclasses import replace
    image_art = ctx.manifest_artifacts[0]
    bad_art = BuildArtifact(
        kind=image_art.kind, path=image_art.path,
        sha256="0" * 64, size_bytes=image_art.size_bytes,
        kernel_release=image_art.kernel_release,
    )
    ctx = replace(ctx, manifest_artifacts=(bad_art, ctx.manifest_artifacts[1]))
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "ARTIFACT_SHA256_MISMATCH" in codes


def test_artifact_file_missing(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    from dataclasses import replace
    bad_art = BuildArtifact(
        kind=ArtifactKind.INITRAMFS,
        path="does/not/exist.img",
        sha256="a" * 64, size_bytes=10, kernel_release=KR,
    )
    ctx = replace(ctx, manifest_artifacts=(bad_art,))
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "ARTIFACT_FILE_MISSING" in codes


# ---------------------------------------------------------------------------
# Lockfile
# ---------------------------------------------------------------------------


def test_lockfile_unresolved_errors(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    import json as _json
    lock_path = ctx.lockfile_path
    data = _json.loads(lock_path.read_text(encoding="utf-8"))
    data["status"] = "unresolved"
    data["checksum_sha256"] = "0" * 64
    data["retrieved_date"] = None
    lock_path.write_text(_json.dumps(data), encoding="utf-8")
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "LOCKFILE_UNRESOLVED" in codes


def test_lockfile_missing_warns(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    from dataclasses import replace
    ctx = replace(ctx, lockfile_path=None)
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    codes = {f.code for f in result.findings}
    assert "LOCKFILE_NOT_PROVIDED" in codes
    # A missing source lock is a blocking verification failure.
    assert result.boot_ready is False


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


def test_dry_run_no_subprocess_boot_ready_false(tmp_path: Path) -> None:
    ctx, _ = _setup_happy(tmp_path)
    runner = FixtureRunner()  # no handlers
    result = ReleaseVerifier(runner).verify_release(ctx, dry_run=True)
    assert runner.calls == ()
    assert result.dry_run is True
    assert result.boot_ready is False  # cannot confirm
    codes = {f.code for f in result.findings}
    assert "VERIFY_DRY_RUN" in codes
    # Filesystem checks still ran (hashes match for good fixture)
    assert "ARTIFACT_SHA256_MISMATCH" not in codes


# ---------------------------------------------------------------------------
# Host check list
# ---------------------------------------------------------------------------


def test_host_checks_empty_when_not_ready(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    nvidia_ko = next(p for p in runner_kwargs["modinfo_fields"] if p.name == "nvidia.ko")
    runner_kwargs["modinfo_fields"][nvidia_ko]["vermagic"] = "wrong"
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    assert result.host_checks_required == ()


def test_host_checks_populated_when_ready(tmp_path: Path) -> None:
    ctx, runner_kwargs = _setup_happy(tmp_path)
    result = ReleaseVerifier(_build_runner(**runner_kwargs)).verify_release(ctx)
    assert result.boot_ready is True
    assert set(result.host_checks_required) == set(HOST_CHECKS)


# Fail-closed release verification: incomplete checks must not promote.
def test_missing_packages_cannot_be_boot_ready(tmp_path: Path) -> None:
    ctx, opts = _setup_happy(tmp_path)
    from dataclasses import replace
    ctx = replace(ctx, expected_packages=())
    result = ReleaseVerifier(_build_runner(**opts)).verify_release(ctx)
    assert not result.boot_ready
    assert "NO_EXPECTED_PACKAGES" in {f.code for f in result.findings}


def test_missing_manifest_cannot_be_boot_ready(tmp_path: Path) -> None:
    ctx, opts = _setup_happy(tmp_path)
    from dataclasses import replace
    ctx = replace(ctx, manifest_artifacts=())
    result = ReleaseVerifier(_build_runner(**opts)).verify_release(ctx)
    assert not result.boot_ready
    assert "MANIFEST_ARTIFACTS_MISSING" in {f.code for f in result.findings}


def test_missing_required_modules_cannot_be_boot_ready(tmp_path: Path) -> None:
    ctx, opts = _setup_happy(tmp_path)
    from dataclasses import replace
    ctx = replace(ctx, required_modules=())
    result = ReleaseVerifier(_build_runner(**opts)).verify_release(ctx)
    assert not result.boot_ready
    assert "REQUIRED_MODULES_MISSING" in {f.code for f in result.findings}


def test_dpkg_deb_bare_field_value_is_supported(tmp_path: Path) -> None:
    ctx, opts = _setup_happy(tmp_path)
    rd = ctx.release_dir
    deb = next(rd.glob("linux-image-*.deb"))
    fake = FixtureRunner()
    fake.on(_is_dpkg_deb, lambda spec: _ok(spec, stdout=b"linux-image-7.2.15-huey1\n"))
    assert ReleaseVerifier(fake)._query_deb_field(deb, "Package") == "linux-image-7.2.15-huey1"


def test_artifact_symlink_escape_is_blocked(tmp_path: Path) -> None:
    ctx, opts = _setup_happy(tmp_path)
    from dataclasses import replace
    link = ctx.release_dir / "secret.txt"
    real = tmp_path / "secret.txt"
    real.write_text("do not read", encoding="utf-8")
    link.symlink_to(real)
    art = replace(ctx.manifest_artifacts[0], path="secret.txt")
    ctx = replace(ctx, manifest_artifacts=(art,))
    result = ReleaseVerifier(_build_runner(**opts)).verify_release(ctx)
    assert not result.boot_ready
    assert "ARTIFACT_PATH_UNSAFE" in {f.code for f in result.findings}
