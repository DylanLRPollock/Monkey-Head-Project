"""Canonical test suite for huey.kernel_build.nvidia_builder (Step 40).

Step 14 landed an initial suite proving each branch worked. This file
expands that suite to the full contract required by the handoff.

Notable design notes:
* The builder produces uncompressed .ko files (make modules output); it
  does not accept compressed forms. Compression happens later.
* ``_run_build`` in Step 14 returns an error result with
  driver_version="" on failure; tests do not assert the driver_version
  field on failure paths (they assert the finding code).
* All subprocess execution goes through FixtureRunner; make and modinfo
  are simulated in pure Python.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

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


# ===========================================================================
# Fixture setup
# ===========================================================================


KR = "7.2.15-huey1"
DRV = "580.196.07"


def _make_headers(tmp_path: Path, *, with_makefile: bool = True, with_generated: bool = True) -> Path:
    headers = tmp_path / "headers"
    headers.mkdir(exist_ok=True)
    if with_generated:
        (headers / "include" / "generated").mkdir(parents=True, exist_ok=True)
    else:
        (headers / "include").mkdir(parents=True, exist_ok=True)
    if with_makefile:
        (headers / "Makefile").write_text("# fake headers\n", encoding="utf-8")
    return headers


def _make_dkms_source(
    tmp_path: Path,
    *,
    version: str = DRV,
    modules: tuple[str, ...] = REQUIRED_MODULES + OPTIONAL_MODULES,
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
    for mod in modules:
        ko = src / mod / f"{mod}.ko"
        ko.parent.mkdir(parents=True, exist_ok=True)
        ko.write_bytes(f"fake ko for {mod} {version}\n".encode())
    return src


def _build_runner(
    *,
    kernel_release: str = KR,
    driver_version: str = DRV,
    vermagic: str | None = None,
    module_version: str | None = None,
    make_returncode: int = 0,
    make_timeout: bool = False,
    make_launch_fails: bool = False,
    modinfo_vermagic_returncode: int = 0,
    modinfo_vermagic_empty: bool = False,
    modinfo_version_returncode: int = 0,
    create_modules: tuple[str, ...] = REQUIRED_MODULES + OPTIONAL_MODULES,
    dkms_source: Path | None = None,
) -> FixtureRunner:
    r = FixtureRunner()
    vermagic_value = vermagic if vermagic is not None else kernel_release
    version_value = module_version if module_version is not None else driver_version

    def _make(spec):
        if make_launch_fails:
            raise RunnerError("make not found")
        if make_timeout:
            raise RunnerTimeout("timeout")
        if make_returncode != 0:
            return _fail(spec, make_returncode)
        if dkms_source is not None:
            # Builder intentionally compiles in a private vendor-source copy,
            # never the operator's original DKMS source tree.
            for mod in create_modules:
                ko = spec.cwd / mod / f"{mod}.ko"
                ko.parent.mkdir(parents=True, exist_ok=True)
                ko.write_bytes(f"built {mod}\n".encode())
        return _ok(spec)

    def _mv(spec):
        if modinfo_vermagic_returncode != 0:
            return _fail(spec, modinfo_vermagic_returncode)
        if modinfo_vermagic_empty:
            return _ok(spec, stdout=b"\n")
        return _ok(spec, stdout=f"{vermagic_value} SMP mod_unload modversions\n".encode())

    def _mver(spec):
        if modinfo_version_returncode != 0:
            return _fail(spec, modinfo_version_returncode)
        return _ok(spec, stdout=f"{version_value}\n".encode())

    r.on(_is_make_modules, _make)
    r.on(_is_modinfo_vermagic, _mv)
    r.on(_is_modinfo_version, _mver)
    return r


# ===========================================================================
# Happy path
# ===========================================================================


def test_happy_path_stages_all_modules(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    out = tmp_path / "out"
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=out,
        dkms_source_dir=src,
    )
    assert result.has_errors() is False, result.findings
    assert result.kernel_release == KR
    assert result.driver_version == DRV
    assert result.module_flavor == ModuleFlavor.PROPRIETARY
    for mod in REQUIRED_MODULES:
        assert mod in result.module_artifacts, f"missing {mod}"
        art = result.module_artifacts[mod]
        assert art.kind == ArtifactKind.NVIDIA_MODULE
        assert art.kernel_release == KR
        assert len(art.sha256) == 64
        assert art.size_bytes > 0
        assert not Path(art.path).is_absolute()
    for mod in OPTIONAL_MODULES:
        assert mod in result.module_artifacts


def test_happy_path_staged_files_on_disk(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    out = tmp_path / "out"
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=out,
        dkms_source_dir=src,
    )
    for mod, art in result.module_artifacts.items():
        staged = out / art.path
        assert staged.is_file(), f"staged file missing for {mod}: {staged}"
        assert hashlib.sha256(staged.read_bytes()).hexdigest() == art.sha256


def test_result_is_json_serializable(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    payload = json.dumps(result.to_dict())
    assert "nvidia-uvm" in payload
    assert DRV in payload
    assert KR in payload


# ===========================================================================
# Command-plan verification
# ===========================================================================


def test_make_modules_invocation_shape(tmp_path: Path) -> None:
    """make modules -j4 with the right env vars."""
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    runner = _build_runner(dkms_source=src)
    NvidiaBuilder(runner).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    make_calls = [c for c in runner.calls if _is_make_modules(c)]
    assert len(make_calls) == 1
    spec = make_calls[0]
    assert spec.argv == ("make", "modules", "-j4")
    assert spec.cwd == (tmp_path / "out" / f"nvidia-{DRV}-{KR}" / "vendor-source").resolve()
    assert spec.cwd != src.resolve()
    env = spec.env_overrides
    assert env["KERNELRELEASE"] == KR
    headers_resolved = str(headers.resolve())
    assert env["KERNEL_DIR"] == headers_resolved
    assert env["KERNEL_SOURCE"] == headers_resolved
    assert env["SYSSRC"] == headers_resolved
    assert env["SYSOUT"] == headers_resolved


# ===========================================================================
# Source discovery
# ===========================================================================


def test_explicit_dkms_source_dir_used(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
        allow_system_dkms_discovery=False,
    )
    assert result.has_errors() is False
    assert result.source_dir == src.resolve()


def test_missing_source_with_discovery_disabled_errors(tmp_path: Path) -> None:
    """No dkms_source_dir and no discovery → DKMS_SOURCE_NOT_FOUND."""
    headers = _make_headers(tmp_path)
    result = NvidiaBuilder(_build_runner()).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        allow_system_dkms_discovery=False,
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_SOURCE_NOT_FOUND" in codes


def test_missing_source_with_discovery_enabled_errors(tmp_path: Path) -> None:
    """Discovery is attempted but nothing exists on a test host → DKMS_SOURCE_NOT_FOUND."""
    headers = _make_headers(tmp_path)
    result = NvidiaBuilder(_build_runner()).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        allow_system_dkms_discovery=True,
    )
    codes = {f.code for f in result.findings}
    # On a test host none of /var/lib/dkms/nvidia/<v>/source,
    # /usr/src/nvidia-<v> exist, so discovery finds nothing.
    assert "DKMS_SOURCE_NOT_FOUND" in codes


def test_dkms_source_dir_that_is_not_a_dir_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    not_a_dir = tmp_path / "not-a-dir"
    not_a_dir.write_text("file", encoding="utf-8")
    result = NvidiaBuilder(_build_runner()).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=not_a_dir,
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_SOURCE_DIR_MISSING" in codes


# ===========================================================================
# Source content verification
# ===========================================================================


def test_dkms_version_mismatch_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path, version="550.100.00")
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version=DRV,
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
        kernel_release=KR,
        driver_version=DRV,
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
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "DKMS_MAKEFILE_MISSING" in codes


# ===========================================================================
# Headers preconditions
# ===========================================================================


def test_headers_makefile_missing_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path, with_makefile=False)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "HEADERS_MAKEFILE_MISSING" in codes


def test_headers_generated_missing_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path, with_generated=False)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "HEADERS_GENERATED_MISSING" in codes


# ===========================================================================
# Precondition errors
# ===========================================================================


def test_empty_kernel_release_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release="",
        driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "KERNEL_RELEASE_MISSING" in codes


def test_empty_driver_version_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version="",
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "DRIVER_VERSION_MISSING" in codes


# ===========================================================================
# Module flavor
# ===========================================================================


def test_open_flavor_rejected(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR,
        driver_version=DRV,
        module_flavor=ModuleFlavor.OPEN,
        headers_dir=headers,
        output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "OPEN_MODULE_REJECTED" in codes
    assert result.has_errors() is True
    assert result.module_artifacts == {}


# ===========================================================================
# Build failures
# ===========================================================================


def test_make_nonzero_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, make_returncode=2)
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "NVIDIA_BUILD_FAILED" in codes


def test_make_launch_failure_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, make_launch_fails=True)
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "NVIDIA_BUILD_LAUNCH_FAILED" in codes


def test_make_timeout_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, make_timeout=True)
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "NVIDIA_BUILD_TIMEOUT" in codes


def test_no_modules_built_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path, modules=())
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, create_modules=())
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "NO_MODULES_BUILT" in codes


# ===========================================================================
# Vermagic verification
# ===========================================================================


def test_vermagic_match_passes(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "VERMAGIC_MISMATCH" not in codes


def test_vermagic_mismatch_is_critical(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, vermagic="7.2.12-huey1")
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "VERMAGIC_MISMATCH" in codes
    critical = [f for f in result.findings if f.code == "VERMAGIC_MISMATCH"]
    assert critical[0].severity == Severity.CRITICAL
    assert "7.2.12-huey1" in critical[0].message
    assert KR in critical[0].message


def test_vermagic_query_failure_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, modinfo_vermagic_returncode=2)
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "VERMAGIC_QUERY_FAILED" in codes


def test_vermagic_empty_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, modinfo_vermagic_empty=True)
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    # Empty vermagic means first token is "" which != KR -> mismatch
    assert "VERMAGIC_MISMATCH" in codes


# ===========================================================================
# Module version verification
# ===========================================================================


def test_module_version_match_passes(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "MODULE_VERSION_MISMATCH" not in codes


def test_module_version_mismatch_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, module_version="550.100.00")
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "MODULE_VERSION_MISMATCH" in codes


def test_module_version_query_failure_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, modinfo_version_returncode=2)
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "MODULE_VERSION_QUERY_FAILED" in codes


# ===========================================================================
# Required modules
# ===========================================================================


def test_missing_nvidia_module_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(
        tmp_path, modules=("nvidia-uvm", "nvidia-modeset")
    )
    result = NvidiaBuilder(
        _build_runner(
            dkms_source=src,
            create_modules=("nvidia-uvm", "nvidia-modeset"),
        )
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "REQUIRED_MODULE_MISSING" in codes
    assert "nvidia" not in result.module_artifacts


def test_missing_nvidia_uvm_module_errors(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(
        tmp_path, modules=("nvidia", "nvidia-modeset")
    )
    result = NvidiaBuilder(
        _build_runner(
            dkms_source=src,
            create_modules=("nvidia", "nvidia-modeset"),
        )
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    codes = {f.code for f in result.findings}
    assert "REQUIRED_MODULE_MISSING" in codes
    assert "nvidia-uvm" not in result.module_artifacts


# ===========================================================================
# Secure Boot
# ===========================================================================


def test_secure_boot_enabled_records_warning(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
        secure_boot_enabled=True,
    )
    warning_codes = {f.code for f in result.findings if f.severity == Severity.WARNING}
    assert "SECUREBOOT_SIGNING_DEFERRED" in warning_codes
    # Not blocking.
    blocking_codes = {
        f.code for f in result.findings if f.severity in (Severity.ERROR, Severity.CRITICAL)
    }
    assert "SECUREBOOT_SIGNING_DEFERRED" not in blocking_codes


def test_secure_boot_disabled_no_warning(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
        secure_boot_enabled=False,
    )
    codes = {f.code for f in result.findings}
    assert "SECUREBOOT_SIGNING_DEFERRED" not in codes


# ===========================================================================
# Staging cleanup
# ===========================================================================


def test_stale_staging_replaced(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    out = tmp_path / "out"
    staging = out / f"nvidia-{DRV}-{KR}"
    staging.mkdir(parents=True)
    (staging / "stale.ko").write_bytes(b"stale")

    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=out,
        dkms_source_dir=src,
    )
    assert not (staging / "stale.ko").exists()
    assert result.has_errors() is False


# ===========================================================================
# Dry run
# ===========================================================================


def test_dry_run_no_io_no_subprocess(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    runner = FixtureRunner()  # zero handlers: any run() raises
    result = NvidiaBuilder(runner).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
        dry_run=True,
    )
    assert result.dry_run is True
    assert runner.calls == ()
    assert not (tmp_path / "out").exists()
    assert result.module_artifacts == {}
    codes = {f.code for f in result.findings}
    assert "NVIDIA_BUILD_DRY_RUN" in codes


# ===========================================================================
# No host mutation (structural)
# ===========================================================================


@pytest.mark.parametrize(
    "forbidden_command",
    [
        "dkms",
        "dpkg",
        "apt",
        "nvidia-installer",
        "mokutil",
        "insmod",
        "rmmod",
        "modprobe",
        "sudo",
        "systemctl",
        "update-initramfs",
        "update-grub",
    ],
)
def test_no_host_mutation_commands_in_argv(
    forbidden_command: str, tmp_path: Path
) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    runner = _build_runner(dkms_source=src)
    NvidiaBuilder(runner).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    for call in runner.calls:
        assert call.argv[0] != forbidden_command, (
            f"builder invoked forbidden command {forbidden_command!r}: "
            f"{call.argv}"
        )


@pytest.mark.parametrize(
    "protected_path",
    ["/boot", "/lib/modules", "/etc/modprobe.d"],
)
def test_no_protected_paths_in_argv(
    protected_path: str, tmp_path: Path
) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    runner = _build_runner(dkms_source=src)
    NvidiaBuilder(runner).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    for call in runner.calls:
        for arg in call.argv:
            assert protected_path not in arg, (
                f"builder passed protected path {protected_path!r}: {call.argv}"
            )


# ===========================================================================
# Invariants
# ===========================================================================


def test_has_errors_true_when_blocking_present(tmp_path: Path) -> None:
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(
        _build_runner(dkms_source=src, vermagic="wrong")
    ).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
    )
    assert result.has_errors() is True


def test_has_errors_false_with_secureboot_warning_only(tmp_path: Path) -> None:
    """Secure Boot warning is not blocking."""
    headers = _make_headers(tmp_path)
    src = _make_dkms_source(tmp_path)
    result = NvidiaBuilder(_build_runner(dkms_source=src)).build(
        kernel_release=KR, driver_version=DRV,
        module_flavor=ModuleFlavor.PROPRIETARY,
        headers_dir=headers, output_dir=tmp_path / "out",
        dkms_source_dir=src,
        secure_boot_enabled=True,
    )
    assert result.has_errors() is False
    assert any(f.severity == Severity.WARNING for f in result.findings)
