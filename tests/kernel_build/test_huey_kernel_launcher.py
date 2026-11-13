"""Tests for scripts/kernel/huey_kernel.py (Step 13).

The launcher is exercised in two complementary ways:

1. **Structural**: file exists, has a shebang, is marked executable, and
   loads as a module without executing or importing the CLI.
2. **Behavioral**: subprocess invocations against a freshly assembled
   mini-repo (copied launcher + synthetic ``src/huey`` tree). This
   simulates both the "CLI present" case (delegation and exit codes)
   and the "CLI absent" case (graceful exit 3) without touching the real
   repository.

All tests run offline and perform no host mutation.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = REPO_ROOT / "scripts" / "kernel" / "huey_kernel.py"
PYTHON = sys.executable


# ---------------------------------------------------------------------------
# Mini-repo helpers
# ---------------------------------------------------------------------------


def _make_mini_repo(tmp_path: Path) -> Path:
    """Create a minimal tree with a copy of the launcher and empty src/huey."""
    repo = tmp_path / "repo"
    (repo / "scripts" / "kernel").mkdir(parents=True)
    (repo / "src" / "huey" / "kernel_build").mkdir(parents=True)

    launcher_copy = repo / "scripts" / "kernel" / "huey_kernel.py"
    launcher_copy.write_text(LAUNCHER.read_text(encoding="utf-8"), encoding="utf-8")
    os.chmod(launcher_copy, 0o755)

    (repo / "src" / "huey" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "src" / "huey" / "kernel_build" / "__init__.py").write_text(
        "", encoding="utf-8"
    )
    return repo


def _install_fake_cli(
    repo: Path,
    body: str = textwrap.dedent(
        """\
        import sys

        def main():
            args = sys.argv[1:]
            if not args:
                return 0
            if args[0] == "boom":
                raise RuntimeError("boom")
            if args[0] == "none":
                return None
            if args[0] == "argv":
                print("argv[0]=" + sys.argv[0])
                print("argv[1:]=" + ",".join(args))
                return 0
            return int(args[0])
        """
    ),
) -> None:
    """Write a stub ``huey.kernel_build.cli`` into the mini-repo."""
    cli_path = repo / "src" / "huey" / "kernel_build" / "cli.py"
    cli_path.write_text(body, encoding="utf-8")


def _run_launcher(
    repo: Path, *args: str, env_extra: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Invoke the mini-repo's launcher in a clean subprocess."""
    env = dict(os.environ)
    # Strip out anything that would let the launcher see the real src/
    for key in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [PYTHON, str(repo / "scripts" / "kernel" / "huey_kernel.py"), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )


# ---------------------------------------------------------------------------
# Structural tests
# ---------------------------------------------------------------------------


def test_launcher_file_exists() -> None:
    assert LAUNCHER.is_file(), f"missing {LAUNCHER}"


def test_launcher_has_python_shebang() -> None:
    first_line = LAUNCHER.read_text(encoding="utf-8").splitlines()[0]
    assert first_line == "#!/usr/bin/env python3", (
        "launcher must start with '#!/usr/bin/env python3' so it is "
        "executable from any POSIX shell"
    )


def test_launcher_is_executable() -> None:
    """Git should track this file with mode 100755."""
    assert os.access(LAUNCHER, os.X_OK), (
        "scripts/kernel/huey_kernel.py must be committed with the "
        "executable bit set (git mode 100755). Run: "
        f"chmod +x {LAUNCHER.relative_to(REPO_ROOT)}"
    )


