"""Tests for scripts/kernel/verify-modules.sh (Step 26).

Mirrors the Step 23/24/25 wrapper tests, with three subsystem-specific
guards:

1. ``--host-read-only`` (first argument) routes to the CLI's
   ``inventory`` subcommand, not ``verify``. Any other position forwards
   verbatim to ``verify`` (where argparse will reject it).
2. Without ``--host-read-only``, the wrapper invokes ``verify``.
3. Executable code in the wrapper does not invoke subprocess tools
   directly (``modinfo``, ``dpkg-deb``, ``lsinitramfs``, ``nvidia-smi``,
   ``dkms``, ``nvidia-installer``, ``.run``, ``insmod``, ``rmmod``,
   ``mokutil``, ``sudo``, ``curl``, ``wget``, ``git clone``, ``apt``,
   ``apt-get``, ``pip install``, ``ssh``, ``scp``) and does not
   reference live host paths (``/boot``, ``/lib/modules``,
   ``/etc/modprobe.d``, ``/etc/initramfs-tools``).
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
WRAPPER = REPO_ROOT / "scripts" / "kernel" / "verify-modules.sh"


# ---------------------------------------------------------------------------
# Mini-repo helpers
# ---------------------------------------------------------------------------


def _make_mini_repo(tmp_path: Path, *, with_src: bool = True) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts" / "kernel").mkdir(parents=True)
    wrapper_copy = repo / "scripts" / "kernel" / "verify-modules.sh"
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
    # The production CLI has a __main__ guard; the miniature fake needs it too.
    body += "\nif __name__ == '__main__':\n    raise SystemExit(main())\n"
    (repo / "src" / "huey" / "kernel_build" / "cli.py").write_text(
        body, encoding="utf-8"
    )


# Fake CLI that reports which subcommand it was invoked with, plus enough
# behavior to test argv forwarding and exit-code propagation.
_FAKE_CLI = textwrap.dedent(
    """\
    from __future__ import annotations
    import os
    import sys

    def main() -> int:
        args = sys.argv[1:]
        if not args:
            print("subcommand=<none>")
            return 0
        sub = args[0]
        rest = args[1:]
        print(f"subcommand={sub}")
        print(f"argc={len(rest)}")
        for i, a in enumerate(rest, start=1):
            print(f"arg[{i}]={a}")
        print("pp=" + os.environ.get("PYTHONPATH", ""))
        print("python=" + sys.version.split()[0])

        # Exit code control: if any arg is a plain integer, use it.
        for a in rest:
            if a.isdigit():
                return int(a)
        return 0
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
        [str(repo / "scripts" / "kernel" / "verify-modules.sh"), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        check=False,
    )


def _executable_code_lines() -> list[str]:
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
        "verify-modules.sh must be committed executable (git mode 100755)"
    )


def test_wrapper_uses_strict_shell_options() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "set -eu" in text or "set -euo pipefail" in text or "set -e" in text, (
        "verify-modules.sh must use 'set -e' (and ideally 'set -eu')"
    )


def test_wrapper_uses_exec_for_python() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "exec python" in text, (
        "verify-modules.sh must 'exec' the Python process so exit codes, "
        "signals, and stdio pass through unchanged"
    )


def test_wrapper_forwards_quoted_argv() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert '"$@"' in text, (
        "verify-modules.sh must forward argv via '\"$@\"' (quoted)"
    )


def test_wrapper_references_only_cli_subcommands() -> None:
    """The wrapper may reference 'verify' and 'inventory' only."""
    text = "\n".join(_executable_code_lines())
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
            f"verify-modules.sh references {name!r}; that logic belongs in "
            "huey.kernel_build.cli (Step 21) or its components, not in the "
            "wrapper"
        )


def test_wrapper_routes_verify_by_default() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "cli verify" in text, (
        "verify-modules.sh must invoke 'huey.kernel_build.cli verify' by "
        "default"
    )


def test_wrapper_routes_host_read_only_to_inventory() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "--host-read-only" in text, (
        "verify-modules.sh must document and support the --host-read-only "
        "flag"
    )
    assert "cli inventory" in text, (
        "verify-modules.sh must route --host-read-only to the CLI's "
        "'inventory' subcommand, not to 'verify' (host read-only checks "
        "belong to inventory)"
    )


