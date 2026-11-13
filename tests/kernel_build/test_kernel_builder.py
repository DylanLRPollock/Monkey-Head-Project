"""Tests for huey.kernel_build.kernel_builder (Step 12; Step 39 expands).

All tests run offline. ``make`` and ``dpkg-deb`` are stubbed via
``FixtureRunner``, which dispatches by argv shape and simulates the real
tools' observable side effects (creating ``.deb`` files, emitting
``Package:`` fields).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from huey.kernel_build.kernel_builder import (
    KernelBuilder,
    KernelBuildResult,
)
from huey.kernel_build.models import (
    ArtifactKind,
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
        self._handlers: list[tuple[callable, callable]] = []
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


def _is_olddefconfig(spec: CommandSpec) -> bool:
    return spec.argv[0] == "make" and spec.argv[-1] == "olddefconfig"


def _is_kernelrelease(spec: CommandSpec) -> bool:
    return (
        spec.argv[0] == "make"
        and "-s" in spec.argv
        and "kernelrelease" in spec.argv
    )


def _is_bindeb(spec: CommandSpec) -> bool:
    return spec.argv[0] == "make" and "bindeb-pkg" in spec.argv


def _is_dpkg_deb(spec: CommandSpec) -> bool:
    return spec.argv[0] == "dpkg-deb"


# ---------------------------------------------------------------------------
# Fixture data
# ---------------------------------------------------------------------------


def _make_source(tmp_path: Path) -> Path:
    src = tmp_path / "source"
    src.mkdir()
    (src / "Makefile").write_text("# fake kernel Makefile\n", encoding="utf-8")
    return src


def _write_config(path: Path) -> Path:
    path.write_text("CONFIG_MODULES=y\nCONFIG_MODVERSIONS=y\n", encoding="utf-8")
    return path


def _fake_deb(build_dir: Path, package: str, version: str, arch: str = "amd64") -> Path:
    build_dir.mkdir(parents=True, exist_ok=True)
    name = f"{package}_{version}_{arch}.deb"
    path = build_dir / name
    # Unique content so SHA-256 differs per package.
    path.write_bytes(f"fake deb for {package} {version}\n".encode())
    return path


def _fake_dpkg_deb_handler(spec: CommandSpec) -> RunnerResult:
    """Return Package field derived from the .deb filename."""
    path = Path(spec.argv[2])
    if not path.is_file():
        return _fail(spec, returncode=2)
    name = path.name
    if not name.endswith(".deb"):
        return _fail(spec, returncode=2)
    stem = name[: -len(".deb")]
    pkg = stem.split("_", 1)[0]
    return _ok(spec, stdout=f"Package: {pkg}\n".encode())


def _build_runner(
    *,
    kernel_release: str = "7.2.15-huey1",
    create_image: bool = True,
    create_headers: bool = True,
    create_other: bool = True,
    kdeb_version: str = "7.2.15-huey1-1",
    bindeb_returncode: int = 0,
    kernelrelease_returncode: int = 0,
    kernelrelease_empty: bool = False,
    olddefconfig_returncode: int = 0,
) -> FixtureRunner:
    """Construct a FixtureRunner that simulates a well-formed build."""

    r = FixtureRunner()

    def _odc(spec):
        return _ok(spec) if olddefconfig_returncode == 0 else _fail(spec, olddefconfig_returncode)

    def _kr(spec):
        if kernelrelease_returncode != 0:
            return _fail(spec, kernelrelease_returncode)
        if kernelrelease_empty:
            return _ok(spec, stdout=b"\n")
        return _ok(spec, stdout=f"{kernel_release}\n".encode())

    def _bd(spec):
        if bindeb_returncode != 0:
            return _fail(spec, bindeb_returncode)
        # Find output dir from O=<path>
        objtree = None
        for arg in spec.argv:
            if arg.startswith("O="):
                objtree = Path(arg[2:])
                break
        assert objtree is not None
        build_dir = objtree.parent
        if create_image:
            _fake_deb(build_dir, f"linux-image-{kernel_release}", kdeb_version)
        if create_headers:
            _fake_deb(build_dir, f"linux-headers-{kernel_release}", kdeb_version)
        if create_other:
            _fake_deb(build_dir, "linux-libc-dev", kdeb_version)
        return _ok(spec)

    r.on(_is_olddefconfig, _odc)
    r.on(_is_kernelrelease, _kr)
    r.on(_is_bindeb, _bd)
    r.on(_is_dpkg_deb, _fake_dpkg_deb_handler)
    return r


def _setup(tmp_path: Path) -> tuple[Path, Path, Path]:
    src = _make_source(tmp_path)
    cfg = _write_config(tmp_path / "config")
    out = tmp_path / "out"
    return src, cfg, out


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_produces_image_and_headers(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    assert result.has_errors() is False, result.findings
    assert result.kernel_release == "7.2.15-huey1"
    assert result.image_deb is not None
    assert result.headers_deb is not None
    assert result.image_deb.kind == ArtifactKind.KERNEL_IMAGE_DEB
    assert result.headers_deb.kind == ArtifactKind.KERNEL_HEADERS_DEB
    assert result.image_deb.kernel_release == "7.2.15-huey1"
    assert result.headers_deb.kernel_release == "7.2.15-huey1"
    # Paths are relative and do not contain '..'
    assert not Path(result.image_deb.path).is_absolute()
    assert ".." not in Path(result.image_deb.path).parts
    # SHA-256 is well-formed
    assert len(result.image_deb.sha256) == 64
    assert result.image_deb.size_bytes > 0


def test_happy_path_records_sha_and_size_match_disk(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    assert result.image_deb is not None
    on_disk = (out / result.image_deb.path)
    assert on_disk.is_file()
    assert result.image_deb.sha256 == hashlib.sha256(on_disk.read_bytes()).hexdigest()
    assert result.image_deb.size_bytes == on_disk.stat().st_size


def test_result_is_json_serializable(tmp_path: Path) -> None:
    import json
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    payload = json.dumps(result.to_dict())
    assert "linux-image-7.2.15-huey1" in payload
    assert "linux-headers-7.2.15-huey1" in payload


def test_other_debs_recorded_as_info(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    info_codes = {f.code for f in result.findings if f.severity == Severity.INFO}
    assert "OTHER_DEBS_PRESENT" in info_codes
    assert result.has_errors() is False


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


def test_dry_run_no_writes_no_subprocess(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()  # no handlers; any .run() would raise
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out, dry_run=True,
    )
    assert result.dry_run is True
    assert result.kernel_release is None
    assert result.image_deb is None
    assert result.headers_deb is None
    assert runner.calls == ()
    assert not out.exists()
    codes = {f.code for f in result.findings}
    assert "KERNEL_BUILD_DRY_RUN" in codes


# ---------------------------------------------------------------------------
# Precondition failures
# ---------------------------------------------------------------------------


def test_missing_makefile_errors(tmp_path: Path) -> None:
    src = tmp_path / "no-make"
    src.mkdir()
    cfg = _write_config(tmp_path / "config")
    out = tmp_path / "out"
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "SOURCE_MISSING_MAKEFILE" in codes
    assert result.has_errors() is True


def test_missing_config_errors(tmp_path: Path) -> None:
    src = _make_source(tmp_path)
    out = tmp_path / "out"
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=tmp_path / "nonexistent", output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "CONFIG_MISSING" in codes


def test_invalid_jobs_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out, jobs=0,
    )
    codes = {f.code for f in result.findings}
    assert "INVALID_JOBS" in codes


def test_invalid_localversion_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out, localversion="huey1",
    )
    codes = {f.code for f in result.findings}
    assert "INVALID_LOCALVERSION" in codes


def test_negative_source_date_epoch_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out, source_date_epoch=-1,
    )
    codes = {f.code for f in result.findings}
    assert "INVALID_SOURCE_DATE_EPOCH" in codes


# ---------------------------------------------------------------------------
# Make failures
# ---------------------------------------------------------------------------


def test_olddefconfig_nonzero_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(olddefconfig_returncode=2)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "OLDDEFCONFIG_FAILED" in codes


def test_kernelrelease_nonzero_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(kernelrelease_returncode=1)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "KERNELRELEASE_FAILED" in codes


def test_kernelrelease_empty_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(kernelrelease_empty=True)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "KERNELRELEASE_EMPTY" in codes


def test_bindeb_nonzero_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(bindeb_returncode=2)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "BINDEB_FAILED" in codes


def test_olddefconfig_launch_failure_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()

    def _raise(spec):
        raise RunnerError("make not found")

    runner.on(_is_olddefconfig, _raise)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "OLDDEFCONFIG_LAUNCH_FAILED" in codes


def test_bindeb_timeout_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    # Override bindeb handler with timeout
    runner = FixtureRunner()
    runner.on(_is_olddefconfig, lambda s: _ok(s))
    runner.on(_is_kernelrelease, lambda s: _ok(s, stdout=b"7.2.15-huey1\n"))

    def _timeout(spec):
        raise RunnerTimeout("timeout")

    runner.on(_is_bindeb, _timeout)
    runner.on(_is_dpkg_deb, _fake_dpkg_deb_handler)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "BINDEB_TIMEOUT" in codes


# ---------------------------------------------------------------------------
# Artifact mismatch rejection
# ---------------------------------------------------------------------------


def test_no_debs_produced_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(create_image=False, create_headers=False, create_other=False)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "NO_DEBS_FOUND" in codes


def test_missing_headers_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(create_headers=False)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "HEADERS_DEB_MISSING" in codes
    assert result.image_deb is not None
    assert result.headers_deb is None
    assert result.has_errors() is True


def test_missing_image_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(create_image=False)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "IMAGE_DEB_MISSING" in codes
    assert result.image_deb is None
    assert result.headers_deb is not None


def test_wrong_release_in_package_name_errors(tmp_path: Path) -> None:
    """Packages named for a different release are not accepted as matching."""
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()
    runner.on(_is_olddefconfig, lambda s: _ok(s))
    runner.on(_is_kernelrelease, lambda s: _ok(s, stdout=b"7.2.15-huey1\n"))

    def _bd(spec):
        objtree = next(Path(a[2:]) for a in spec.argv if a.startswith("O="))
        # produce headers/image for a DIFFERENT release
        _fake_deb(objtree.parent, "linux-image-7.2.12-huey1", "7.2.12-huey1-1")
        _fake_deb(objtree.parent, "linux-headers-7.2.12-huey1", "7.2.12-huey1-1")
        return _ok(spec)

    runner.on(_is_bindeb, _bd)
    runner.on(_is_dpkg_deb, _fake_dpkg_deb_handler)

    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "IMAGE_DEB_MISSING" in codes
    assert "HEADERS_DEB_MISSING" in codes
    assert result.image_deb is None
    assert result.headers_deb is None


# ---------------------------------------------------------------------------
# Localversion warning
# ---------------------------------------------------------------------------


def test_localversion_not_in_kernelrelease_warns(tmp_path: Path) -> None:
    """If make ignores LOCALVERSION, the result carries a WARNING (not error)."""
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()
    runner.on(_is_olddefconfig, lambda s: _ok(s))
    # kernelrelease returns a value without the requested localversion
    runner.on(_is_kernelrelease, lambda s: _ok(s, stdout=b"7.2.15\n"))

    def _bd(spec):
        objtree = next(Path(a[2:]) for a in spec.argv if a.startswith("O="))
        _fake_deb(objtree.parent, "linux-image-7.2.15", "7.2.15-1")
        _fake_deb(objtree.parent, "linux-headers-7.2.15", "7.2.15-1")
        return _ok(spec)

    runner.on(_is_bindeb, _bd)
    runner.on(_is_dpkg_deb, _fake_dpkg_deb_handler)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out, localversion="-huey1",
    )
    warning_codes = {f.code for f in result.findings if f.severity == Severity.WARNING}
    assert "LOCALVERSION_NOT_IN_KERNELRELEASE" in warning_codes
    # Not blocking: artifacts still found (they match the actual release)
    assert result.has_errors() is False


# ---------------------------------------------------------------------------
# Environment wiring
# ---------------------------------------------------------------------------


def test_make_env_contains_reproducibility_vars(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
        localversion="-huey1", source_date_epoch=0,
    )
    for call in runner.calls:
        if call.argv[0] != "make":
            continue
        env = call.env_overrides
        assert env["LOCALVERSION"] == "-huey1"
        assert env["SOURCE_DATE_EPOCH"] == "0"
        assert "KBUILD_BUILD_TIMESTAMP" in env
        assert env["KBUILD_BUILD_USER"] == "huey"
        assert env["KBUILD_BUILD_HOST"] == "huey-builder"
        break


def test_kdeb_pkgversion_propagates_when_set(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner(kdeb_version="7.2.15-huey1-1")
    KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
        kdeb_pkgversion="7.2.15-huey1-1",
    )
    for call in runner.calls:
        if call.argv[0] != "make":
            continue
        assert call.env_overrides["KDEB_PKGVERSION"] == "7.2.15-huey1-1"
        break

# Added workspace confinement and malformed-input regression tests.

@pytest.mark.parametrize("bad_jobs", [True, "4", 0, -2])
def test_jobs_fail_closed_with_malformed_input(tmp_path: Path, bad_jobs: object) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()
    result = KernelBuilder(runner).build(src, cfg, out, jobs=bad_jobs)
    assert "INVALID_JOBS" in {f.code for f in result.findings}
    assert not runner.calls


@pytest.mark.parametrize("bad", ["-../../etc", "-huey/evil", "-huey\x00bad"])
def test_localversion_cannot_escape_workspace(tmp_path: Path, bad: str) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(FixtureRunner()).build(src, cfg, out, localversion=bad)
    assert "INVALID_LOCALVERSION" in {f.code for f in result.findings}
    assert not out.exists()


def test_kernel_builder_denies_boot_path_before_runner(tmp_path: Path) -> None:
    src, cfg, _ = _setup(tmp_path)
    runner = FixtureRunner()
    result = KernelBuilder(runner).build(src, cfg, Path("/boot/huey"))
    assert "PROTECTED_HOST_PATH" in {f.code for f in result.findings}
    assert not runner.calls


def test_kernel_builder_rejects_source_output_overlap(tmp_path: Path) -> None:
    src, cfg, _ = _setup(tmp_path)
    result = KernelBuilder(FixtureRunner()).build(src, cfg, src / "output")
    assert "UNSAFE_OUTPUT_OVERLAP" in {f.code for f in result.findings}


def test_kernel_builder_rejects_wrong_workspace(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    root = tmp_path / "approved"
    runner = FixtureRunner()
    result = KernelBuilder(runner).build(src, cfg, out, workspace_root=root)
    assert "PATH_ESCAPES_WORKSPACE" in {f.code for f in result.findings}
    assert not runner.calls


def test_kernel_builder_relative_output_uses_workspace(tmp_path: Path) -> None:
    src, cfg, _ = _setup(tmp_path)
    root = tmp_path / "approved"
    result = KernelBuilder(_build_runner()).build(src, cfg, Path("out"), workspace_root=root)
    assert not result.has_errors(), result.findings
    assert (root / "out" / "build").is_dir()


def test_kernelrelease_invalid_token_is_error(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner(kernel_release="../../etc/passwd")
    result = KernelBuilder(runner).build(src, cfg, out)
    assert "KERNELRELEASE_INVALID" in {f.code for f in result.findings}