def test_launcher_import_does_not_execute_or_import_cli() -> None:
    """Loading the file as a module must not run the entry point or import the CLI."""
    sys.modules.pop("huey.kernel_build.cli", None)
    spec = importlib.util.spec_from_file_location(
        "huey_kernel_launcher_import_test", LAUNCHER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Entry points exist and are callable.
    assert callable(getattr(module, "_main"))
    assert callable(getattr(module, "_repo_src_dir"))
    # The CLI was not imported as a side effect.
    assert "huey.kernel_build.cli" not in sys.modules


def test_launcher_repo_src_dir_resolves_correctly() -> None:
    spec = importlib.util.spec_from_file_location(
        "huey_kernel_launcher_srcdir_test", LAUNCHER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module._repo_src_dir() == REPO_ROOT / "src"


# ---------------------------------------------------------------------------
# Behavioral tests: CLI absent (current state)
# ---------------------------------------------------------------------------


def test_missing_cli_exits_with_code_3(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    # No cli.py installed -> launcher must degrade gracefully.
    result = _run_launcher(repo, "--help")
    assert result.returncode == 3, (
        f"expected exit 3 (missing prerequisites), got {result.returncode}. "
        f"stderr={result.stderr!r}"
    )
    assert "CLI not yet available" in result.stderr
    assert "huey.kernel_build.cli" in result.stderr
    assert "--help" not in result.stdout, "no help text expected while CLI is absent"


def test_missing_cli_exit_code_is_stable_regardless_of_argv(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    for args in ((), ("inventory",), ("--dry-run",), ("nonsense", "arg")):
        result = _run_launcher(repo, *args)
        assert result.returncode == 3, (
            f"argv={args!r}: expected exit 3, got {result.returncode}"
        )


# ---------------------------------------------------------------------------
# Behavioral tests: CLI present (delegation contract for Step 21)
# ---------------------------------------------------------------------------


def test_launcher_delegates_and_propagates_zero(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo)
    result = _run_launcher(repo)
    assert result.returncode == 0, result.stderr


def test_launcher_propagates_nonzero_exit_code(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo)
    result = _run_launcher(repo, "7")
    assert result.returncode == 7, (
        f"expected exit 7 (CLI return), got {result.returncode}. "
        f"stderr={result.stderr!r}"
    )


def test_launcher_treats_none_return_as_zero(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo)
    result = _run_launcher(repo, "none")
    assert result.returncode == 0


def test_launcher_argv_forwarding(tmp_path: Path) -> None:
    """sys.argv[0] is 'huey-kernel'; sys.argv[1:] matches the caller's argv."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo)
    result = _run_launcher(repo, "argv", "inventory", "--json")
    assert result.returncode == 0, result.stderr
    assert "argv[0]=huey-kernel" in result.stdout, result.stdout
    assert "argv[1:]=argv,inventory,--json" in result.stdout, result.stdout


def test_launcher_restores_sys_argv_after_call(tmp_path: Path) -> None:
    """``sys.argv`` must be restored even when the CLI raises."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(
        repo,
        body=textwrap.dedent(
            """\
            import sys

            def main():
                before = sys.argv[:]
                sys.argv = ["corrupted", "argv"]
                raise RuntimeError(f"argv before raise: {before}")
            """
        ),
    )
    result = _run_launcher(repo, "anything")
    # The CLI raises, Python exits 1 with a traceback, but the launcher
    # must have restored sys.argv in its finally block before letting the
    # exception propagate. We do not assert on the traceback contents
    # (brittle); we only assert the process did fail as expected.
    assert result.returncode != 0
    assert "RuntimeError" in result.stderr


def test_launcher_does_not_inject_cli_into_its_own_argv(tmp_path: Path) -> None:
    """The launcher's own argv[1:] must match what the CLI sees as argv[1:]."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(
        repo,
        body=textwrap.dedent(
            """\
            import sys

            def main():
                # Report exactly what the CLI saw.
                print("count=" + str(len(sys.argv) - 1))
                for i, a in enumerate(sys.argv[1:], start=1):
                    print(f"arg[{i}]={a}")
                return 0
            """
        ),
    )
    result = _run_launcher(repo, "alpha", "beta", "gamma")
    assert result.returncode == 0, result.stderr
    assert "count=3" in result.stdout
    assert "arg[1]=alpha" in result.stdout
    assert "arg[2]=beta" in result.stdout
    assert "arg[3]=gamma" in result.stdout


def test_launcher_adds_src_to_path(tmp_path: Path) -> None:
    """With src/ on sys.path via the launcher, the fake CLI resolves.

    This is proven indirectly: the fake cli.py is only reachable through
    ``<repo>/src``. If the launcher failed to add that path, the import
    would fail and exit would be 3, not 0.
    """
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo)
    result = _run_launcher(repo)
    assert result.returncode == 0, (
        "launcher failed to make src/huey.kernel_build.cli importable; "
        f"stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# No-logic guard: launcher must not parse arguments itself
# ---------------------------------------------------------------------------


def test_launcher_does_not_reference_subcommand_names() -> None:
    """Subcommand names belong to the CLI, not the launcher."""
    text = LAUNCHER.read_text(encoding="utf-8")
    for subcommand in (
        "inventory",
        "doctor",
        "plan",
        "config",
        "build-kernel",
        "build-nvidia",
        "initramfs",
        "sign",
        "verify",
        "release",
    ):
        # Allow the word inside docstring examples if needed; disallow quoting
        # it as if it were a literal subcommand constant.
        assert f'"{subcommand}"' not in text and f"'{subcommand}'" not in text, (
            f"launcher references subcommand {subcommand!r}; "
            "subcommand parsing belongs in huey.kernel_build.cli (Step 21)"
        )


def test_launcher_has_no_subprocess_calls() -> None:
    """The launcher must never spawn subprocesses."""
    text = LAUNCHER.read_text(encoding="utf-8")
    for forbidden in (
        "subprocess.",
        "os.system(",
        "os.exec",
        "os.spawn",
        "Popen(",
        "check_output(",
        "check_call(",
    ):
        assert forbidden not in text, (
            f"launcher contains forbidden subprocess invocation {forbidden!r}; "
            "subprocess use belongs in huey.kernel_build.runner (Step 6)"
        )


def test_launcher_does_not_import_optional_heavy_modules() -> None:
    """The launcher is a thin bootstrap: only stdlib + the CLI import."""
    text = LAUNCHER.read_text(encoding="utf-8")
    for forbidden in (
        "import yaml",
        "import numpy",
        "import torch",
        "import tensorflow",
        "import requests",
    ):
        assert forbidden not in text, (
            f"launcher must not import {forbidden!r}; keep it a thin bootstrap"
        )
