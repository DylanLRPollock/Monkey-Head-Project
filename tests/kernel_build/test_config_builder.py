"""Tests for huey.kernel_build.config_builder (Step 11; Step 38 expands).

Tests never invoke `merge_config.sh`, `make`, or any other external tool.
A FixtureRunner responds to:

* the ``merge_config.sh`` argv pattern by performing the merge in pure
  Python (later fragments win, ``# CONFIG_X is not set`` unsets), and
* the ``make -C ... olddefconfig`` pattern by leaving ``.config`` alone
  (this models a well-formed input that needs no dependency fixup).

The delta report and critical-symbol validation run against the resulting
files, exercising the same code paths used in production.
"""

from __future__ import annotations

import io
import re
import tarfile
from pathlib import Path
from typing import Callable

import pytest

from huey.kernel_build.config_builder import (
    ConfigBuilder,
    ConfigBuildResult,
    ConfigDelta,
    ParsedConfig,
)
from huey.kernel_build.models import CommandResult, Severity
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
    """Runner that dispatches commands to Python handlers by matcher."""

    def __init__(self) -> None:
        self._handlers: list[
            tuple[Callable[[CommandSpec], bool], Callable[[CommandSpec], RunnerResult]]
        ] = []
        self._calls: list[CommandSpec] = []

    def on(
        self,
        matcher: Callable[[CommandSpec], bool],
        handler: Callable[[CommandSpec], RunnerResult],
    ) -> "FixtureRunner":
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


def _ok(spec: CommandSpec, *, stdout: bytes = b"", stderr: bytes = b"") -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv,
            cwd=str(spec.cwd),
            returncode=0,
            elapsed_seconds=0.0,
        ),
        executed=True,
        dry_run=False,
        stdout=stdout,
        stderr=stderr,
    )


# ---------------------------------------------------------------------------
# Fake merge_config.sh
# ---------------------------------------------------------------------------

_ASSIGN_RE = re.compile(r"^(CONFIG_[A-Za-z0-9_]+)=(.+)$")
_UNSET_RE = re.compile(r"^#\s*(CONFIG_[A-Za-z0-9_]+) is not set$")


