"""Tests for scripts/kernel/build-kernel.sh (Step 23).

Runs the wrapper in isolated subprocess interpreters against a mini-repo
that copies the wrapper and installs a synthetic CLI, so we measure the
wrapper's behavior without invoking the real CLI or touching the host.

Behavioral coverage:
* argv forwarding (including spaces and shell metacharacters, inert);
* --help and --dry-run passthrough;
* CLI exit codes 0, 2, 3, 4, 5 forwarded unchanged;
* missing python3.13 -> exit 90;
* missing src/huey -> exit 91;
* PYTHONPATH is injected only with <repo>/src, without clobbering the parent.

Structural coverage:
* shebang, executable bit, `set -eu` or `set -euo pipefail`, no business
  logic (no `huey.kernel_build.*` submodule references beyond `cli`,
  no argparse, no direct kernel source references).
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "kernel" / "build-kernel.sh"


# ---------------------------------------------------------------------------
# Mini-repo helpers
# ---------------------------------------------------------------------------


def _make_mini_repo(tmp_path: Path, *, with_src: bool = True) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts" / "kernel").mkdir(parents=True)
    wrapper_copy = repo / "scripts" / "kernel" / "build-kernel.sh"
    shutil.copy2(WRAPPER, wrapper_copy)
    os.chmod(wrapper_copy, 0o755)
    if with_src:
        (repo / "src" / "huey" / "kernel_build").mkdir(parents=True)
        (repo / "src" / "huey" / "__init__.py").write_text("", encoding="utf-8")
        (repo / "src" / "huey" / "kernel_build" / "__init__.py").write_text(
            "", encoding="utf-8"
        )
    return repo


def _install_fake_cli(repo: Path, body: str) -> None:
    # Model the fixed subcommand that the real dispatcher consumes.
    body = body.replace("args = sys.argv[1:]", "args = sys.argv[2:]")
    # The production CLI has a __main__ guard; the miniature fake needs it too.
    body += "\nif __name__ == '__main__':\n    raise SystemExit(main())\n"
    cli_path = repo / "src" / "huey" / "kernel_build" / "cli.py"
    cli_path.write_text(body, encoding="utf-8")


_DEFAULT_CLI = textwrap.dedent(
    """\
    from __future__ import annotations
    import sys

    def main() -> int:
        args = sys.argv[1:]
        if not args:
            return 0
        first = args[0]
        if first == "argc":
            print("argc=" + str(len(args) - 1))
            for i, a in enumerate(args[1:], start=1):
                print(f"arg[{i}]={a}")
            return 0
        if first == "print-py3":
            print("python=" + sys.version.split()[0])
            return 0
        if first == "print-pp":
            import os
            print("pp=" + os.environ.get("PYTHONPATH", ""))
            return 0
        if first == "echo-args":
            for a in args[1:]:
                print(a)
            return 0
        try:
            return int(first)
        except ValueError:
            return 99
    """
)


def _make_path_without_python313(bin_dir: Path) -> str:
    """Return a PATH containing symlinks to every executable except python3.13."""
    bin_dir.mkdir(exist_ok=True)
    for tool in ("sh", "env", "dirname", "pwd", "cd", "printf"):
        src = shutil.which(tool)
        if src is not None:
            dst = bin_dir / tool
            if not dst.exists():
                try:
                    os.symlink(src, dst)
                except OSError:
                    pass
    # Also symlink the current Python for the fake CLI to run (but not as
    # python3.13). The wrapper will still fail the python3.13 check.
    py = Path(sys.executable)
    if py.is_file():
        try:
            os.symlink(py, bin_dir / "python3")
        except OSError:
            pass
    return str(bin_dir)


def _run_wrapper(
    repo: Path,
    *args: str,
    path_override: str | None = None,
    extra_env: dict[str, str] | None = None,
    timeout: float = 20.0,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    if path_override is not None:
        env["PATH"] = path_override
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(repo / "scripts" / "kernel" / "build-kernel.sh"), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        check=False,
    )


# ---------------------------------------------------------------------------
# Structural
# ---------------------------------------------------------------------------


def test_wrapper_exists() -> None:
    assert WRAPPER.is_file(), f"missing {WRAPPER}"


def test_wrapper_has_sh_shebang() -> None:
    first = WRAPPER.read_text(encoding="utf-8").splitlines()[0]
    assert first.startswith("#!"), f"missing shebang: {first!r}"
    assert "sh" in first, f"unexpected interpreter: {first!r}"


def test_wrapper_is_executable() -> None:
    mode = WRAPPER.stat().st_mode
    assert mode & stat.S_IXUSR, (
        "build-kernel.sh must be committed executable (git mode 100755)"
    )


def test_wrapper_uses_strict_shell_options() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "set -eu" in text or "set -euo pipefail" in text or "set -e" in text, (
        "build-kernel.sh must use 'set -e' (and ideally 'set -eu') so "
        "failures abort the wrapper"
    )


def test_wrapper_uses_exec_for_python() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "exec python" in text or "exec /usr" in text, (
        "build-kernel.sh must 'exec' the Python process so signals, exit "
        "codes, and stdin/stdout/stderr pass through unchanged"
    )


def test_wrapper_forwards_quoted_argv() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert '"$@"' in text, (
        "build-kernel.sh must forward argv via '\"$@\"' (quoted) so that "
        "spaces and shell metacharacters are preserved"
    )


def test_wrapper_references_only_cli_subcommand() -> None:
    """The wrapper must not name any module other than cli."""
    text = WRAPPER.read_text(encoding="utf-8")
    forbidden = [
        "kernel_builder",
        "config_builder",
        "nvidia_builder",
        "initramfs_builder",
        "release.py",
        "verifier",
        "signing",
        "subprocess",
        "argparse",
    ]
    for name in forbidden:
        assert name not in text, (
            f"build-kernel.sh references {name!r}; that logic belongs in "
            "huey.kernel_build.cli (Step 21) or its components, not in the "
            "wrapper"
        )


# ---------------------------------------------------------------------------
# Behavioral: argv forwarding
# ---------------------------------------------------------------------------


def test_no_args_exit_zero(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(repo)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("exit_code", [0, 2, 3, 4, 5, 42])
def test_exit_code_forwarded(tmp_path: Path, exit_code: int) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(repo, str(exit_code))
    assert result.returncode == exit_code, (
        f"expected exit {exit_code}, got {result.returncode}; "
        f"stderr={result.stderr!r}"
    )


def test_argv_forwarding_in_order(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(
        repo, "argc", "--dry-run", "--config", "kernel/huey-linux/build.yaml",
    )
    assert result.returncode == 0, result.stderr
    assert "argc=3" in result.stdout
    assert "arg[1]=--dry-run" in result.stdout
    assert "arg[2]=--config" in result.stdout
    assert "arg[3]=kernel/huey-linux/build.yaml" in result.stdout


def test_spaces_in_argv_preserved(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(repo, "echo-args", "path with spaces", "another arg")
    assert result.returncode == 0, result.stderr
    assert "path with spaces" in result.stdout
    assert "another arg" in result.stdout


def test_shell_metacharacters_inert(tmp_path: Path) -> None:
    """Metacharacters inside argv must not be interpreted by the wrapper."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    marker = tmp_path / "should-not-exist"
    payload = f"a b ; touch {marker} ; echo done"
    result = _run_wrapper(repo, "echo-args", payload)
    assert result.returncode == 0, result.stderr
    assert payload in result.stdout, (
        f"payload was mangled by the wrapper: stdout={result.stdout!r}"
    )
    assert not marker.exists(), (
        "wrapper interpreted shell metacharacters from an argv element"
    )


