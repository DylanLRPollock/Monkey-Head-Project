"""Canonical test suite for huey.kernel_build.kernel_builder (Step 39).

Step 12 landed an initial suite proving the happy path, preconditions,
make failures, and artifact discovery worked. This file expands that suite
to the full contract required by the handoff:

* command-plan verification: correct argv shape and env vars on every make
  call; correct order (olddefconfig -> kernelrelease -> bindeb-pkg);
* package discovery by dpkg-deb Package field, not filename;
* release mismatch rejection (kernelrelease != .deb package suffix);
* no host state modification (structural proof of no dpkg -i, apt,
  update-*, dkms install in any argv);
* precondition errors (missing Makefile/config, jobs <= 0, bad
  LOCALVERSION, negative SOURCE_DATE_EPOCH);
* every make failure mode (nonzero / launch / timeout) for
  olddefconfig, kernelrelease, and bindeb-pkg;
* dpkg-deb failure handling (missing, nonzero, invalid Package field);
* dry run performs no I/O and launches no subprocess;
* stale .deb cleanup;
* other .debs recorded as INFO and not promoted;
* LOCALVERSION warning when the requested suffix is not in kernelrelease;
* KDEB_PKGVERSION and SOURCE_DATE_EPOCH propagate to make;
* to_dict() is JSON-serializable;
* path escape is rejected in artifact discovery.

All tests are offline; make and dpkg-deb are simulated via FixtureRunner.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Callable

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
        for matcher, handler in reversed(self._handlers):
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


# ===========================================================================
# Helpers
# ===========================================================================


KR = "7.2.15-huey1"
DRV_VERSION = "7.2.15-huey1-1"


def _make_source(tmp_path: Path) -> Path:
    src = tmp_path / "source"
    src.mkdir()
    (src / "Makefile").write_text("# fake kernel Makefile\n", encoding="utf-8")
    return src


def _write_config(path: Path) -> Path:
    path.write_text("CONFIG_MODULES=y\nCONFIG_MODVERSIONS=y\n", encoding="utf-8")
    return path


def _fake_deb(
    build_dir: Path,
    package: str,
    version: str,
    arch: str = "amd64",
    *,
    filename_override: str | None = None,
) -> Path:
    build_dir.mkdir(parents=True, exist_ok=True)
    name = filename_override or f"{package}_{version}_{arch}.deb"
    path = build_dir / name
    # Unique content per (package, version) so SHA-256 differs.
    path.write_bytes(f"Package: {package}\nVersion: {version}\n".encode())
    return path


def _fake_dpkg_deb_handler(spec: CommandSpec) -> RunnerResult:
    """Return the actual Package control field, not the filename."""
    path = Path(spec.argv[2])
    if not path.is_file() or not path.name.endswith(".deb"):
        return _fail(spec, returncode=2)
    pkg = next((line.split(":", 1)[1].strip() for line in
                path.read_text().splitlines() if line.startswith("Package:")), None)
    if not pkg:
        return _fail(spec, returncode=2)
    return _ok(spec, stdout=f"Package: {pkg}\n".encode())


def _build_runner(
    *,
    kernel_release: str = KR,
    create_image: bool = True,
    create_headers: bool = True,
    create_other: bool = True,
    kdeb_version: str = DRV_VERSION,
    bindeb_returncode: int = 0,
    kernelrelease_returncode: int = 0,
    kernelrelease_empty: bool = False,
    olddefconfig_returncode: int = 0,
    image_filename: str | None = None,
    headers_filename: str | None = None,
    image_package_name: str | None = None,
    headers_package_name: str | None = None,
) -> FixtureRunner:
    """Construct a FixtureRunner that simulates a well-formed build.

    ``image_filename`` and ``headers_filename`` allow overriding the
    filename while keeping the Package field derived from the name. This
    lets a test verify discovery-by-field, not discovery-by-filename.
    """
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
        objtree = next(Path(a[2:]) for a in spec.argv if a.startswith("O="))
        build_dir = objtree.parent
        if create_image:
            pkg = image_package_name or f"linux-image-{kernel_release}"
            _fake_deb(
                build_dir,
                pkg,
                kdeb_version,
                filename_override=image_filename,
            )
        if create_headers:
            pkg = headers_package_name or f"linux-headers-{kernel_release}"
            _fake_deb(
                build_dir,
                pkg,
                kdeb_version,
                filename_override=headers_filename,
            )
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


# ===========================================================================
# Happy path
# ===========================================================================


def test_happy_path_produces_image_and_headers(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    assert result.has_errors() is False, result.findings
    assert result.kernel_release == KR
    assert result.image_deb is not None
    assert result.headers_deb is not None
    assert result.image_deb.kind == ArtifactKind.KERNEL_IMAGE_DEB
    assert result.headers_deb.kind == ArtifactKind.KERNEL_HEADERS_DEB
    assert result.image_deb.kernel_release == KR
    assert result.headers_deb.kernel_release == KR


def test_happy_path_sha_and_size_match_disk(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    assert result.image_deb is not None
    on_disk = out / result.image_deb.path
    assert on_disk.is_file()
    assert result.image_deb.sha256 == hashlib.sha256(on_disk.read_bytes()).hexdigest()
    assert result.image_deb.size_bytes == on_disk.stat().st_size


def test_result_is_json_serializable(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    payload = json.dumps(result.to_dict())
    assert KR in payload
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


# ===========================================================================
# Command-plan verification
# ===========================================================================


def test_make_command_order(tmp_path: Path) -> None:
    """olddefconfig -> kernelrelease -> bindeb-pkg, in that order."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    KernelBuilder(runner).build(source_dir=src, config_path=cfg, output_dir=out)
    make_calls = [c for c in runner.calls if c.argv[0] == "make"]
    assert len(make_calls) >= 3
    assert make_calls[0].argv[-1] == "olddefconfig"
    assert "kernelrelease" in make_calls[1].argv
    assert "bindeb-pkg" in make_calls[2].argv


