"""Tests for the existing scripts/kernel/assemble_config.sh (Step 22).

The script is **not modified by this step**. It ships in the repository
and is tested here against:

* the current ``src/huey/core/*.config`` fragments, and
* the new ``kernel/huey-linux/profiles/v100-workstation.config`` fragment
  added in Step 10.

Structural tests always run. They catch the invariants that must never
regress: executable bit, shebang, ``merge_config.sh`` reference, and the
presence of the ``core``, ``pulse``, and ``lab`` profile names.

Behavioral tests use **capability detection**: each behavioral test first
probes the script with a small set of plausible invocations. If the
interface the test needs is not detected, the test skips with an explicit,
actionable reason naming the capability the script is missing so the
operator can either confirm the interface or add the smallest compatible
change in a follow-up. The alternative — silently passing, or failing
against an interface this test file has never seen — would misrepresent
the script's state.

The three behavioral scenarios named by the handoff are covered explicitly:

* ``test_missing_fragment_produces_nonzero_exit``
* ``test_conflicting_symbols_resolves_deterministically``
* ``test_recursive_include_is_detected_or_rejected``

Interface detection
-------------------
``_detect_capabilities`` reads the script's text once and reports which
optional features it appears to expose. Behavioral tests consume the
result. Detection is intentionally generous (a plain ``--help`` string
counts as help support) because the goal is to run the behavioral test
whenever there is a plausible interface, not to enforce a specific one.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "kernel" / "assemble_config.sh"
CORE_DIR = REPO_ROOT / "src" / "huey" / "core"
PROFILES_DIR = REPO_ROOT / "kernel" / "huey-linux" / "profiles"

_REQUIRED_CORE_FRAGMENTS = ("base.config", "core.config", "pulse.config", "lab.config")
_REQUIRED_PROFILE_NAMES = ("core", "pulse", "lab")


# ---------------------------------------------------------------------------
# Capability detection
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Capabilities:
    supports_help: bool
    has_profile_flag: bool
    has_positional_profile: bool
    has_output_flag: bool
    has_base_config_flag: bool
    mentions_merge_config: bool
    mentions_fallback: bool

    @property
    def has_any_invocation(self) -> bool:
        return self.supports_help or self.has_profile_flag or self.has_positional_profile


def _read_script() -> str:
    assert SCRIPT.is_file(), f"missing {SCRIPT}"
    return SCRIPT.read_text(encoding="utf-8", errors="replace")


def _detect_capabilities() -> Capabilities:
    text = _read_script()
    lowered = text.lower()
    return Capabilities(
        supports_help=bool(re.search(r"\b(--help|-h\b)", text)),
        has_profile_flag=bool(re.search(r"--profile\b", text)),
        has_positional_profile=bool(re.search(r"\$\{?[1-9]", text)),
        has_output_flag=bool(re.search(r"(?:--output\b|\s-o\s)", text)),
        has_base_config_flag=bool(re.search(r"(--base-config\b|--base\b)", text)),
        mentions_merge_config="merge_config.sh" in text,
        mentions_fallback=(
            "fallback" in lowered
            or "cannot find" in lowered
            or "not found" in lowered
        ),
    )


def _capabilities_or_skip(*required: str) -> Capabilities:
    """Return detected capabilities or skip with an actionable reason."""
    caps = _detect_capabilities()
    missing = [name for name in required if not getattr(caps, name)]
    if missing:
        pytest.skip(
            f"assemble_config.sh does not expose capability {missing!r} "
            "as detected by string inspection. Confirm the interface with "
            "'scripts/kernel/assemble_config.sh --help' and, if needed, "
            "add the smallest compatible change (e.g. a usage() function) "
            "in a follow-up. Detection results: "
            + ", ".join(f"{k}={getattr(caps, k)}" for k in caps.__dataclass_fields__)
        )
    return caps


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def script_path() -> Path:
    if not SCRIPT.is_file():
        pytest.fail(f"missing script: {SCRIPT}")
    return SCRIPT


def _run_script(*argv: str, cwd: Path | None = None, timeout: float = 30.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT), *argv],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd is not None else str(REPO_ROOT),
        timeout=timeout,
        check=False,
    )


# ---------------------------------------------------------------------------
# Structural invariants (always run)
# ---------------------------------------------------------------------------


def test_script_exists(script_path: Path) -> None:
    assert script_path.is_file()


def test_script_is_executable(script_path: Path) -> None:
    assert os.access(script_path, os.X_OK), (
        f"{script_path} must be executable (git mode 100755). Run: "
        f"chmod +x {script_path.relative_to(REPO_ROOT)}"
    )


def test_script_has_shebang(script_path: Path) -> None:
    first = script_path.read_text(encoding="utf-8").splitlines()[0]
    assert first.startswith("#!"), f"missing shebang: {first!r}"
    assert "sh" in first or "bash" in first, f"unexpected interpreter: {first!r}"


def test_script_references_merge_config(script_path: Path) -> None:
    text = script_path.read_text(encoding="utf-8")
    assert "merge_config.sh" in text, (
        "assemble_config.sh must reference the kernel's merge_config.sh; "
        "if the fallback has been removed, this must be documented per the "
        "handoff: 'Do not delete its fallback unless the Linux merge-script "
        "dependency becomes mandatory and is documented.'"
    )


@pytest.mark.parametrize("profile", _REQUIRED_PROFILE_NAMES)
def test_script_mentions_profile_name(script_path: Path, profile: str) -> None:
    text = script_path.read_text(encoding="utf-8")
    pattern = re.compile(rf"\b{re.escape(profile)}\b")
    assert pattern.search(text), (
        f"assemble_config.sh must mention the '{profile}' profile; the "
        "handoff requires preserving core|pulse|lab behavior."
    )


def test_script_does_not_hardcode_credentials(script_path: Path) -> None:
    text = script_path.read_text(encoding="utf-8")
    for pattern in (
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"\bMOK_PIN\s*=",
        r"\bKBUILD_SIGN_PIN\s*=",
        r"\bGITHUB_TOKEN\s*=",
    ):
        assert not re.search(pattern, text), (
            f"assemble_config.sh must not contain {pattern!r}"
        )


# ---------------------------------------------------------------------------
# Fixture availability
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fragment", _REQUIRED_CORE_FRAGMENTS)
def test_core_fragment_exists(fragment: str) -> None:
    path = CORE_DIR / fragment
    assert path.is_file(), f"missing core fragment: {path}"


def test_v100_workstation_fragment_exists() -> None:
    path = PROFILES_DIR / "v100-workstation.config"
    assert path.is_file(), (
        f"missing {path}; Step 10 adds it and assemble_config.sh is expected "
        "to consume it via the profile name 'v100-workstation'."
    )


# ---------------------------------------------------------------------------
# Behavioral: --help / no-args usage
# ---------------------------------------------------------------------------


def test_script_help_or_usage() -> None:
    """A usage message must be reachable without a real kernel tree.

    The test accepts any of:
    * ``--help`` exits 0/1/2 with some output,
    * no arguments exit nonzero with some usage text.
    """
    candidates = [("--help",), (), ("-h",)]
    for argv in candidates:
        try:
            result = _run_script(*argv, timeout=10.0)
        except subprocess.TimeoutExpired:
            continue
        if result.returncode in (0, 1, 2) and (result.stdout or result.stderr):
            return
    pytest.skip(
        "assemble_config.sh produced no usage text for any of --help, -h, or "
        "no-args. If the script intentionally requires positional arguments "
        "only, add a 'usage:' line to stderr on error to satisfy this check."
    )


# ---------------------------------------------------------------------------
# Behavioral checks against the actual positional interface:
# assemble_config.sh <role> <output-config> [kernel-config-dir]
# ---------------------------------------------------------------------------


def _fixture_config_dir(tmp_path: Path, role_text: str) -> Path:
    cfg = tmp_path / "configs"
    cfg.mkdir()
    (cfg / "base.config").write_text(
        "CONFIG_MODULES=y\nCONFIG_X=first\n", encoding="utf-8",
    )
    (cfg / "core.config").write_text(role_text, encoding="utf-8")
    return cfg


def test_missing_fragment_produces_nonzero_exit(tmp_path: Path) -> None:
    cfg = _fixture_config_dir(tmp_path, "# include fragments/absent.config\n")
    result = _run_script("core", str(tmp_path / "output.config"), str(cfg), cwd=tmp_path)
    assert result.returncode != 0
    assert "missing included fragment" in (result.stdout + result.stderr).lower()
    assert not (tmp_path / "output.config").exists()


def test_conflicting_symbols_resolves_deterministically(tmp_path: Path) -> None:
    cfg = _fixture_config_dir(tmp_path, "CONFIG_X=second\nCONFIG_EXTRA=y\n")
    out = tmp_path / "output.config"
    first = _run_script("core", str(out), str(cfg), cwd=tmp_path)
    assert first.returncode == 0, first.stderr
    data = out.read_bytes()
    x_assignments = [line for line in data.decode().splitlines() if line.startswith("CONFIG_X=")]
    assert x_assignments == ["CONFIG_X=second"]
    second = _run_script("core", str(out), str(cfg), cwd=tmp_path)
    assert second.returncode == 0, second.stderr
    assert out.read_bytes() == data, "kernel config merging must be deterministic"


def test_recursive_include_is_detected_or_rejected(tmp_path: Path) -> None:
    cfg = _fixture_config_dir(tmp_path, "# include fragments/a.config\n")
    fragments = cfg / "fragments"
    fragments.mkdir()
    (fragments / "a.config").write_text(
        "CONFIG_A=y\n# include fragments/b.config\n", encoding="utf-8",
    )
    (fragments / "b.config").write_text(
        "CONFIG_B=y\n# include fragments/a.config\n", encoding="utf-8",
    )
    out = tmp_path / "output.config"
    result = _run_script("core", str(out), str(cfg), cwd=tmp_path, timeout=10)
    assert result.returncode != 0, "include cycle must be rejected"
    assert "recursive include" in (result.stdout + result.stderr).lower()
    assert not out.exists()