# ---------------------------------------------------------------------------
# Subsystem-specific: not a direct tool invoker
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "forbidden_tool",
    [
        "modinfo",
        "dpkg-deb",
        "lsinitramfs",
        "nvidia-smi",
        "dkms",
        "nvidia-installer",
        ".run",
        "insmod",
        "rmmod",
        "mokutil",
        "update-initramfs",
        "update-grub",
        "mkinitramfs",
        "depmod",
    ],
)
def test_wrapper_invokes_no_tool_directly(forbidden_tool: str) -> None:
    """The wrapper must not invoke any subprocess tool directly.

    All read-only tools flow through the CLI's audited Runner, which
    validates argv and rejects shell interpolation. The wrapper is a
    passthrough only.
    """
    for line in _executable_code_lines():
        assert forbidden_tool not in line, (
            f"verify-modules.sh invokes or references {forbidden_tool!r} in "
            f"executable code; offending line: {line!r}. Read-only tools "
            "must be invoked via the CLI, not the wrapper."
        )


@pytest.mark.parametrize(
    "forbidden_tool",
    ["sudo", "curl", "wget", "ssh", "scp", "apt", "apt-get", "pip"],
)
def test_wrapper_does_not_reference_privileged_or_network_tools(
    forbidden_tool: str,
) -> None:
    for line in _executable_code_lines():
        pattern = rf"\b{re.escape(forbidden_tool)}\b"
        assert not re.search(pattern, line), (
            f"verify-modules.sh references {forbidden_tool!r} in executable "
            f"code; offending line: {line!r}. The wrapper must be "
            "privilege-free and offline."
        )


@pytest.mark.parametrize(
    "forbidden_path",
    ["/boot", "/lib/modules", "/etc/modprobe.d", "/etc/initramfs-tools"],
)
def test_wrapper_does_not_reference_live_host_paths(forbidden_path: str) -> None:
    for line in _executable_code_lines():
        assert forbidden_path not in line, (
            f"verify-modules.sh references {forbidden_path!r} in executable "
            f"code; offending line: {line!r}. Staged-module verification "
            "must not touch live host state."
        )


# ---------------------------------------------------------------------------
# Behavioral: default subcommand (verify)
# ---------------------------------------------------------------------------


def test_default_subcommand_is_verify(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo, "--release-dir", "/tmp/release")
    assert result.returncode == 0, result.stderr
    assert "subcommand=verify" in result.stdout, result.stdout
    assert "arg[1]=--release-dir" in result.stdout
    assert "arg[2]=/tmp/release" in result.stdout


def test_no_args_defaults_to_verify(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo)
    assert result.returncode == 0, result.stderr
    assert "subcommand=verify" in result.stdout


# ---------------------------------------------------------------------------
# Behavioral: --host-read-only dispatch
# ---------------------------------------------------------------------------


def test_host_read_only_routes_to_inventory(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo, "--host-read-only")
    assert result.returncode == 0, result.stderr
    assert "subcommand=inventory" in result.stdout, result.stdout
    assert "subcommand=verify" not in result.stdout


def test_host_read_only_strips_the_flag(tmp_path: Path) -> None:
    """The --host-read-only flag must be consumed by the wrapper."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo, "--host-read-only")
    assert result.returncode == 0
    assert "argc=0" in result.stdout, (
        f"--host-read-only must be consumed; got args: {result.stdout!r}"
    )
    assert "--host-read-only" not in result.stdout


def test_host_read_only_with_extra_args_forwards_them(tmp_path: Path) -> None:
    """Trailing arguments pass through to `inventory`."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo, "--host-read-only", "--json")
    assert result.returncode == 0
    assert "subcommand=inventory" in result.stdout
    assert "arg[1]=--json" in result.stdout


def test_host_read_only_not_first_is_forwarded_to_verify(tmp_path: Path) -> None:
    """Only the first argument triggers the inventory route."""
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo, "--release-dir", "/tmp/r", "--host-read-only")
    assert result.returncode == 0
    assert "subcommand=verify" in result.stdout
    assert "arg[3]=--host-read-only" in result.stdout


