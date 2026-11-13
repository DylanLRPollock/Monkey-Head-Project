"""Tests for huey.kernel_build.nvidia_builder (Step 14; Step 40 expands)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from huey.kernel_build.models import (
    ArtifactKind,
    CommandResult,
    ModuleFlavor,
    Severity,
)
from huey.kernel_build.nvidia_builder import (
    NvidiaBuilder,
    NvidiaBuildResult,
    OPTIONAL_MODULES,
    REQUIRED_MODULES,
)
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerResult,
    RunnerTimeout,
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


def _is_make_modules(spec: CommandSpec) -> bool:
    return spec.argv[0] == "make" and "modules" in spec.argv


def _is_modinfo_vermagic(spec: CommandSpec) -> bool:
    return (
        spec.argv[0] == "modinfo"
        and "-F" in spec.argv
        and "vermagic" in spec.argv
    )


def _is_modinfo_version(spec: CommandSpec) -> bool:
    return (
        spec.argv[0] == "modinfo"
        and "-F" in spec.argv
        and "version" in spec.argv
    )


# ---------------------------------------------------------------------------
# Fixture setup
# ---------------------------------------------------------------------------


def _make_headers(tmp_path: Path) -> Path:
    headers = tmp_path / "headers"
    (headers / "include" / "generated").mkdir(parents=True)
    (headers / "Makefile").write_text("# fake headers\n", encoding="utf-8")
    return headers


def _make_dkms_source(
    tmp_path: Path,
    *,
    version: str = "580.196.07",
    modules: tuple[str, ...] = ("nvidia", "nvidia-uvm", "nvidia-modeset", "nvidia-drm"),
    makefile: bool = True,
    dkms_conf: bool = True,
) -> Path:
    src = tmp_path / "dkms-source"
    src.mkdir(exist_ok=True)
    if dkms_conf:
        (src / "dkms.conf").write_text(
            f'PACKAGE_NAME="nvidia"\nPACKAGE_VERSION="{version}"\n',
            encoding="utf-8",
        )
    if makefile:
        (src / "Makefile").write_text("# fake nvidia Makefile\n", encoding="utf-8")
    # Simulate built .ko files at known paths.
    for mod in modules:
        ko = src / mod / f"{mod}.ko"
        ko.parent.mkdir(parents=True, exist_ok=True)
        ko.write_bytes(f"fake ko for {mod} {version}\n".encode())
    return src


def _build_runner(
    *,
    kernel_release: str = "7.2.15-huey1",
    driver_version: str = "580.196.07",
    vermagic: str | None = None,
    module_version: str | None = None,
    make_returncode: int = 0,
    make_timeout: bool = False,
    modinfo_vermagic_returncode: int = 0,
    modinfo_version_returncode: int = 0,
    create_modules: tuple[str, ...] = REQUIRED_MODULES + OPTIONAL_MODULES,
    dkms_source: Path | None = None,
) -> FixtureRunner:
    r = FixtureRunner()
    vermagic_value = vermagic if vermagic is not None else kernel_release
    version_value = module_version if module_version is not None else driver_version

    def _make(spec):
        if make_timeout:
            raise RunnerTimeout("timeout")
        if make_returncode != 0:
            return _fail(spec, make_returncode)
        if dkms_source is not None:
            for mod in create_modules:
                ko = spec.cwd / mod / f"{mod}.ko"
                ko.parent.mkdir(parents=True, exist_ok=True)
                ko.write_bytes(f"built {mod}\n".encode())
        return _ok(spec)

    def _mv(spec):
        if modinfo_vermagic_returncode != 0:
            return _fail(spec, modinfo_vermagic_returncode)
        return _ok(spec, stdout=f"{vermagic_value} SMP mod_unload modversions\n".encode())

    def _mver(spec):
        if modinfo_version_returncode != 0:
            return _fail(spec, modinfo_version_returncode)
        return _ok(spec, stdout=f"{version_value}\n".encode())

    r.on(_is_make_modules, _make)
    r.on(_is_modinfo_vermagic, _mv)
    r.on(_is_modinfo_version, _mver)
    return r


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_stages_required_and_optional_modules(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    out = tmp_path / "out"
    result = NvidiaBuilder(
        _build_runner(dkms_source=src)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=out,
        dkms_source_dir=src,
    )
    assert result.has_errors() is False, result.findings
    assert result.kernel_release == "7.2.15-huey1"
    assert result.driver_version == "580.196.07"
    assert result.module_flavor == ModuleFlavor.PROPRIETARY
    for mod in REQUIRED_MODULES:
        assert mod in result.module_artifacts, f"missing required module {mod}"
        art = result.module_artifacts[mod]
        assert art.kind == ArtifactKind.NVIDIA_MODULE
        assert art.kernel_release == "7.2.15-huey1"
        assert len(art.sha256) == 64
        assert art.size_bytes > 0
        assert not Path(art.path).is_absolute()
    for mod in OPTIONAL_MODULES:
        assert mod in result.module_artifacts


def test_happy_path_staged_files_exist_on_disk(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    out = tmp_path / "out"
    result = NvidiaBuilder(
        _build_runner(dkms_source=src)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=out,
        dkms_source_dir=src,
    )
    for mod, art in result.module_artifacts.items():
        staged = out / art.path
        assert staged.is_file(), f"staged file missing for {mod}: {staged}"


def test_result_is_json_serializable(tmp_path: Path) -> None:
    import json
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    payload = json.dumps(result.to_dict())
    assert "nvidia-uvm" in payload
    assert "580.196.07" in payload
    assert "7.2.15-huey1" in payload


# ---------------------------------------------------------------------------
# Module flavor rejection
# ---------------------------------------------------------------------------


def test_open_flavor_rejected(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.OPEN,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "OPEN_MODULE_REJECTED" in codes
    assert result.has_errors() is True
    assert result.module_artifacts == {}


# ---------------------------------------------------------------------------
# Source resolution
# ---------------------------------------------------------------------------


def test_missing_source_without_discovery_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    result = NvidiaBuilder(_build_runner()).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_SOURCE_NOT_FOUND" in codes


def test_missing_source_dir_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    result = NvidiaBuilder(_build_runner()).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=tmp_path / "does-not-exist",
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_SOURCE_DIR_MISSING" in codes


def test_dkms_version_mismatch_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path, version="550.100.00")
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_VERSION_MISMATCH" in codes


def test_dkms_conf_missing_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path, dkms_conf=False)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_CONF_MISSING" in codes


def test_dkms_makefile_missing_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path, makefile=False)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_MAKEFILE_MISSING" in codes


def test_system_dkms_discovery_disabled_by_default(tmp_path: Path) -> None:
    """Without the opt-in, system discovery is not attempted."""
    headers = _make_headers(tmp_path)
    result = NvidiaBuilder(_build_runner()).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        allow_system_dkms_discovery=False,
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_SOURCE_NOT_FOUND" in codes


# ---------------------------------------------------------------------------
# Headers validation
# ---------------------------------------------------------------------------


def test_headers_makefile_missing_errors(tmp_path: Path) -> None:
    headers = tmp_path / "bad-headers"
    (headers / "include" / "generated").mkdir(parents=True)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "HEADERS_MAKEFILE_MISSING" in codes


def test_headers_generated_missing_errors(tmp_path: Path) -> None:
    headers = tmp_path / "bad-headers"
    headers.mkdir()
    (headers / "Makefile").write_text("# fake\n", encoding="utf-8")
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "HEADERS_GENERATED_MISSING" in codes


# ---------------------------------------------------------------------------
# Build failures
# ---------------------------------------------------------------------------


def test_make_failure_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, make_returncode=2)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "NVIDIA_BUILD_FAILED" in codes


def test_make_timeout_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, make_timeout=True)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "NVIDIA_BUILD_TIMEOUT" in codes


def test_no_modules_built_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path, modules=())  # no .ko files
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, create_modules=())
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "NO_MODULES_BUILT" in codes


# ---------------------------------------------------------------------------
# Vermagic mismatch
# ---------------------------------------------------------------------------


def test_vermagic_mismatch_is_critical(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, vermagic="7.2.12-huey1")
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "VERMAGIC_MISMATCH" in codes
    critical = [f for f in result.findings if f.code == "VERMAGIC_MISMATCH"]
    assert critical[0].severity == Severity.CRITICAL
    assert "7.2.12-huey1" in critical[0].message
    assert "7.2.15-huey1" in critical[0].message


def test_vermagic_query_failure_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, modinfo_vermagic_returncode=2)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "VERMAGIC_QUERY_FAILED" in codes


# ---------------------------------------------------------------------------
# Module version mismatch
# ---------------------------------------------------------------------------


def test_module_version_mismatch_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, module_version="550.100.00")
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "MODULE_VERSION_MISMATCH" in codes


# ---------------------------------------------------------------------------
# Required module presence
# ---------------------------------------------------------------------------


def test_missing_uvm_module_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(
        tmp_path, modules=("nvidia", "nvidia-modeset", "nvidia-drm")
    )
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, create_modules=("nvidia", "nvidia-modeset", "nvidia-drm"))
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "REQUIRED_MODULE_MISSING" in codes
    assert "nvidia-uvm" not in result.module_artifacts


# ---------------------------------------------------------------------------
# Secure Boot
# ---------------------------------------------------------------------------


def test_secure_boot_enabled_records_warning(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
        secure_boot_enabled=True,
    )
    warning_codes = {f.code for f in result.findings if f.severity == Severity.WARNING}
    assert "SECUREBOOT_SIGNING_DEFERRED" in warning_codes
    # Not a blocking error by itself.
    assert all(
        f.code != "SECUREBOOT_SIGNING_DEFERRED"
        or f.severity != Severity.ERROR
        for f in result.findings
    )


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


def test_dry_run_no_io_no_subprocess(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    runner = FixtureRunner()  # no handlers; any run raises
    result = NvidiaBuilder(runner).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
        dry_run=True,
    )
    assert result.dry_run is True
    assert runner.calls == ()
    assert not (tmp_path / "out").exists()
    assert result.module_artifacts == {}
    codes = {f.code for f in result.findings}
    assert "NVIDIA_BUILD_DRY_RUN" in codes


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_stale_staging_is_replaced(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    out = tmp_path / "out"
    staging = out / "nvidia-580.196.07-7.2.15-huey1"
    staging.mkdir(parents=True)
    (staging / "stale.ko").write_bytes(b"stale")

    result = NvidiaBuilder(
        _build_runner(dkms_source=src)
    ).build(
        kernel_release="7.2.15-huey1",
        driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=out,
        dkms_source_dir=src,
    )
    assert not (staging / "stale.ko").exists()
    assert result.has_errors() is False

# Security regression tests for staging and direct builder entry points.

def test_nvidia_builder_preserves_vendor_source_tree(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    original = {str(p.relative_to(src)): p.read_bytes() for p in src.rglob("*") if p.is_file()}
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release="7.2.15-huey1", driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out", dkms_source_dir=src,
    )
    assert not result.has_errors(), result.findings
    assert original == {str(p.relative_to(src)): p.read_bytes() for p in src.rglob("*") if p.is_file()}
    assert (tmp_path / "out" / "nvidia-580.196.07-7.2.15-huey1" / "vendor-source").is_dir()


def test_nvidia_rejects_protected_output(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(FixtureRunner()).build(
        kernel_release="7.2.15-huey1", driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=Path("/boot/huey"), dkms_source_dir=src,
    )
    assert "PROTECTED_HOST_PATH" in {f.code for f in result.findings}


def test_nvidia_rejects_overlapping_stage(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(FixtureRunner()).build(
        kernel_release="7.2.15-huey1", driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=src / "build", dkms_source_dir=src,
    )
    assert "UNSAFE_OUTPUT_OVERLAP" in {f.code for f in result.findings}


def test_nvidia_rejects_escaping_identifier(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(FixtureRunner()).build(
        kernel_release="../../etc", driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out", dkms_source_dir=src,
    )
    assert "UNSAFE_BUILD_IDENTIFIER" in {f.code for f in result.findings}


def test_nvidia_rejects_untrusted_source_symlink(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    (src / "outside").symlink_to("/etc")
    result = NvidiaBuilder(FixtureRunner()).build(
        kernel_release="7.2.15-huey1", driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out", dkms_source_dir=src,
    )
    assert "SOURCE_STAGING_FAILED" in {f.code for f in result.findings}


def test_nvidia_workspace_relative_output(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    root = tmp_path / "approved"
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release="7.2.15-huey1", driver_version="580.196.07",
        module_flavor=ModuleFlavor.PROPRIETARY, headers_dir=headers,
        output_dir=Path("modules"), workspace_root=root, dkms_source_dir=src,
    )
    assert not result.has_errors(), result.findings
    assert (root / "modules").is_dir()