def test_make_argv_shapes(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out, jobs=4,
    )
    by_kind = {
        "olddefconfig": [c for c in runner.calls if _is_olddefconfig(c)][0],
        "kernelrelease": [c for c in runner.calls if _is_kernelrelease(c)][0],
        "bindeb": [c for c in runner.calls if _is_bindeb(c)][0],
    }
    # Every call carries an O=<objtree> argument.
    for name, spec in by_kind.items():
        assert any(a.startswith("O=") for a in spec.argv), (
            f"{name} missing O=<objtree>: {spec.argv}"
        )
    # bindeb-pkg carries -jN.
    assert "-j4" in by_kind["bindeb"].argv


def test_make_env_carries_reproducibility_vars(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
        localversion="-huey1", source_date_epoch=1700000000,
    )
    for call in runner.calls:
        if call.argv[0] != "make":
            continue
        env = call.env_overrides
        assert env["LOCALVERSION"] == "-huey1"
        assert env["SOURCE_DATE_EPOCH"] == "1700000000"
        assert "KBUILD_BUILD_TIMESTAMP" in env
        assert env["KBUILD_BUILD_USER"] == "huey"
        assert env["KBUILD_BUILD_HOST"] == "huey-builder"


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


def test_kdeb_pkgversion_absent_when_not_set(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    for call in runner.calls:
        if call.argv[0] != "make":
            continue
        assert "KDEB_PKGVERSION" not in call.env_overrides


# ===========================================================================
# Discovery by Package field, not filename
# ===========================================================================


def test_discovery_by_field_not_filename(tmp_path: Path) -> None:
    """A .deb whose filename does not encode the version is still accepted
    when the Package field matches."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner(
        image_filename="linux-image-7.2.15-huey1-renamed.deb",
        headers_filename="linux-headers-7.2.15-huey1-renamed.deb",
    )
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    assert result.has_errors() is False, result.findings
    assert result.image_deb is not None
    assert result.headers_deb is not None


def test_mismatched_release_in_package_name_rejected(tmp_path: Path) -> None:
    """Packages named for a different release are not accepted."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner(
        image_package_name="linux-image-7.2.12-huey1",
        headers_package_name="linux-headers-7.2.12-huey1",
    )
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "IMAGE_DEB_MISSING" in codes
    assert "HEADERS_DEB_MISSING" in codes
    assert result.image_deb is None
    assert result.headers_deb is None


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


# ===========================================================================
# dpkg-deb failure handling
# ===========================================================================