# ---------------------------------------------------------------------------
# Behavioral: argv forwarding and inertness
# ---------------------------------------------------------------------------


def test_argv_forwarding_in_order(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(
        repo,
        "--release-dir", "/tmp/release",
        "--kernel-release", "7.2.15-huey1",
        "--driver-version", "580.196.07",
        "--secure-boot-state", "enabled",
    )
    assert result.returncode == 0
    assert "subcommand=verify" in result.stdout
    assert "argc=8" in result.stdout
    assert "arg[1]=--release-dir" in result.stdout
    assert "arg[8]=enabled" in result.stdout


def test_spaces_in_argv_preserved(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo, "--release-dir", "/tmp/some path/release")
    assert result.returncode == 0
    assert "/tmp/some path/release" in result.stdout


def test_shell_metacharacters_inert(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    marker = tmp_path / "should-not-exist"
    payload = f"a b ; touch {marker} ; echo done"
    result = _run_wrapper(repo, payload)
    assert result.returncode == 0, result.stderr
    assert payload in result.stdout, (
        f"payload was mangled: stdout={result.stdout!r}"
    )
    assert not marker.exists(), (
        "wrapper interpreted shell metacharacters from an argv element"
    )


# ---------------------------------------------------------------------------
# Behavioral: exit code passthrough
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("exit_code", [0, 2, 3, 4, 5, 42])
def test_exit_code_forwarded(tmp_path: Path, exit_code: int) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo, str(exit_code))
    assert result.returncode == exit_code, (
        f"expected exit {exit_code}, got {result.returncode}; "
        f"stderr={result.stderr!r}"
    )


# ---------------------------------------------------------------------------
# Behavioral: environment
# ---------------------------------------------------------------------------


def test_pythonpath_contains_repo_src(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo)
    assert result.returncode == 0
    assert f"pp={repo}/src" in result.stdout


def test_pythonpath_preserves_parent_value(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(
        repo, extra_env={"PYTHONPATH": "/some/parent/path"}
    )
    assert result.returncode == 0
    assert f"{repo}/src" in result.stdout
    assert "/some/parent/path" in result.stdout


def test_python_interpreter_is_used(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    result = _run_wrapper(repo)
    assert result.returncode == 0
    assert "python=3.13" in result.stdout, (
        f"expected python 3.13, got {result.stdout!r}"
    )


# ---------------------------------------------------------------------------
# Behavioral: failure modes
# ---------------------------------------------------------------------------


def test_missing_python313_exits_90(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    _install_fake_cli(repo, _FAKE_CLI)
    path_without_313 = _make_path_without_python313(tmp_path / "bin")
    result = _run_wrapper(repo, path_override=path_without_313)
    assert result.returncode == 90, (
        f"expected exit 90 for missing python3.13, got {result.returncode}; "
        f"stderr={result.stderr!r}"
    )
    assert "python3.13" in result.stderr


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
                raise RuntimeError("simulated verify failure")
            """
        ),
    )
    result = _run_wrapper(repo, "boom")
    assert result.returncode != 0
    assert "simulated verify failure" in result.stderr


# ---------------------------------------------------------------------------
# Parity with sibling wrappers
# ---------------------------------------------------------------------------


def test_wrapper_matches_sibling_wrapper_shape() -> None:
    siblings = {
        "build-kernel": REPO_ROOT / "scripts" / "kernel" / "build-kernel.sh",
        "build-nvidia": REPO_ROOT / "scripts" / "kernel" / "build-nvidia.sh",
        "build-initramfs": REPO_ROOT
        / "scripts"
        / "kernel"
        / "build-initramfs.sh",
    }
    a = WRAPPER.read_text(encoding="utf-8")
    for name, path in siblings.items():
        if not path.is_file():
            continue
        b = path.read_text(encoding="utf-8")
        assert "exit 90" in a and "exit 90" in b
        assert "exit 91" in a and "exit 91" in b
        assert "exec python3.13 -m huey.kernel_build.cli " in a
        assert "exec python3.13 -m huey.kernel_build.cli " in b
