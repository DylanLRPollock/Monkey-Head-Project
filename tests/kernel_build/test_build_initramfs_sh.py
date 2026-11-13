"""Tests for scripts/kernel/build-initramfs.sh (Step 25).

Mirrors the Step 23/24 wrapper tests, with subsystem-specific guards:
the wrapper must never invoke mkinitramfs, depmod, lsinitramfs,
update-initramfs, or update-grub directly, and must not reference any of
the live host's initramfs/boot locations (/boot, /etc/initramfs-tools,
/etc/modprobe.d, /lib/modules) in executable code. Those operations go
through the CLI (Step 21) -> initramfs_builder (Step 17), which writes
only under the caller-supplied --output-dir.

Behavioral coverage:
* argv forwarding (including spaces and shell metacharacters, inert);
* --help and --dry-run passthrough;
* CLI exit codes 0, 2, 3, 4, 5, 42 forwarded unchanged;
* missing python3.13 -> exit 90;
* missing src/huey -> exit 91;
* PYTHONPATH injected only with <repo>/src, without clobbering the parent.

Structural coverage:
* shebang, executable bit, strict shell options, exec usage, quoted "$@";
* no reference to components other than the CLI, no subprocess/argparse;
* no direct invocation of mkinitramfs/depmod/lsinitramfs/update-*;
* no reference to live host boot/initramfs paths in executable code.
"""

from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "kernel" / "build-initramfs.sh"


# ---------------------------------------------------------------------------
# Mini-repo helpers (same pattern as Steps 23/24)
# ---------------------------------------------------------------------------


def _make_mini_repo(tmp_path: Path, *, with_src: bool = True) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts" / "kernel").mkdir(parents=True)
    wrapper_copy = repo / "scripts" / "kernel" / "build-initramfs.sh"
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
    (repo / "src" / "huey" / "kernel_build" / "cli.py").write_text(
        body, encoding="utf-8"
    )


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
        [str(repo / "scripts" / "kernel" / "build-initramfs.sh"), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        check=False,
    )


def _executable_code_lines() -> list[str]:
    """Return the wrapper's text with comment lines stripped."""
    text = WRAPPER.read_text(encoding="utf-8")
    return [line for line in text.splitlines() if not line.lstrip().startswith("#")]


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
        "build-initramfs.sh must be committed executable (git mode 100755)"
    )


def test_wrapper_uses_strict_shell_options() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "set -eu" in text or "set -euo pipefail" in text or "set -e" in text, (
        "build-initramfs.sh must use 'set -e' (and ideally 'set -eu')"
    )


def test_wrapper_uses_exec_for_python() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "exec python" in text, (
        "build-initramfs.sh must 'exec' the Python process so exit codes, "
        "signals, and stdio pass through unchanged"
    )


def test_wrapper_forwards_quoted_argv() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert '"$@"' in text, (
        "build-initramfs.sh must forward argv via '\"$@\"' (quoted)"
    )


def test_wrapper_references_only_cli_subcommand() -> None:
    text = "\n".join(_executable_code_lines())
    forbidden = [
        "initramfs_builder",
        "kernel_builder",
        "config_builder",
        "nvidia_builder",
        "release.py",
        "verifier",
        "signing",
        "subprocess",
        "argparse",
    ]
    for name in forbidden:
        assert name not in text, (
            f"build-initramfs.sh references {name!r}; that logic belongs in "
            "huey.kernel_build.cli (Step 21) or its components, not in the "
            "wrapper"
        )


def test_wrapper_targets_initramfs_subcommand() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "cli initramfs" in text, (
        "build-initramfs.sh must exec 'huey.kernel_build.cli initramfs'"
    )


# ---------------------------------------------------------------------------
# Subsystem-specific: not a hidden initramfs generator or boot modifier
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_command",
    [
        "mkinitramfs",
        "update-initramfs",
        "update-grub",
        "depmod",
        "lsinitramfs",
        "initramfs-tools",
        "grub-install",
        "grub-mkconfig",
    ],
)
def test_wrapper_invokes_no_boot_tool_directly(forbidden_command: str) -> None:
    """The wrapper must not run any initramfs/boot tool directly.

    All such operations flow through the CLI so their arguments and target
    paths are validated by initramfs_builder (Step 17). The wrapper is a
    passthrough only.
    """
    for line in _executable_code_lines():
        assert forbidden_command not in line, (
            f"build-initramfs.sh invokes or references {forbidden_command!r} "
            f"in executable code; offending line: {line!r}. These operations "
            "must flow through the CLI, not the wrapper."
        )