# ---------------------------------------------------------------------------
# Behavioral: environment
# ---------------------------------------------------------------------------


def test_pythonpath_contains_repo_src(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(repo, "print-pp")
    assert result.returncode == 0, result.stderr
    assert f"pp={repo}/src" in result.stdout, (
        f"PYTHONPATH was not set to {repo}/src; got {result.stdout!r}"
    )


def test_pythonpath_preserves_parent_value(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(
        repo, "print-pp", extra_env={"PYTHONPATH": "/some/parent/path"}
    )
    assert result.returncode == 0, result.stderr
    # The wrapper prepends <repo>/src; the parent value remains after it.
    assert f"{repo}/src" in result.stdout
    assert "/some/parent/path" in result.stdout


def test_python_interpreter_is_used(tmp_path: Path) -> None:
    """The wrapper invokes the CLI under python3.13 from PATH."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(repo, "print-py3")
    assert result.returncode == 0, result.stderr
    # The interpreter used must be python3.13 on the current PATH.
    assert "python=3.13" in result.stdout, (
        f"expected python 3.13, got {result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Behavioral: failure modes
# ---------------------------------------------------------------------------


def test_missing_python313_exits_90(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    bin_dir = tmp_path / "bin"
    path_without_313 = _make_path_without_python313(bin_dir)
    result = _run_wrapper(repo, path_override=path_without_313)
    assert result.returncode == 90, (
        f"expected exit 90 for missing python3.13, got {result.returncode}; "
        f"stderr={result.stderr!r}"
    )
    assert "python3.13" in result.stderr
    assert "not found" in result.stderr


def test_missing_src_huey_exits_91(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path, with_src=False)
    result = _run_wrapper(repo)
    assert result.returncode == 91, (
        f"expected exit 91 for missing src/huey, got {result.returncode}; "
        f"stderr={result.stderr!r}"
    )
    assert "src/huey" in result.stderr


def test_cli_failure_passthrough(tmp_path: Path) -> None:
    """A CLI that raises must produce a nonzero exit, not hang."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(
        repo,
        textwrap.dedent(
            """\
            import sys
            def main() -> int:
                raise RuntimeError("simulated failure")
            """
        ),
    )
    result = _run_wrapper(repo, "boom")
    assert result.returncode != 0
    assert "simulated failure" in result.stderr


# ---------------------------------------------------------------------------
# Consistency with the launcher from Step 13
# ---------------------------------------------------------------------------


def test_wrapper_matches_launcher_contract() -> None:
    """Same invocation contract as scripts/kernel/huey_kernel.py."""
    wrapper_text = WRAPPER.read_text(encoding="utf-8")
    assert "huey.kernel_build.cli" in wrapper_text
    assert "build-kernel" in wrapper_text