def test_dpkg_deb_missing_warns_and_skips(tmp_path: Path) -> None:
    """When dpkg-deb cannot be launched, the .deb is not classified."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()

    def _raise(spec):
        raise RunnerError("dpkg-deb not found")

    runner.on(_is_dpkg_deb, _raise)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "DEB_PACKAGE_FIELD_UNAVAILABLE" in codes
    # The required image/headers check also fires because classification
    # never succeeded.
    assert "IMAGE_DEB_MISSING" in codes or "HEADERS_DEB_MISSING" in codes


def test_dpkg_deb_nonzero_warns_and_skips(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    runner.on(_is_dpkg_deb, lambda s: _fail(s, returncode=2))
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "DEB_PACKAGE_FIELD_UNAVAILABLE" in codes


def test_dpkg_deb_invalid_package_field_warns(tmp_path: Path) -> None:
    """If the output has no Package: line, the .deb is not classified."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    runner.on(_is_dpkg_deb, lambda s: _ok(s, stdout=b"NotAPackageLine\n"))
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "DEB_PACKAGE_FIELD_UNAVAILABLE" in codes


# ===========================================================================
# Precondition errors
# ===========================================================================


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


@pytest.mark.parametrize("jobs", [0, -1])
def test_invalid_jobs_errors(tmp_path: Path, jobs: int) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out, jobs=jobs,
    )
    codes = {f.code for f in result.findings}
    assert "INVALID_JOBS" in codes


@pytest.mark.parametrize("localversion", ["huey1", "1", "1.0"])
def test_invalid_localversion_errors(tmp_path: Path, localversion: str) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out, localversion=localversion,
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


def test_empty_localversion_is_valid(tmp_path: Path) -> None:
    """An empty LOCALVERSION is a valid request (kernel with no suffix)."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner(kernel_release="7.2.15")
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out, localversion="",
    )
    assert result.has_errors() is False, result.findings
    assert result.kernel_release == "7.2.15"


# ===========================================================================
# Subprocess failures: olddefconfig
# ===========================================================================


def test_olddefconfig_nonzero_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(olddefconfig_returncode=2)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "OLDDEFCONFIG_FAILED" in codes


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


def test_olddefconfig_timeout_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()

    def _timeout(spec):
        raise RunnerTimeout("timed out")

    runner.on(_is_olddefconfig, _timeout)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "OLDDEFCONFIG_TIMEOUT" in codes


# ===========================================================================
# Subprocess failures: kernelrelease
# ===========================================================================


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


def test_kernelrelease_launch_failure_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()
    runner.on(_is_olddefconfig, lambda s: _ok(s))

    def _raise(spec):
        raise RunnerError("make not found")

    runner.on(_is_kernelrelease, _raise)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "KERNELRELEASE_LAUNCH_FAILED" in codes


def test_kernelrelease_timeout_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()
    runner.on(_is_olddefconfig, lambda s: _ok(s))

    def _timeout(spec):
        raise RunnerTimeout("timed out")

    runner.on(_is_kernelrelease, _timeout)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "KERNELRELEASE_TIMEOUT" in codes


# ===========================================================================
# Subprocess failures: bindeb-pkg
# ===========================================================================


def test_bindeb_nonzero_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(bindeb_returncode=2)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    codes = {f.code for f in result.findings}
    assert "BINDEB_FAILED" in codes


def test_bindeb_launch_failure_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()
    runner.on(_is_olddefconfig, lambda s: _ok(s))
    runner.on(_is_kernelrelease, lambda s: _ok(s, stdout=b"7.2.15-huey1\n"))

    def _raise(spec):
        raise RunnerError("make not found")

    runner.on(_is_bindeb, _raise)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "BINDEB_LAUNCH_FAILED" in codes


def test_bindeb_timeout_errors(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()
    runner.on(_is_olddefconfig, lambda s: _ok(s))
    runner.on(_is_kernelrelease, lambda s: _ok(s, stdout=b"7.2.15-huey1\n"))

    def _timeout(spec):
        raise RunnerTimeout("timed out")

    runner.on(_is_bindeb, _timeout)
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "BINDEB_TIMEOUT" in codes


# ===========================================================================
# LOCALVERSION warning
# ===========================================================================


def test_localversion_not_in_kernelrelease_warns(tmp_path: Path) -> None:
    """If make ignores LOCALVERSION, the result carries a WARNING."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner(kernel_release="7.2.15")  # no suffix

    # The runner creates packages for "7.2.15" (matching the returned
    # kernelrelease), so artifact discovery succeeds; only the localversion
    # suffix warning fires.
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out, localversion="-huey1",
    )
    warning_codes = {f.code for f in result.findings if f.severity == Severity.WARNING}
    assert "LOCALVERSION_NOT_IN_KERNELRELEASE" in warning_codes
    # Not blocking: artifacts still match.
    assert result.has_errors() is False


# ===========================================================================
# Dry run
# ===========================================================================


