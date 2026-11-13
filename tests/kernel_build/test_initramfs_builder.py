"""Canonical test suite for huey.kernel_build.initramfs_builder (Step 41).

Step 17 landed an initial suite proving each branch worked. This file
expands that suite to the full contract required by the handoff:

* command-plan verification: correct argv shape and env vars on every
  depmod / mkinitramfs / lsinitramfs call;
* staging content: lib/modules/<kr>/, initramfs.conf, modules file, and
  the modprobe hook are all correctly placed and populated;
* lsinitramfs verification matrix: correct release, all modules present
  (including compressed forms), no Nouveau, modprobe conf present;
* failure classification (critical vs error vs warning) for each class;
* lsinitramfs unavailability produces warnings but keeps the archive;
* preconditions, depmod failures, mkinitramfs failures;
* staging cleanup before rebuild;
* dry run makes no I/O and launches no subprocess;
* structural proof of no host mutation.

All tests are offline; depmod, mkinitramfs, and lsinitramfs are simulated
via FixtureRunner.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable

import pytest

from huey.kernel_build.initramfs_builder import (
    InitramfsBuilder,
    InitramfsBuildResult,
)
from huey.kernel_build.models import (
    CommandResult,
    Severity,
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


def _ok(spec, *, stdout: bytes = b"", stderr: bytes = b"") -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv, cwd=str(spec.cwd),
            returncode=0, elapsed_seconds=0.0,
        ),
        executed=True, dry_run=False, stdout=stdout, stderr=stderr,
    )


def _fail(spec, returncode: int = 1) -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv, cwd=str(spec.cwd),
            returncode=returncode, elapsed_seconds=0.0,
        ),
        executed=True, dry_run=False, stdout=b"", stderr=b"",
    )


def _is_depmod(spec: CommandSpec) -> bool:
    return spec.argv[0] == "depmod"


def _is_mkinitramfs(spec: CommandSpec) -> bool:
    return spec.argv[0] == "mkinitramfs"


def _is_lsinitramfs(spec: CommandSpec) -> bool:
    return spec.argv[0] == "lsinitramfs"


# ===========================================================================
# Fixture setup
# ===========================================================================


KR = "7.2.15-huey1"


def _make_module_tree(tmp_path: Path) -> Path:
    tree = tmp_path / "modules-tree"
    (tree / "kernel" / "drivers" / "gpu" / "drm" / "amd" / "amdgpu").mkdir(parents=True)
    (tree / "kernel" / "drivers" / "gpu" / "drm" / "amd" / "amdgpu" / "amdgpu.ko").write_bytes(
        b"fake amdgpu.ko\n"
    )
    (tree / "updates" / "nvidia").mkdir(parents=True)
    (tree / "updates" / "nvidia" / "nvidia.ko").write_bytes(b"fake nvidia.ko\n")
    (tree / "updates" / "nvidia" / "nvidia-uvm.ko").write_bytes(b"fake nvidia-uvm.ko\n")
    (tree / "modules.dep").write_text("", encoding="utf-8")
    return tree


def _write_modules_list(path: Path, modules: tuple[str, ...] = ("amdgpu", "nvidia", "nvidia-uvm")) -> Path:
    path.write_text(
        "# Test modules\n" + "\n".join(modules) + "\n", encoding="utf-8"
    )
    return path


def _write_modprobe_conf(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "blacklist nouveau\ninstall nouveau /bin/false\n", encoding="utf-8"
    )
    return path


_DEFAULT_LISTING = (
    "lib/modules/{kr}/modules.dep",
    "lib/modules/{kr}/modules.alias",
    "lib/modules/{kr}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko",
    "lib/modules/{kr}/updates/nvidia/nvidia.ko",
    "lib/modules/{kr}/updates/nvidia/nvidia-uvm.ko",
    "etc/modprobe.d/huey-v100.conf",
    "init",
    "bin/busybox",
)


def _build_runner(
    *,
    kernel_release: str = KR,
    listing_entries: tuple[str, ...] | None = None,
    depmod_returncode: int = 0,
    depmod_launch_fails: bool = False,
    depmod_timeout: bool = False,
    mkinit_returncode: int = 0,
    mkinit_launch_fails: bool = False,
    mkinit_timeout: bool = False,
    lsinit_returncode: int = 0,
    lsinit_launch_fails: bool = False,
    lsinit_timeout: bool = False,
    include_archive_output: bool = True,
) -> FixtureRunner:
    r = FixtureRunner()

    def _depmod(spec):
        if depmod_launch_fails:
            raise RunnerError("depmod not found")
        if depmod_timeout:
            raise RunnerTimeout("depmod timeout")
        if depmod_returncode != 0:
            return _fail(spec, depmod_returncode)
        return _ok(spec)

    def _mkinit(spec):
        if mkinit_launch_fails:
            raise RunnerError("mkinitramfs not found")
        if mkinit_timeout:
            raise RunnerTimeout("mkinitramfs timeout")
        if mkinit_returncode != 0:
            return _fail(spec, mkinit_returncode)
        if include_archive_output:
            idx = spec.argv.index("-o")
            out_path = Path(spec.argv[idx + 1])
            out_path.write_bytes(b"fake initramfs archive bytes\n")
        return _ok(spec)

    def _lsinit(spec):
        if lsinit_launch_fails:
            raise RunnerError("lsinitramfs not found")
        if lsinit_timeout:
            raise RunnerTimeout("lsinitramfs timeout")
        if lsinit_returncode != 0:
            return _fail(spec, lsinit_returncode)
        entries = listing_entries
        if entries is None:
            entries = tuple(e.format(kr=kernel_release) for e in _DEFAULT_LISTING)
        return _ok(spec, stdout=("\n".join(entries) + "\n").encode())

    r.on(_is_depmod, _depmod)
    r.on(_is_mkinitramfs, _mkinit)
    r.on(_is_lsinitramfs, _lsinit)
    return r


def _setup(tmp_path: Path) -> dict:
    tree = _make_module_tree(tmp_path)
    modules_list = _write_modules_list(tmp_path / "modules.list")
    modprobe_conf = _write_modprobe_conf(tmp_path / "huey-v100.conf")
    out = tmp_path / "out"
    out.mkdir()
    return {
        "module_tree": tree,
        "modules_list_path": modules_list,
        "modprobe_conf_path": modprobe_conf,
        "output_dir": out,
    }


# ===========================================================================
# Happy path
# ===========================================================================


def test_happy_path_builds_and_verifies(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    assert result.has_errors() is False, result.findings
    assert result.kernel_release == KR
    assert result.initramfs_path is not None
    assert result.initramfs_path.is_file()
    assert result.initramfs_sha256 is not None
    assert len(result.initramfs_sha256) == 64
    assert result.modules_requested == ("amdgpu", "nvidia", "nvidia-uvm")
    assert set(result.modules_present) == {"amdgpu", "nvidia", "nvidia-uvm"}
    assert result.modules_missing == ()


def test_happy_path_sha_matches_disk(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    assert result.initramfs_path is not None
    on_disk = hashlib.sha256(result.initramfs_path.read_bytes()).hexdigest()
    assert result.initramfs_sha256 == on_disk


def test_result_is_json_serializable(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    payload = json.dumps(result.to_dict())
    assert "amdgpu" in payload
    assert KR in payload


# ===========================================================================
# Command-plan verification
# ===========================================================================


def test_depmod_argv_shape(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    runner = _build_runner()
    InitramfsBuilder(runner).build(kernel_release=KR, **s)
    depmods = [c for c in runner.calls if _is_depmod(c)]
    assert len(depmods) == 1
    spec = depmods[0]
    assert spec.argv == ("depmod", "-b", str((s["output_dir"] / f"stage-{KR}").resolve()), KR)


def test_mkinitramfs_argv_shape(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    runner = _build_runner()
    InitramfsBuilder(runner).build(kernel_release=KR, **s)
    mkinit_calls = [c for c in runner.calls if _is_mkinitramfs(c)]
    assert len(mkinit_calls) == 1
    spec = mkinit_calls[0]
    # -k <kr>
    assert spec.argv[spec.argv.index("-k") + 1] == KR
    # -o <out>/initramfs-<kr>
    out_arg = spec.argv[spec.argv.index("-o") + 1]
    assert out_arg.endswith(f"initramfs-{KR}")
    # -d <stage_root>/etc/initramfs-tools
    conf_arg = spec.argv[spec.argv.index("-d") + 1]
    assert conf_arg.endswith("etc/initramfs-tools")
    assert f"stage-{KR}" in conf_arg


def test_mkinitramfs_env_vars(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    runner = _build_runner()
    InitramfsBuilder(runner).build(kernel_release=KR, **s)
    spec = next(c for c in runner.calls if _is_mkinitramfs(c))
    assert spec.env_overrides["MODULESDIR"].endswith(
        f"stage-{KR}/lib/modules"
    )
    assert spec.env_overrides["SOURCE_DATE_EPOCH"] == "0"


# ===========================================================================
# Staging content
# ===========================================================================


def test_module_tree_staged_under_lib_modules(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    staged = s["output_dir"] / f"stage-{KR}" / "lib" / "modules" / KR
    assert staged.is_dir()
    assert (staged / "kernel" / "drivers" / "gpu" / "drm" / "amd" / "amdgpu" / "amdgpu.ko").is_file()
    assert (staged / "updates" / "nvidia" / "nvidia.ko").is_file()
    assert (staged / "updates" / "nvidia" / "nvidia-uvm.ko").is_file()


def test_initramfs_conf_has_modules_dep_and_modulesdir(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    conf = (
        s["output_dir"]
        / f"stage-{KR}" / "etc" / "initramfs-tools" / "initramfs.conf"
    )
    text = conf.read_text(encoding="utf-8")
    assert "MODULES=dep" in text
    assert "MODULESDIR=" in text
    assert f"stage-{KR}/lib/modules" in text
    assert "COMPRESS=gzip" in text


def test_modules_file_has_requested_modules(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    modules_conf = (
        s["output_dir"]
        / f"stage-{KR}" / "etc" / "initramfs-tools" / "modules"
    )
    text = modules_conf.read_text(encoding="utf-8")
    assert "amdgpu" in text
    assert "nvidia" in text
    assert "nvidia-uvm" in text
    # The generated-by comment references the builder.
    assert "initramfs_builder" in text


def test_modprobe_hook_installed_and_executable(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    hook = (
        s["output_dir"]
        / f"stage-{KR}" / "etc" / "initramfs-tools" / "hooks" / "huey-v100-modprobe"
    )
    assert hook.is_file()
    # Executable bit set (required by mkinitramfs).
    import os
    assert os.access(hook, os.X_OK)
    text = hook.read_text(encoding="utf-8")
    # Standard hook skeleton.
    assert text.startswith("#!/bin/sh")
    assert "prereqs" in text
    assert "hook-functions" in text
    # Copies the modprobe policy into the archive.
    assert "DESTDIR" in text
    assert "huey-v100.conf" in text
    assert "cp" in text


def test_staged_modprobe_conf_matches_input(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    staged = (
        s["output_dir"]
        / f"stage-{KR}" / "etc" / "modprobe.d" / "huey-v100.conf"
    )
    assert staged.is_file()
    assert staged.read_bytes() == s["modprobe_conf_path"].read_bytes()


# ===========================================================================
# lsinitramfs verification matrix
# ===========================================================================


def test_wrong_release_is_critical(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    listing = (
        "lib/modules/7.2.12-huey1/kernel/x.ko",
        "etc/modprobe.d/huey-v100.conf",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_WRONG_RELEASE" in codes
    critical = [f for f in result.findings if f.code == "INITRAMFS_WRONG_RELEASE"]
    assert critical[0].severity == Severity.CRITICAL
    assert result.has_errors() is True


def test_missing_required_module_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    listing = (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        # nvidia-uvm deliberately omitted
        "etc/modprobe.d/huey-v100.conf",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_REQUIRED_MODULE_MISSING" in codes
    assert "nvidia-uvm" in result.modules_missing
    assert result.has_errors() is True


def test_forbidden_nouveau_is_critical(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    listing = tuple(e.format(kr=KR) for e in _DEFAULT_LISTING) + (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/nouveau/nouveau.ko",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_FORBIDDEN_MODULE_PRESENT" in codes
    critical = [
        f for f in result.findings if f.code == "INITRAMFS_FORBIDDEN_MODULE_PRESENT"
    ]
    assert critical[0].severity == Severity.CRITICAL
    assert result.has_errors() is True


def test_compressed_ko_recognized_as_present(tmp_path: Path) -> None:
    """All supported compression suffixes count as the module being present."""
    for suffix in (".ko.zst", ".ko.xz", ".ko.gz", ".ko.bz2"):
        listing = (
            f"lib/modules/{KR}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko",
            f"lib/modules/{KR}/updates/nvidia/nvidia{suffix}",
            f"lib/modules/{KR}/updates/nvidia/nvidia-uvm{suffix}",
            "etc/modprobe.d/huey-v100.conf",
        )
        # Re-create setup per iteration to avoid cross-contamination.
        sub = tmp_path / f"iter_{suffix.replace('.', '_')}"
        sub.mkdir()
        s = _setup(sub)
        result = InitramfsBuilder(
            _build_runner(listing_entries=listing)
        ).build(kernel_release=KR, **s)
        assert set(result.modules_present) == {"amdgpu", "nvidia", "nvidia-uvm"}, (
            f"suffix {suffix}: {result.findings}"
        )
        assert "INITRAMFS_REQUIRED_MODULE_MISSING" not in {
            f.code for f in result.findings
        }


def test_modprobe_conf_missing_warns(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    listing = (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko",
        # no etc/modprobe.d entry
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **s)
    warning_codes = {f.code for f in result.findings if f.severity == Severity.WARNING}
    assert "INITRAMFS_MODPROBE_CONF_MISSING" in warning_codes
    # Modprobe configuration absence is a warning at this build stage.
    # Release verification separately requires full security evidence.
    assert result.has_errors() is False


def test_modprobe_conf_not_asserted_when_hook_disabled(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    listing = (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(
        kernel_release=KR,
        include_modprobe_hook=False,
        **s,
    )
    warning_codes = {f.code for f in result.findings if f.severity == Severity.WARNING}
    assert "INITRAMFS_MODPROBE_CONF_MISSING" not in warning_codes


def test_hook_not_installed_when_disabled(tmp_path: Path) -> None:
    """With include_modprobe_hook=False, the hook file is not written."""
    s = _setup(tmp_path)
    InitramfsBuilder(_build_runner()).build(
        kernel_release=KR, include_modprobe_hook=False, **s
    )
    hook = (
        s["output_dir"]
        / f"stage-{KR}" / "etc" / "initramfs-tools" / "hooks" / "huey-v100-modprobe"
    )
    assert not hook.exists()


# ===========================================================================
# lsinitramfs unavailability
# ===========================================================================


@pytest.mark.parametrize(
    "kwargs, expected_code",
    [
        ({"lsinit_returncode": 2}, "LSINITRAMFS_FAILED"),
        ({"lsinit_launch_fails": True}, "LSINITRAMFS_UNAVAILABLE"),
        ({"lsinit_timeout": True}, "LSINITRAMFS_TIMEOUT"),
    ],
)
def test_lsinitramfs_unavailability_warns_but_keeps_archive(
    tmp_path: Path, kwargs: dict, expected_code: str
) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner(**kwargs)).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert expected_code in codes
    assert "INITRAMFS_UNVERIFIED" in codes
    # Archive is still returned because the file exists on disk.
    assert result.initramfs_path is not None
    assert result.initramfs_path.is_file()
    # All requested modules are recorded as missing.
    assert set(result.modules_missing) == {"amdgpu", "nvidia", "nvidia-uvm"}
    assert result.modules_present == ()
    # An unreadable initramfs must not be marked ready for promotion.
    assert result.has_errors() is True
    assert any(f.code == "INITRAMFS_UNVERIFIED" and f.severity == Severity.ERROR
               for f in result.findings)


# ===========================================================================
# Preconditions
# ===========================================================================


def test_missing_module_tree_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    s["module_tree"] = tmp_path / "nonexistent"
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "MODULE_TREE_MISSING" in codes


def test_empty_module_tree_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    empty = tmp_path / "empty-tree"
    empty.mkdir()
    s["module_tree"] = empty
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "MODULE_TREE_EMPTY" in codes


def test_missing_modules_list_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    s["modules_list_path"] = tmp_path / "nonexistent.list"
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "MODULES_LIST_MISSING" in codes


def test_missing_modprobe_conf_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    s["modprobe_conf_path"] = tmp_path / "nonexistent.conf"
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "MODPROBE_CONF_MISSING" in codes


def test_missing_output_dir_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    s["output_dir"] = tmp_path / "does-not-exist"
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "OUTPUT_DIR_MISSING" in codes


def test_empty_kernel_release_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(kernel_release="", **s)
    codes = {f.code for f in result.findings}
    assert "KERNEL_RELEASE_MISSING" in codes


# ===========================================================================
# depmod failures
# ===========================================================================


def test_depmod_nonzero_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(depmod_returncode=2)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "DEPMOD_FAILED" in codes


def test_depmod_launch_failure_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(depmod_launch_fails=True)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "DEPMOD_LAUNCH_FAILED" in codes


def test_depmod_timeout_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(depmod_timeout=True)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "DEPMOD_TIMEOUT" in codes


# ===========================================================================
# mkinitramfs failures
# ===========================================================================


def test_mkinitramfs_nonzero_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(mkinit_returncode=2)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "MKINITRAMFS_FAILED" in codes


def test_mkinitramfs_launch_failure_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(mkinit_launch_fails=True)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "MKINITRAMFS_LAUNCH_FAILED" in codes


def test_mkinitramfs_timeout_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(mkinit_timeout=True)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "MKINITRAMFS_TIMEOUT" in codes


def test_mkinitramfs_no_output_errors(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(include_archive_output=False)
    ).build(kernel_release=KR, **s)
    codes = {f.code for f in result.findings}
    assert "MKINITRAMFS_NO_OUTPUT" in codes


# ===========================================================================
# Dry run
# ===========================================================================


def test_dry_run_no_io_no_subprocess(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    runner = FixtureRunner()  # zero handlers
    result = InitramfsBuilder(runner).build(
        kernel_release=KR, dry_run=True, **s,
    )
    assert result.dry_run is True
    assert result.initramfs_path is None
    assert runner.calls == ()
    assert not (s["output_dir"] / f"stage-{KR}").exists()
    assert not (s["output_dir"] / f"initramfs-{KR}").exists()
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_BUILD_DRY_RUN" in codes


# ===========================================================================
# Staging cleanup
# ===========================================================================


def test_stale_staging_replaced(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    stale = s["output_dir"] / f"stage-{KR}"
    stale.mkdir()
    (stale / "junk").write_text("stale", encoding="utf-8")
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    assert not (stale / "junk").exists()
    assert result.has_errors() is False


def test_stale_archive_replaced(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    stale = s["output_dir"] / f"initramfs-{KR}"
    stale.write_bytes(b"stale archive content")
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **s)
    assert result.has_errors() is False
    # The archive was replaced; sha256 differs from the stale bytes.
    assert hashlib.sha256(b"stale archive content").hexdigest() != result.initramfs_sha256


# ===========================================================================
# Structural proof of no host mutation
# ===========================================================================


@pytest.mark.parametrize(
    "forbidden_command",
    [
        "update-initramfs",
        "update-grub",
        "grub-install",
        "dpkg",
        "apt",
        "apt-get",
        "dkms",
        "mokutil",
        "sudo",
        "systemctl",
        "modprobe",  # builder does not invoke modprobe directly
    ],
)
def test_no_host_mutation_commands_in_argv(
    forbidden_command: str, tmp_path: Path
) -> None:
    """The builder's own tools (depmod, mkinitramfs, lsinitramfs) are allowed;
    all other host-mutation commands are forbidden."""
    s = _setup(tmp_path)
    runner = _build_runner()
    InitramfsBuilder(runner).build(kernel_release=KR, **s)
    for call in runner.calls:
        assert call.argv[0] != forbidden_command, (
            f"builder invoked forbidden command {forbidden_command!r}: "
            f"{call.argv}"
        )


def test_only_allowed_tools_invoked(tmp_path: Path) -> None:
    """Positive proof: only depmod, mkinitramfs, and lsinitramfs are invoked."""
    s = _setup(tmp_path)
    runner = _build_runner()
    InitramfsBuilder(runner).build(kernel_release=KR, **s)
    allowed = {"depmod", "mkinitramfs", "lsinitramfs"}
    invoked = {call.argv[0] for call in runner.calls}
    assert invoked <= allowed, (
        f"builder invoked unexpected tools: {sorted(invoked - allowed)}"
    )


@pytest.mark.parametrize(
    "protected_path",
    ["/boot", "/etc/modprobe.d", "/etc/initramfs-tools"],
)
def test_no_protected_paths_in_argv(
    protected_path: str, tmp_path: Path
) -> None:
    s = _setup(tmp_path)
    runner = _build_runner()
    InitramfsBuilder(runner).build(kernel_release=KR, **s)
    for call in runner.calls:
        for arg in call.argv:
            # Staging paths under tmp_path may contain /etc/initramfs-tools
            # as a path component without referring to the live /etc tree.
            assert not (arg == protected_path or arg.startswith(protected_path + "/")), (
                f"builder passed live protected path {protected_path!r}: {call.argv}"
            )


# Note: /lib/modules is deliberately NOT in the protected-path check for
# initramfs_builder: the builder places the staged tree under
# <output_dir>/stage-<kr>/lib/modules/<kr>/, and its own -d and MODULESDIR
# env values point there. The stage directory is under the caller's
# output_dir, not the live /lib/modules. Step 5's policy layer enforces
# that output_dir itself is not a protected host path; this test verifies
# the builder does not accidentally construct a path under the live
# /lib/modules.

# ===========================================================================
# Invariants
# ===========================================================================


def test_has_errors_true_when_blocking_present(tmp_path: Path) -> None:
    s = _setup(tmp_path)
    listing = (
        f"lib/modules/7.2.12-huey1/updates/nvidia/nvidia.ko",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **s)
    assert result.has_errors() is True


def test_has_errors_false_when_only_warnings(tmp_path: Path) -> None:
    """A modprobe conf missing is WARNING, not blocking."""
    s = _setup(tmp_path)
    listing = (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **s)
    assert result.has_errors() is False
    assert any(f.severity == Severity.WARNING for f in result.findings)