def _fake_merge_config_handler(spec: CommandSpec) -> RunnerResult:
    argv = list(spec.argv)
    output_dir: Path | None = None
    files: list[Path] = []
    i = 1
    while i < len(argv):
        if argv[i] == "-m":
            i += 1
        elif argv[i] == "-O":
            output_dir = Path(argv[i + 1])
            i += 2
        elif argv[i].startswith("-"):
            i += 1
        else:
            files.append(Path(argv[i]))
            i += 1

    if not files or output_dir is None:
        raise RunnerError("fake merge_config.sh: missing -O or files")

    # Seed from base config.
    symbols: dict[str, str | None] = {}
    base = files[0]
    for raw in base.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        m = _ASSIGN_RE.match(line)
        if m:
            symbols[m.group(1)] = m.group(2)
            continue
        m = _UNSET_RE.match(line)
        if m:
            symbols[m.group(1)] = None

    # Merge fragments. Later wins. Emit overrides.
    override_msgs: list[str] = []
    for frag in files[1:]:
        for raw in frag.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            m = _ASSIGN_RE.match(line)
            if m:
                sym, val = m.group(1), m.group(2)
                if sym in symbols:
                    override_msgs.append(
                        f"Value of {sym} is redefined by fragment {frag}"
                    )
                symbols[sym] = val
                continue
            m = _UNSET_RE.match(line)
            if m:
                sym = m.group(1)
                if sym in symbols:
                    override_msgs.append(
                        f"Value of {sym} is redefined by fragment {frag}"
                    )
                symbols[sym] = None

    # Write output.
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / ".config"
    lines: list[str] = []
    for sym in sorted(symbols):
        val = symbols[sym]
        lines.append(f"# {sym} is not set" if val is None else f"{sym}={val}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return _ok(spec, stderr=("\n".join(override_msgs) + "\n").encode())


def _fake_olddefconfig_handler(spec: CommandSpec) -> RunnerResult:
    """No-op olddefconfig: leaves .config unchanged."""
    for arg in spec.argv:
        if arg.startswith("O="):
            outdir = Path(arg[2:])
            if not (outdir / ".config").is_file():
                raise RunnerError(f"fake olddefconfig: no .config at {outdir}")
            break
    return _ok(spec)


def _is_merge_config(spec: CommandSpec) -> bool:
    return spec.argv[0].endswith("scripts/kconfig/merge_config.sh")


def _is_olddefconfig(spec: CommandSpec) -> bool:
    return spec.argv[0] == "make" and spec.argv[-1] == "olddefconfig"


def _make_runner(*, olddefconfig_returncode: int = 0) -> FixtureRunner:
    r = FixtureRunner()
    r.on(_is_merge_config, _fake_merge_config_handler)

    def odc(spec: CommandSpec) -> RunnerResult:
        if olddefconfig_returncode != 0:
            return RunnerResult(
                command=CommandResult(
                    argv=spec.argv, cwd=str(spec.cwd),
                    returncode=olddefconfig_returncode, elapsed_seconds=0.0,
                ),
                executed=True, dry_run=False, stdout=b"", stderr=b"",
            )
        return _fake_olddefconfig_handler(spec)

    r.on(_is_olddefconfig, odc)
    return r


# ---------------------------------------------------------------------------
# Fixture setup helpers
# ---------------------------------------------------------------------------


def _make_source(tmp_path: Path) -> Path:
    src = tmp_path / "source"
    (src / "scripts" / "kconfig").mkdir(parents=True)
    (src / "Makefile").write_text("# fake kernel Makefile\n", encoding="utf-8")
    (src / "scripts" / "kconfig" / "merge_config.sh").write_text(
        "#!/bin/sh\n# fake merge\n", encoding="utf-8"
    )
    return src


def _write_config(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


_BASE_CONFIG = """\
CONFIG_MODULES=y
CONFIG_MODVERSIONS=y
CONFIG_DRM_AMDGPU=m
CONFIG_DRM_NOUVEAU=y
CONFIG_EXT4_FS=y
CONFIG_PCI=y
CONFIG_PCI_MSI=y
"""

_V100_FRAGMENT = """\
# Disable Nouveau for the V100.
# CONFIG_DRM_NOUVEAU is not set
CONFIG_DRM_AMDGPU=m
CONFIG_MODULES=y
CONFIG_MODVERSIONS=y
"""


def _setup(tmp_path: Path) -> tuple[Path, Path, list[Path], Path]:
    src = _make_source(tmp_path)
    base = _write_config(tmp_path / "base.config", _BASE_CONFIG)
    frag = _write_config(tmp_path / "profile.config", _V100_FRAGMENT)
    out = tmp_path / "out"
    return src, base, [frag], out


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_happy_path_produces_effective_config(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    assert result.has_errors() is False, result.findings
    assert result.effective_config_path is not None
    assert result.effective_config_path.is_file()
    assert result.effective_config is not None
    assert result.effective_config.get("CONFIG_MODULES") == "y"
    assert result.effective_config.get("CONFIG_MODVERSIONS") == "y"
    assert result.effective_config.get("CONFIG_DRM_NOUVEAU") is None  # unset


def test_delta_report_written(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    assert result.delta_report_path is not None
    assert result.delta_report_path.is_file()
    text = result.delta_report_path.read_text(encoding="utf-8")
    assert "HueyOS kernel config delta report" in text
    assert "CONFIG_DRM_NOUVEAU" in text


def test_delta_categorizes_correctly(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    assert isinstance(result.delta, ConfigDelta)
    # Nouveau was y in base, unset in effective -> removed
    removed_symbols = {sym for sym, _ in result.delta.removed}
    assert "CONFIG_DRM_NOUVEAU" in removed_symbols
    # No symbols added because base already has everything the fragment sets
    assert result.delta.added == ()
    # No symbol changed to a different non-null value
    assert result.delta.changed == ()


def test_override_recorded_for_nouveau(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    assert any(ov.symbol == "CONFIG_DRM_NOUVEAU" for ov in result.overrides)


# ---------------------------------------------------------------------------
# Critical symbol validation
# ---------------------------------------------------------------------------


def test_modules_missing_is_error(tmp_path: Path) -> None:
    src = _make_source(tmp_path)
    base = _write_config(
        tmp_path / "base.config",
        "CONFIG_MODVERSIONS=y\nCONFIG_DRM_AMDGPU=m\n",
    )
    frag = _write_config(
        tmp_path / "frag.config",
        "# CONFIG_DRM_NOUVEAU is not set\n",
    )
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=[frag],
        output_dir=tmp_path / "out", profile="v100-workstation",
    )
    assert result.has_errors() is True
    codes = {f.code for f in result.findings}
    assert "MODULES_NOT_ENABLED" in codes


def test_modversions_missing_is_error(tmp_path: Path) -> None:
    src = _make_source(tmp_path)
    base = _write_config(
        tmp_path / "base.config",
        "CONFIG_MODULES=y\nCONFIG_DRM_AMDGPU=m\n",
    )
    frag = _write_config(
        tmp_path / "frag.config",
        "# CONFIG_DRM_NOUVEAU is not set\n",
    )
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=[frag],
        output_dir=tmp_path / "out", profile="v100-workstation",
    )
    assert result.has_errors() is True
    codes = {f.code for f in result.findings}
    assert "MODVERSIONS_NOT_ENABLED" in codes


def test_nouveau_forced_by_fragment_is_critical(tmp_path: Path) -> None:
    """If a fragment sets Nouveau=y, the profile check errors even though
    MODULES and MODVERSIONS are set correctly."""
    src = _make_source(tmp_path)
    base = _write_config(
        tmp_path / "base.config",
        "CONFIG_MODULES=y\nCONFIG_MODVERSIONS=y\n"
        "# CONFIG_DRM_NOUVEAU is not set\n",
    )
    frag = _write_config(
        tmp_path / "frag.config",
        "CONFIG_DRM_NOUVEAU=y\n",
    )
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=[frag],
        output_dir=tmp_path / "out", profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "NOUVEAU_FORCED_FOR_V100" in codes
    critical = [
        f for f in result.findings if f.code == "NOUVEAU_FORCED_FOR_V100"
    ]
    assert critical[0].severity == Severity.CRITICAL


def test_nouveau_override_works_when_fragment_wins(tmp_path: Path) -> None:
    """Base has Nouveau=y, fragment unsets it -> no error."""
    src, base, frags, out = _setup(tmp_path)
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "NOUVEAU_FORCED_FOR_V100" not in codes
    assert result.has_errors() is False


def test_non_v100_profile_does_not_check_nouveau(tmp_path: Path) -> None:
    """The Nouveau check is v100-specific."""
    src = _make_source(tmp_path)
    base = _write_config(
        tmp_path / "base.config",
        "CONFIG_MODULES=y\nCONFIG_MODVERSIONS=y\nCONFIG_DRM_NOUVEAU=y\n",
    )
    frag = _write_config(tmp_path / "frag.config", "# comment\n")
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=[frag],
        output_dir=tmp_path / "out", profile="lab",
    )
    codes = {f.code for f in result.findings}
    assert "NOUVEAU_FORCED_FOR_V100" not in codes


# ---------------------------------------------------------------------------
# Precondition failures
# ---------------------------------------------------------------------------


def test_missing_makefile_is_error(tmp_path: Path) -> None:
    src = tmp_path / "src_no_makefile"
    (src / "scripts" / "kconfig").mkdir(parents=True)
    (src / "scripts" / "kconfig" / "merge_config.sh").write_text(
        "#!/bin/sh\n", encoding="utf-8"
    )
    base = _write_config(tmp_path / "base.config", "CONFIG_MODULES=y\n")
    frag = _write_config(tmp_path / "frag.config", "# comment\n")
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=[frag],
        output_dir=tmp_path / "out", profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "SOURCE_MISSING_MAKEFILE" in codes


def test_missing_merge_script_is_error(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "Makefile").write_text("# kernel\n", encoding="utf-8")
    base = _write_config(tmp_path / "base.config", "CONFIG_MODULES=y\n")
    frag = _write_config(tmp_path / "frag.config", "# comment\n")
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=[frag],
        output_dir=tmp_path / "out", profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "SOURCE_MISSING_MERGE_SCRIPT" in codes


def test_missing_base_config_is_error(tmp_path: Path) -> None:
    src = _make_source(tmp_path)
    frag = _write_config(tmp_path / "frag.config", "# comment\n")
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=tmp_path / "nonexistent.config",
        fragments=[frag], output_dir=tmp_path / "out",
        profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "BASE_CONFIG_MISSING" in codes


def test_missing_fragment_is_error(tmp_path: Path) -> None:
    src = _make_source(tmp_path)
    base = _write_config(tmp_path / "base.config", "CONFIG_MODULES=y\n")
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base,
        fragments=[tmp_path / "missing.config"],
        output_dir=tmp_path / "out", profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "FRAGMENT_MISSING" in codes


def test_oversized_fragment_is_error(tmp_path: Path) -> None:
    src = _make_source(tmp_path)
    base = _write_config(tmp_path / "base.config", "CONFIG_MODULES=y\n")
    huge = tmp_path / "huge.config"
    huge.write_text("CONFIG_X=y\n" * 1500, encoding="utf-8")
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=[huge],
        output_dir=tmp_path / "out", profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "FRAGMENT_TOO_LARGE" in codes


# ---------------------------------------------------------------------------
# Runner failures propagate as findings
# ---------------------------------------------------------------------------


def test_olddefconfig_nonzero_is_error(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    result = ConfigBuilder(_make_runner(olddefconfig_returncode=2)).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "OLDDEFCONFIG_FAILED" in codes


def test_merge_launch_failure_is_error(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    runner = FixtureRunner()

    def _raise_merge(spec: CommandSpec) -> RunnerResult:
        raise RunnerError("merge_config.sh missing")

    runner.on(_is_merge_config, _raise_merge)
    result = ConfigBuilder(runner).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "MERGE_CONFIG_LAUNCH_FAILED" in codes


def test_merge_timeout_is_error(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    runner = FixtureRunner()

    def _timeout(spec: CommandSpec) -> RunnerResult:
        raise RunnerTimeout("timed out")

    runner.on(_is_merge_config, _timeout)
    result = ConfigBuilder(runner).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    codes = {f.code for f in result.findings}
    assert "MERGE_CONFIG_TIMEOUT" in codes


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------


def test_dry_run_makes_no_writes_and_no_subprocesses(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    runner = FixtureRunner()  # no handlers -> any call raises
    result = ConfigBuilder(runner).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation", dry_run=True,
    )
    assert result.dry_run is True
    assert runner.calls == ()
    assert not out.exists(), "dry_run must not create output_dir"
    assert result.effective_config_path is None
    codes = {f.code for f in result.findings}
    assert "CONFIG_BUILD_DRY_RUN" in codes


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


def test_two_runs_same_inputs_same_output(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    r1 = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    text1 = r1.effective_config_path.read_text(encoding="utf-8")
    r2 = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    text2 = r2.effective_config_path.read_text(encoding="utf-8")
    assert text1 == text2


def test_stale_config_in_output_is_replaced(tmp_path: Path) -> None:
    """A leftover .config must not seed the merge."""
    src, base, frags, out = _setup(tmp_path)
    out.mkdir(parents=True)
    (out / ".config").write_text("CONFIG_STALE=y\n", encoding="utf-8")
    result = ConfigBuilder(_make_runner()).build(
        source_dir=src, base_config_path=base, fragments=frags,
        output_dir=out, profile="v100-workstation",
    )
    assert result.effective_config is not None
    assert result.effective_config.get("CONFIG_STALE") is None


# ---------------------------------------------------------------------------
# ParsedConfig helpers
# ---------------------------------------------------------------------------


def test_parsed_config_set_symbols_excludes_unset() -> None:
    cfg = ParsedConfig(symbols={"CONFIG_A": "y", "CONFIG_B": None})
    assert cfg.set_symbols == {"CONFIG_A": "y"}
    assert cfg.is_set("CONFIG_A") is True
    assert cfg.is_set("CONFIG_B") is False
    assert cfg.get("CONFIG_C") is None
    assert cfg.get("CONFIG_C", "default") == "default"


# Additional output-path and host-safety checks for the kernel builder.

def test_protected_host_output_rejected_before_runner(tmp_path: Path) -> None:
    src, base, frags, _ = _setup(tmp_path)
    runner = FixtureRunner()
    result = ConfigBuilder(runner).build(src, base, frags, Path("/boot/huey-config"),
                                         profile="v100-workstation")
    assert result.has_errors()
    assert {f.code for f in result.findings} == {"PROTECTED_HOST_PATH"}
    assert not runner.calls


def test_output_path_escape_denied_by_workspace_root(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    runner = FixtureRunner()
    result = ConfigBuilder(runner).build(src, base, frags, out,
                                         profile="v100-workstation",
                                         workspace_root=tmp_path / "approved")
    assert "PATH_ESCAPES_WORKSPACE" in {f.code for f in result.findings}
    assert not runner.calls
    assert not out.exists()


def test_symlink_escape_from_workspace_denied(tmp_path: Path) -> None:
    src, base, frags, _ = _setup(tmp_path)
    ws = tmp_path / "approved"
    ws.mkdir()
    (ws / "out").symlink_to(tmp_path)
    runner = FixtureRunner()
    result = ConfigBuilder(runner).build(src, base, frags, ws / "out" / "build",
                                         profile="v100-workstation", workspace_root=ws)
    assert "PATH_ESCAPES_WORKSPACE" in {f.code for f in result.findings}
    assert not runner.calls


def test_parent_directory_traversal_is_rejected(tmp_path: Path) -> None:
    src, base, frags, _ = _setup(tmp_path)
    runner = FixtureRunner()
    result = ConfigBuilder(runner).build(src, base, frags, Path("../out"),
                                         profile="v100-workstation")
    assert "PATH_ESCAPES_WORKSPACE" in {f.code for f in result.findings}
    assert not runner.calls


def test_output_inside_kernel_source_rejected(tmp_path: Path) -> None:
    src, base, frags, _ = _setup(tmp_path)
    runner = FixtureRunner()
    result = ConfigBuilder(runner).build(src, base, frags, src / "out",
                                         profile="v100-workstation")
    assert "OUTPUT_INSIDE_SOURCE_TREE" in {f.code for f in result.findings}
    assert not runner.calls


def test_output_overwriting_base_config_rejected(tmp_path: Path) -> None:
    src, base, frags, _ = _setup(tmp_path)
    runner = FixtureRunner()
    base = _write_config(tmp_path / ".config", _BASE_CONFIG)
    result = ConfigBuilder(runner).build(src, base, frags, tmp_path,
                                         profile="v100-workstation")
    assert "OUTPUT_OVERWRITES_INPUT" in {f.code for f in result.findings}
    assert base.is_file()
    assert not runner.calls


@pytest.mark.parametrize("filename", [".config", "config-delta.txt"])
def test_symlinked_output_file_refused(tmp_path: Path, filename: str) -> None:
    src, base, frags, out = _setup(tmp_path)
    out.mkdir()
    guarded = tmp_path / "guarded"
    guarded.write_text("must-not-change", encoding="utf-8")
    (out / filename).symlink_to(guarded)
    runner = FixtureRunner()
    result = ConfigBuilder(runner).build(src, base, frags, out,
                                         profile="v100-workstation")
    assert "OUTPUT_SYMLINK_REFUSED" in {f.code for f in result.findings}
    assert guarded.read_text(encoding="utf-8") == "must-not-change"
    assert not runner.calls


def test_make_timeout_has_distinct_error(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    runner = FixtureRunner().on(_is_merge_config, _fake_merge_config_handler)

    def timeout(spec: CommandSpec) -> RunnerResult:
        raise RunnerTimeout("olddefconfig exceeded deadline")

    runner.on(_is_olddefconfig, timeout)
    result = ConfigBuilder(runner).build(src, base, frags, out,
                                         profile="v100-workstation")
    assert "OLDDEFCONFIG_TIMEOUT" in {f.code for f in result.findings}


def test_amdgpu_removed_by_olddefconfig_blocks_profile(tmp_path: Path) -> None:
    src, base, frags, out = _setup(tmp_path)
    runner = FixtureRunner().on(_is_merge_config, _fake_merge_config_handler)

    def change_amd(spec: CommandSpec) -> RunnerResult:
        p = next(Path(x[2:]) for x in spec.argv if x.startswith("O=")) / ".config"
        p.write_text(p.read_text(encoding="utf-8").replace(
            "CONFIG_DRM_AMDGPU=m", "# CONFIG_DRM_AMDGPU is not set",
        ), encoding="utf-8")
        return _ok(spec)

    runner.on(_is_olddefconfig, change_amd)
    result = ConfigBuilder(runner).build(src, base, frags, out,
                                         profile="v100-workstation")
    assert "AMDGPU_MODULE_REQUIRED" in {f.code for f in result.findings}
    assert result.has_errors()


def test_valid_workspace_scoped_output_passes(tmp_path: Path) -> None:
    src, base, frags, _ = _setup(tmp_path)
    ws = tmp_path / "approved"
    out = ws / "config"
    result = ConfigBuilder(_make_runner()).build(src, base, frags, out,
                                                 profile="v100-workstation",
                                                 workspace_root=ws)
    assert not result.has_errors()
    assert result.effective_config_path == out / ".config"


def test_relative_output_is_rooted_in_approved_workspace(tmp_path: Path) -> None:
    src, base, frags, _ = _setup(tmp_path)
    root = tmp_path / "approved"
    result = ConfigBuilder(_make_runner()).build(
        src, base, frags, Path("config"),
        profile="v100-workstation", workspace_root=root,
    )
    assert not result.has_errors(), result.findings
    assert result.effective_config_path == root / "config" / ".config"
    assert (root / "config" / ".config").exists()