def test_dry_run_no_writes_no_subprocess(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = FixtureRunner()  # zero handlers
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


# ===========================================================================
# Stale .deb cleanup
# ===========================================================================


def test_stale_deb_cleanup_before_build(tmp_path: Path) -> None:
    """A stale .deb from a previous run must not be treated as this run's."""
    src, cfg, out = _setup(tmp_path)
    build_dir = out / "build"
    build_dir.mkdir(parents=True)
    stale = build_dir / "linux-image-7.2.15-huey1_old_amd64.deb"
    stale.write_bytes(b"stale package content")

    result = KernelBuilder(_build_runner()).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    assert result.has_errors() is False
    assert not stale.exists()
    # The fresh package exists and its content is not the stale bytes.
    assert result.image_deb is not None
    on_disk = out / result.image_deb.path
    assert on_disk.read_bytes() != b"stale package content"


# ===========================================================================
# No host state modification (structural)
# ===========================================================================


@pytest.mark.parametrize(
    "forbidden_command",
    [
        "dpkg",
        "apt",
        "apt-get",
        "update-initramfs",
        "update-grub",
        "grub-install",
        "dkms",
        "mokutil",
        "systemctl",
        "modprobe",
    ],
)
def test_no_host_mutation_commands_in_argv(
    forbidden_command: str, tmp_path: Path
) -> None:
    """Structural proof: the builder never invokes a host-mutation command."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    for call in runner.calls:
        # `dpkg-deb` is allowed (read-only field query); bare `dpkg` is not.
        if forbidden_command == "dpkg":
            if call.argv[0] == "dpkg-deb":
                continue
            assert call.argv[0] != "dpkg", (
                f"builder must not invoke 'dpkg': {call.argv}"
            )
            continue
        # No other forbidden command may appear as the executable.
        assert call.argv[0] != forbidden_command, (
            f"builder invoked forbidden command {forbidden_command!r}: {call.argv}"
        )


@pytest.mark.parametrize(
    "protected_path",
    ["/boot", "/lib/modules", "/etc/modprobe.d", "/etc/initramfs-tools"],
)
def test_no_protected_paths_in_argv(
    protected_path: str, tmp_path: Path
) -> None:
    """Structural proof: no protected host path appears in any argv."""
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    for call in runner.calls:
        for arg in call.argv:
            assert protected_path not in arg, (
                f"builder passed protected path {protected_path!r}: {call.argv}"
            )


# ===========================================================================
# Path escape rejection
# ===========================================================================


def test_deb_outside_output_dir_is_rejected(tmp_path: Path) -> None:
    """A .deb whose resolved path is not under output_dir is not accepted."""
    src, cfg, out = _setup(tmp_path)
    # Create a .deb outside output_dir that has the right Package field.
    outside = tmp_path / "outside"
    outside.mkdir()
    _fake_deb(outside, f"linux-image-{KR}", DRV_VERSION)

    runner = _build_runner(create_image=False)
    # Also make the handler emit no .deb under build_dir; the only matching
    # .deb is outside. Discovery globs build_dir, so it should not find
    # the outside one.
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out,
    )
    codes = {f.code for f in result.findings}
    assert "IMAGE_DEB_MISSING" in codes


# ===========================================================================
# Invariants
# ===========================================================================


def test_has_errors_true_when_blocking_present(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    result = KernelBuilder(
        _build_runner(create_image=False)
    ).build(source_dir=src, config_path=cfg, output_dir=out)
    assert result.has_errors() is True


def test_has_errors_false_when_only_warnings(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner(kernel_release="7.2.15")
    result = KernelBuilder(runner).build(
        source_dir=src, config_path=cfg, output_dir=out, localversion="-huey1",
    )
    # Only LOCALVERSION_NOT_IN_KERNELRELEASE (WARNING) — not blocking.
    assert result.has_errors() is False
    assert any(f.severity == Severity.WARNING for f in result.findings)


def test_dpkg_deb_real_bare_field_is_accepted(tmp_path: Path) -> None:
    src, cfg, out = _setup(tmp_path)
    runner = _build_runner()
    runner.on(_is_dpkg_deb, lambda spec: _ok(spec, stdout=
        Path(spec.argv[2]).read_text().splitlines()[0].split(":", 1)[1].strip().encode()+b"\n"))
    result = KernelBuilder(runner).build(source_dir=src, config_path=cfg, output_dir=out)
    assert not result.has_errors(), result.findings
    assert result.image_deb and result.headers_deb