@pytest.mark.parametrize(
    "forbidden_path",
    [
        "/boot",
        "/etc/initramfs-tools",
        "/etc/modprobe.d",
        "/lib/modules",
        "/usr/share/initramfs-tools",
    ],
)
def test_wrapper_does_not_reference_live_boot_paths(forbidden_path: str) -> None:
    """The wrapper must not mention live boot/initramfs paths."""
    for line in _executable_code_lines():
        assert forbidden_path not in line, (
            f"build-initramfs.sh references {forbidden_path!r} in executable "
            f"code; offending line: {line!r}. Live boot state is never "
            "touched by a build wrapper."
        )


def test_wrapper_does_not_reference_root_operations() -> None:
    """No sudo in executable code."""
    for line in _executable_code_lines():
        assert not re.search(r"\bsudo\b", line), (
            f"build-initramfs.sh must not invoke sudo; offending line: {line!r}"
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
        repo,
        "argc",
        "--kernel-release", "7.2.15-huey1",
        "--module-tree", "/tmp/tree",
        "--modules-list", "/tmp/modules.list",
        "--modprobe-conf", "/tmp/huey-v100.conf",
        "--output-dir", "/tmp/out",
        "--dry-run",
    )
    assert result.returncode == 0, result.stderr
    assert "argc=11" in result.stdout
    assert "arg[1]=--kernel-release" in result.stdout
    assert "arg[2]=7.2.15-huey1" in result.stdout
    assert "arg[9]=--output-dir" in result.stdout
    assert "arg[10]=/tmp/out" in result.stdout


def test_spaces_in_argv_preserved(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(
        repo, "echo-args",
        "--module-tree", "/tmp/some path/tree",
        "--modprobe-conf", "/tmp/a b c/huey-v100.conf",
    )
    assert result.returncode == 0, result.stderr
    assert "/tmp/some path/tree" in result.stdout
    assert "/tmp/a b c/huey-v100.conf" in result.stdout


def test_shell_metacharacters_inert(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    marker = tmp_path / "should-not-exist"
    payload = f"a b ; touch {marker} ; echo done"
    result = _run_wrapper(repo, "echo-args", payload)
    assert result.returncode == 0, result.stderr
    assert payload in result.stdout, (
        f"payload was mangled: stdout={result.stdout!r}"
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
    assert f"pp={repo}/src" in result.stdout


def test_pythonpath_preserves_parent_value(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(
        repo, "print-pp", extra_env={"PYTHONPATH": "/some/parent/path"}
    )
    assert result.returncode == 0, result.stderr
    assert f"{repo}/src" in result.stdout
    assert "/some/parent/path" in result.stdout


def test_python_interpreter_is_used(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    result = _run_wrapper(repo, "print-py3")
    assert result.returncode == 0, result.stderr
    assert "python=3.13" in result.stdout, (
        f"expected python 3.13, got {result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Behavioral: failure modes
# ---------------------------------------------------------------------------


def test_missing_python313_exits_90(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _DEFAULT_CLI)
    path_without_313 = _make_path_without_python313(tmp_path / "bin")
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
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(
        repo,
        textwrap.dedent(
            """\
            def main() -> int:
                raise RuntimeError("simulated initramfs failure")
            """
        ),
    )
    result = _run_wrapper(repo, "boom")
    assert result.returncode != 0
    assert "simulated initramfs failure" in result.stderr


# ---------------------------------------------------------------------------
# Parity with the Step 23/24 wrappers
# ---------------------------------------------------------------------------


def test_wrapper_matches_sibling_wrapper_shape() -> None:
    """Structural parity with build-kernel.sh and build-nvidia.sh."""
    siblings = {
        "build-kernel": REPO_ROOT / "scripts" / "kernel" / "build-kernel.sh",
        "build-nvidia": REPO_ROOT / "scripts" / "kernel" / "build-nvidia.sh",
    }
    a = WRAPPER.read_text(encoding="utf-8")
    for name, path in siblings.items():
        if not path.is_file():
            continue
        b = path.read_text(encoding="utf-8")
        # Same environment exit codes.
        assert "exit 90" in a and "exit 90" in b
        assert "exit 91" in a and "exit 91" in b
        # Same exec pattern (differ only by subcommand name).
        assert "exec python3.13 -m huey.kernel_build.cli " in a
        assert "exec python3.13 -m huey.kernel_build.cli " in b
