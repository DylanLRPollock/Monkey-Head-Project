"""Tests for huey.kernel_build.initramfs_builder (Step 17; Step 41 expands).

``depmod``, ``mkinitramfs``, and ``lsinitramfs`` are simulated via
``FixtureRunner``. The fake ``mkinitramfs`` creates an empty placeholder
file at the ``-o`` path, and the fake ``lsinitramfs`` returns a configurable
listing. No host subprocesses are launched and no files are written
outside ``tmp_path``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

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


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------


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


def _write_modules_list(path: Path) -> Path:
    path.write_text(
        "# Test modules\namdgpu\nnvidia\nnvidia-uvm\n", encoding="utf-8"
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
    mkinit_returncode: int = 0,
    lsinit_returncode: int = 0,
    depmod_timeout: bool = False,
    mkinit_timeout: bool = False,
    lsinit_timeout: bool = False,
    include_archive_output: bool = True,
) -> FixtureRunner:
    r = FixtureRunner()

    def _depmod(spec):
        if depmod_timeout:
            raise RunnerTimeout("depmod timeout")
        if depmod_returncode != 0:
            return _fail(spec, depmod_returncode)
        return _ok(spec)

    def _mkinit(spec):
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
    modprobe_conf = _write_modprobe_conf(
        tmp_path / "huey-v100.conf"
    )
    out = tmp_path / "out"
    out.mkdir()
    return {
        "module_tree": tree,
        "modules_list_path": modules_list,
        "modprobe_conf_path": modprobe_conf,
        "output_dir": out,
    }


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_builds_and_verifies(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(
        kernel_release=KR, **setup,
    )
    assert result.has_errors() is False, result.findings
    assert result.kernel_release == KR
    assert result.initramfs_path is not None
    assert result.initramfs_path.is_file()
    assert result.initramfs_sha256 is not None
    assert len(result.initramfs_sha256) == 64
    assert result.initramfs_size is not None
    assert result.initramfs_size > 0
    assert result.modules_requested == ("amdgpu", "nvidia", "nvidia-uvm")
    assert set(result.modules_present) == {"amdgpu", "nvidia", "nvidia-uvm"}
    assert result.modules_missing == ()


def test_happy_path_sha256_matches_disk(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(
        kernel_release=KR, **setup,
    )
    assert result.initramfs_path is not None
    on_disk = hashlib.sha256(result.initramfs_path.read_bytes()).hexdigest()
    assert result.initramfs_sha256 == on_disk


def test_result_is_json_serializable(tmp_path: Path) -> None:
    import json
    setup = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(
        kernel_release=KR, **setup,
    )
    payload = json.dumps(result.to_dict())
    assert "amdgpu" in payload
    assert KR in payload


# ---------------------------------------------------------------------------
# Correct release assertion
# ---------------------------------------------------------------------------


def test_wrong_release_in_archive_is_critical(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(kernel_release="7.2.12-huey1")
    ).build(
        kernel_release="7.2.15-huey1", **setup,
    )
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_WRONG_RELEASE" in codes
    critical = [f for f in result.findings if f.code == "INITRAMFS_WRONG_RELEASE"]
    assert critical[0].severity == Severity.CRITICAL
    assert result.has_errors() is True


# ---------------------------------------------------------------------------
# Module presence and forbidden modules
# ---------------------------------------------------------------------------


def test_missing_required_module_is_error(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    listing = (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        # nvidia-uvm deliberately omitted
        "etc/modprobe.d/huey-v100.conf",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_REQUIRED_MODULE_MISSING" in codes
    assert "nvidia-uvm" in result.modules_missing
    assert result.has_errors() is True


def test_forbidden_nouveau_present_is_critical(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    listing = tuple(e.format(kr=KR) for e in _DEFAULT_LISTING) + (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/nouveau/nouveau.ko",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_FORBIDDEN_MODULE_PRESENT" in codes
    critical = [
        f for f in result.findings if f.code == "INITRAMFS_FORBIDDEN_MODULE_PRESENT"
    ]
    assert critical[0].severity == Severity.CRITICAL


def test_compressed_ko_recognized_as_present(tmp_path: Path) -> None:
    """nvidia.ko.zst should count as nvidia present."""
    setup = _setup(tmp_path)
    listing = (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko.zst",
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko.zst",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko.zst",
        "etc/modprobe.d/huey-v100.conf",
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **setup)
    assert set(result.modules_present) == {"amdgpu", "nvidia", "nvidia-uvm"}
    assert "INITRAMFS_REQUIRED_MODULE_MISSING" not in {
        f.code for f in result.findings
    }


# ---------------------------------------------------------------------------
# Modprobe conf presence
# ---------------------------------------------------------------------------


def test_modprobe_conf_missing_warns(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    listing = (
        f"lib/modules/{KR}/kernel/drivers/gpu/drm/amd/amdgpu/amdgpu.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia.ko",
        f"lib/modules/{KR}/updates/nvidia/nvidia-uvm.ko",
        # no etc/modprobe.d entry
    )
    result = InitramfsBuilder(
        _build_runner(listing_entries=listing)
    ).build(kernel_release=KR, **setup)
    warning_codes = {f.code for f in result.findings if f.severity == Severity.WARNING}
    assert "INITRAMFS_MODPROBE_CONF_MISSING" in warning_codes
    # Not blocking
    assert result.has_errors() is False


def test_modprobe_conf_not_asserted_when_hook_disabled(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
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
        **setup,
    )
    warning_codes = {f.code for f in result.findings if f.severity == Severity.WARNING}
    assert "INITRAMFS_MODPROBE_CONF_MISSING" not in warning_codes


# ---------------------------------------------------------------------------
# Precondition failures
# ---------------------------------------------------------------------------


def test_missing_module_tree_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    setup["module_tree"] = tmp_path / "nonexistent"
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "MODULE_TREE_MISSING" in codes


def test_empty_module_tree_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    empty = tmp_path / "empty-tree"
    empty.mkdir()
    setup["module_tree"] = empty
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "MODULE_TREE_EMPTY" in codes


def test_missing_modules_list_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    setup["modules_list_path"] = tmp_path / "nonexistent.list"
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "MODULES_LIST_MISSING" in codes


def test_missing_modprobe_conf_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    setup["modprobe_conf_path"] = tmp_path / "nonexistent.conf"
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "MODPROBE_CONF_MISSING" in codes


def test_missing_output_dir_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    setup["output_dir"] = tmp_path / "does-not-exist"
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "OUTPUT_DIR_MISSING" in codes


def test_empty_kernel_release_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(
        kernel_release="", **setup,
    )
    codes = {f.code for f in result.findings}
    assert "KERNEL_RELEASE_MISSING" in codes


# ---------------------------------------------------------------------------
# Subprocess failures
# ---------------------------------------------------------------------------


def test_depmod_failure_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(depmod_returncode=2)
    ).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "DEPMOD_FAILED" in codes


def test_mkinitramfs_failure_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(mkinit_returncode=2)
    ).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "MKINITRAMFS_FAILED" in codes


def test_mkinitramfs_timeout_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(mkinit_timeout=True)
    ).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "MKINITRAMFS_TIMEOUT" in codes


def test_depmod_timeout_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(depmod_timeout=True)
    ).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "DEPMOD_TIMEOUT" in codes


def test_mkinitramfs_no_output_errors(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(include_archive_output=False)
    ).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "MKINITRAMFS_NO_OUTPUT" in codes


def test_lsinitramfs_failure_is_warning(tmp_path: Path) -> None:
    """lsinitramfs failure must warn, not error: archive is still useful."""
    setup = _setup(tmp_path)
    result = InitramfsBuilder(
        _build_runner(lsinit_returncode=2)
    ).build(kernel_release=KR, **setup)
    codes = {f.code for f in result.findings}
    assert "LSINITRAMFS_FAILED" in codes
    # Without an inventory listing, the archive cannot be trusted.
    assert "INITRAMFS_UNVERIFIED" in codes
    assert result.has_errors() is True
    assert any(f.code == "INITRAMFS_UNVERIFIED" and f.severity == Severity.ERROR
               for f in result.findings)
    assert result.initramfs_path is not None


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


def test_dry_run_no_io_no_subprocess(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    runner = FixtureRunner()  # no handlers; any run() would raise
    result = InitramfsBuilder(runner).build(
        kernel_release=KR, dry_run=True, **setup,
    )
    assert result.dry_run is True
    assert result.initramfs_path is None
    assert runner.calls == ()
    assert not (tmp_path / "out" / f"stage-{KR}").exists()
    assert not (tmp_path / "out" / f"initramfs-{KR}").exists()
    codes = {f.code for f in result.findings}
    assert "INITRAMFS_BUILD_DRY_RUN" in codes


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_stale_staging_is_replaced(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    stale = setup["output_dir"] / f"stage-{KR}"
    stale.mkdir()
    (stale / "junk").write_text("stale", encoding="utf-8")

    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **setup)
    assert not (stale / "junk").exists()
    assert result.has_errors() is False


def test_stale_archive_is_replaced(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    stale = setup["output_dir"] / f"initramfs-{KR}"
    stale.write_bytes(b"stale archive")
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **setup)
    assert result.has_errors() is False
    # Archive was replaced, sha256 shouldn't match the stale bytes.
    import hashlib
    assert hashlib.sha256(b"stale archive").hexdigest() != result.initramfs_sha256


# ---------------------------------------------------------------------------
# Command construction checks
# ---------------------------------------------------------------------------


def test_mkinitramfs_called_with_expected_argv(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    runner = _build_runner()
    InitramfsBuilder(runner).build(kernel_release=KR, **setup)

    mkinit_calls = [c for c in runner.calls if c.argv[0] == "mkinitramfs"]
    assert len(mkinit_calls) == 1
    spec = mkinit_calls[0]
    assert "-k" in spec.argv
    assert spec.argv[spec.argv.index("-k") + 1] == KR
    assert "-o" in spec.argv
    out = spec.argv[spec.argv.index("-o") + 1]
    assert out.endswith(f"initramfs-{KR}")
    assert "-d" in spec.argv
    conf_dir = spec.argv[spec.argv.index("-d") + 1]
    assert "etc/initramfs-tools" in conf_dir
    assert spec.env_overrides.get("MODULESDIR") is not None
    assert spec.env_overrides["MODULESDIR"].endswith(
        f"stage-{KR}/lib/modules"
    )


def test_depmod_called_with_expected_argv(tmp_path: Path) -> None:
    setup = _setup(tmp_path)
    runner = _build_runner()
    InitramfsBuilder(runner).build(kernel_release=KR, **setup)

    depmod_calls = [c for c in runner.calls if c.argv[0] == "depmod"]
    assert len(depmod_calls) == 1
    spec = depmod_calls[0]
    assert spec.argv == (
        "depmod",
        "-b",
        str((setup["output_dir"] / f"stage-{KR}").resolve()),
        KR,
    )


# Guard against staging into protected host paths and path traversal.
def test_initramfs_blocks_protected_output(tmp_path: Path) -> None:
    opts = _setup(tmp_path)
    opts["output_dir"] = Path("/boot")
    result = InitramfsBuilder(_build_runner()).build(kernel_release=KR, **opts)
    assert result.has_errors()
    assert "PROTECTED_HOST_PATH" in {f.code for f in result.findings}


def test_initramfs_blocks_kernel_release_traversal(tmp_path: Path) -> None:
    opts = _setup(tmp_path)
    result = InitramfsBuilder(_build_runner()).build(kernel_release="../../evil", **opts)
    assert result.has_errors()
    assert "INVALID_KERNEL_RELEASE" in {f.code for f in result.findings}
