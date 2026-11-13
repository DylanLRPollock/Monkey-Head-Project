"""Guard for `.gitignore` and root `pyproject.toml` (Step 31).

Additions to `.gitignore` and `pyproject.toml` are made by **merging**, not
overwriting. Because the handoff requires preserving existing rules and
metadata, this test file does not assume any particular prior content. It
verifies that the required additions are present and that the additions do
not introduce dangerous over-broad patterns.

Behavioral tests that require the additions skip with an actionable reason
when the additions have not yet been merged; structural tests always run.
Every behavioral test uses `pytest.skip(..., allow_module_level=False)` with
a message pointing at the exact `.gitignore` / `pyproject.toml` block that
Step 31 asks the operator to append.

If a future change replaces the current structure (for example, splitting
`pyproject.toml` into a `hatch`-style layout with separate metadata files),
this test file must be updated in the same change. The additions this file
guards are part of the project's security posture, not incidental.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = REPO_ROOT / ".gitignore"
PYPROJECT = REPO_ROOT / "pyproject.toml"


# ---------------------------------------------------------------------------
# Existence and parseability (always run)
# ---------------------------------------------------------------------------


def test_gitignore_exists() -> None:
    assert GITIGNORE.is_file(), f"missing {GITIGNORE}"


def test_pyproject_exists_and_parses() -> None:
    assert PYPROJECT.is_file(), f"missing {PYPROJECT}"
    tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _gitignore_lines() -> list[str]:
    return [
        ln.strip()
        for ln in GITIGNORE.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]


def _gitignore_text() -> str:
    return GITIGNORE.read_text(encoding="utf-8")


def _pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def _runtime_deps() -> list[str]:
    doc = _pyproject()
    project = doc.get("project", {})
    return list(project.get("dependencies") or [])


def _test_extra() -> list[str]:
    doc = _pyproject()
    project = doc.get("project", {})
    extras = project.get("optional-dependencies") or {}
    return list(extras.get("test") or [])


def _skip_unless_applied(marker: str, hint: str) -> None:
    pytest.skip(f"{marker} not yet applied. {hint}")


# ---------------------------------------------------------------------------
# .gitignore: required entries
# ---------------------------------------------------------------------------


def test_gitignore_ignores_build_huey_kernel() -> None:
    assert "build/huey-kernel/" in _gitignore_lines(), (
        "add 'build/huey-kernel/' to .gitignore; the framework writes only "
        "under that tree"
    )


@pytest.mark.parametrize(
    "pattern",
    [
        "*.deb",
        "*.ko",
        "*.ko.zst",
        "*.ko.gz",
        "*.ko.xz",
        "*.run",
        "initramfs-*",
        "MANIFEST.json",
        "SHA256SUMS",
        "config-delta.txt",
        "kernel-release.json",
        "nvidia-build.json",
    ],
)
def test_gitignore_ignores_artifacts(pattern: str) -> None:
    lines = _gitignore_lines()
    if not lines:
        _skip_unless_applied(
            "The .gitignore block from Step 31",
            "Append the 'HueyOS kernel build framework' block to .gitignore.",
        )
    assert pattern in lines, (
        f"add '{pattern}' to .gitignore; the framework produces files with "
        "that extension or name"
    )


@pytest.mark.parametrize(
    "pattern",
    [
        "*.priv",
        "*.p12",
        "*.pfx",
        "MOK.der",
        "MOK.priv",
        "MOK.pem",
        "id_rsa",
        ".env",
    ],
)
def test_gitignore_ignores_secrets(pattern: str) -> None:
    lines = _gitignore_lines()
    if not lines:
        _skip_unless_applied(
            "The .gitignore block from Step 31",
            "Append the 'HueyOS kernel build framework' block to .gitignore.",
        )
    assert pattern in lines, (
        f"add '{pattern}' to .gitignore so a careless 'git add -A' cannot "
        "stage secret material"
    )


def test_gitignore_ignores_logs_and_coverage() -> None:
    lines = _gitignore_lines()
    if not lines:
        _skip_unless_applied(
            "The .gitignore block from Step 31",
            "Append the 'HueyOS kernel build framework' block to .gitignore.",
        )
    for pattern in ("*.log", ".huey-kernel-logs/", ".coverage"):
        assert pattern in lines, f"add '{pattern}' to .gitignore"


# ---------------------------------------------------------------------------
# .gitignore: dangerous patterns must NOT be present
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "dangerous_pattern",
    [
        # These would ignore legitimate source files or break the repo.
        "*.config",
        "*.toml",
        "*.py",
        "*.md",
        "pyproject.toml",
        "src/",
        "kernel/",
        "scripts/",
        "tests/",
    ],
)
def test_gitignore_does_not_ignore_source(dangerous_pattern: str) -> None:
    lines = _gitignore_lines()
    # Allow a re-inclusion of the form `!pattern` (that is not a bare pattern).
    if dangerous_pattern in lines:
        pytest.fail(
            f".gitignore contains dangerous bare pattern {dangerous_pattern!r}; "
            "it would ignore legitimate source files. If you intended to ignore "
            "generated outputs of this type, use a narrower path."
        )


def test_gitignore_does_not_broadly_ignore_build() -> None:
    """Bare `build/` may already exist with different intent. Verify it does
    not shadow `build/huey-kernel/` in a way that would break source there.
    """
    lines = _gitignore_lines()
    # `build/` is acceptable if the repo already had it. This test only
    # fails if BOTH `build/` is present AND no source directory is safe.
    # We simply report the presence for the operator to see.
    if "build/" in lines and "build/huey-kernel/" not in lines:
        pytest.fail(
            ".gitignore has bare 'build/' but is missing 'build/huey-kernel/'; "
            "add the specific path so the intent is explicit even if 'build/' "
            "is already ignored"
        )


def test_gitignore_reincludes_config_fragments() -> None:
    """Any future `*.config` rule must be paired with explicit re-includes."""
    text = _gitignore_text()
    # Required unconditional re-includes. They are harmless if `*.config` is
    # not present, and protective if a future contributor adds it.
    assert "!src/huey/core/*.config" in text, (
        "add '!src/huey/core/*.config' to .gitignore; the core config "
        "fragments are source"
    )
    assert "!kernel/huey-linux/profiles/*.config" in text, (
        "add '!kernel/huey-linux/profiles/*.config' to .gitignore; the "
        "v100-workstation fragment is source"
    )


def test_gitignore_does_not_ignore_pyproject_or_gitignore() -> None:
    for line in _gitignore_lines():
        assert line != "pyproject.toml", (
            ".gitignore must not ignore pyproject.toml"
        )
        assert line != ".gitignore", (
            ".gitignore must not ignore itself"
        )


# ---------------------------------------------------------------------------
# pyproject.toml: required additions
# ---------------------------------------------------------------------------


def test_pyproject_declares_pyyaml() -> None:
    deps = _runtime_deps()
    if not deps:
        _skip_unless_applied(
            "PyYAML in [project] dependencies",
            "Add \"PyYAML>=6.0,<7\" to pyproject.toml so pip install -e . "
            "installs it; the CLI's build.yaml loader requires it.",
        )
    assert any("pyyaml" in d.lower() for d in deps), (
        "pyproject.toml [project] dependencies must include PyYAML; "
        f"current dependencies: {deps}"
    )


def test_pyproject_pyyaml_constraint_is_reasonable() -> None:
    deps = _runtime_deps()
    matching = [d for d in deps if "pyyaml" in d.lower()]
    if not matching:
        _skip_unless_applied(
            "PyYAML in [project] dependencies",
            "Add \"PyYAML>=6.0,<7\" to pyproject.toml.",
        )
    spec = matching[0].lower()
    # Confirm the lower bound is at least 6.0 and no upper bound below 7.0.
    m = re.search(r"(?:>=?|==)\s*(\d+)", spec)
    assert m is not None, (
        f"PyYAML constraint {matching[0]!r} has no lower bound or exact pin"
    )
    assert int(m.group(1)) >= 6, (
        f"PyYAML constraint {matching[0]!r} requires < 6; the framework "
        "uses safe_load, which is available from 6.x and preferred from "
        "that major"
    )
    # If there is an upper bound, it must be >= 7.
    upper = re.search(r"<\s*(\d+)", spec)
    if upper is not None:
        assert int(upper.group(1)) >= 7, (
            f"PyYAML upper bound < {upper.group(1)} would exclude 6.x-adjacent "
            "fixes; use <7"
        )


def test_pyproject_test_extra_exists() -> None:
    deps = _test_extra()
    if not deps:
        _skip_unless_applied(
            "The [test] extra in [project.optional-dependencies]",
            "Add a [project.optional-dependencies] section with a 'test' key "
            "listing pytest, ruff, and mypy.",
        )
    joined = " ".join(deps).lower()
    for tool in ("pytest", "ruff", "mypy"):
        assert tool in joined, (
            f"the [test] extra must include {tool}; the CI workflow installs "
            ".[test]"
        )


# ---------------------------------------------------------------------------
# pyproject.toml: existing metadata preserved
# ---------------------------------------------------------------------------


def test_pyproject_preserves_requires_python_313() -> None:
    doc = _pyproject()
    requires = doc.get("project", {}).get("requires-python", "")
    assert "3.13" in str(requires), (
        f"requires-python must state Python 3.13; got {requires!r}. The "
        "framework targets Python 3.13 (Step 1 README)."
    )


def test_pyproject_has_name_and_version() -> None:
    doc = _pyproject()
    project = doc.get("project", {})
    assert project.get("name"), "project.name is missing"
    assert project.get("version"), "project.version is missing"


def test_pyproject_does_not_list_nvidia_binaries() -> None:
    """Vendor binaries must not be declared as project dependencies."""
    text = PYPROJECT.read_text(encoding="utf-8").lower()
    for forbidden in ("nvidia.whl", "nvidia.run", "cuda-toolkit", "cudnn"):
        assert forbidden not in text, (
            f"pyproject.toml must not declare {forbidden!r}; vendor binaries "
            "are staged outside the repository per Step 1 and Step 28"
        )


def test_pyproject_has_no_private_secret_paths() -> None:
    """No developer machine paths or secret file references in pyproject."""
    text = PYPROJECT.read_text(encoding="utf-8")
    for pattern in (
        r"/home/[a-z]/",  # developer-specific paths
        r"MOK\.(priv|der|pem)",
        r"\.priv",
        r"KBUILD_SIGN_PIN",
    ):
        assert not re.search(pattern, text), (
            f"pyproject.toml must not reference {pattern!r}"
        )
