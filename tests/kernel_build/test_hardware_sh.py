"""Tests for scripts/kernel/test-hardware.sh (Step 27).

All tests run offline. The inventory command, GPU smoke commands, and
BOOT_DIR are overridable via environment variables so the wrapper can be
exercised without a real GPU, without root, and without touching the live
/boot.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WRAPPER = REPO_ROOT / "scripts" / "kernel" / "test-hardware.sh"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mini_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "scripts" / "kernel").mkdir(parents=True)
    shutil.copy2(WRAPPER, repo / "scripts" / "kernel" / "test-hardware.sh")
    os.chmod(repo / "scripts" / "kernel" / "test-hardware.sh", 0o755)
    (repo / "src" / "huey").mkdir(parents=True)
    return repo


def _make_boot_dir(
    tmp_path: Path,
    *,
    initramfs: tuple[str, ...] = ("initrd.img-7.2.15+deb14-amd64",),
    configs: tuple[str, ...] = ("config-7.2.15+deb14-amd64",),
) -> Path:
    boot = tmp_path / "boot"
    boot.mkdir()
    for name in initramfs:
        (boot / name).write_bytes(b"fake initramfs\n")
    for name in configs:
        (boot / name).write_text("CONFIG_MODULES=y\n", encoding="utf-8")
    return boot


_FAKE_INVENTORY_JSON = (
    '{"subcommand":"inventory","status":"ok","exit_code":0,'
    '"message":"kernel=7.2.15+deb14-amd64 secureboot=disabled gpus=2",'
    '"payload":{"running_kernel":"7.2.15+deb14-amd64","secure_boot":"disabled",'
    '"gpus":[],"driver":null,"findings":[]}}\n'
)


def _run_wrapper(
    repo: Path,
    *args: str,
    extra_env: dict[str, str] | None = None,
    path_override: str | None = None,
    timeout: float = 30.0,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    env["HUEY_TEST_HARDWARE_INVENTORY_CMD"] = (
        f"printf '%s' '{_FAKE_INVENTORY_JSON.strip()}'"
    )
    env["HUEY_TEST_HARDWARE_CUDA_CMD"] = "echo fake-cuda-device"
    env["HUEY_TEST_HARDWARE_OLLAMA_CMD"] = "echo fake-ollama-list"
    env["HUEY_TEST_HARDWARE_COMFYUI_CMD"] = "echo fake-comfyui-process"
    if path_override is not None:
        env["PATH"] = path_override
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [str(repo / "scripts" / "kernel" / "test-hardware.sh"), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=timeout,
        check=False,
    )


def _make_path_without_python313(bin_dir: Path) -> str:
    bin_dir.mkdir(exist_ok=True)
    for tool in ("sh", "env", "dirname", "pwd", "cd", "printf", "mktemp", "tr",
                 "cut", "head", "sed", "ls", "rm", "cat"):
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
    import stat as _stat
    assert WRAPPER.stat().st_mode & _stat.S_IXUSR


def test_wrapper_uses_set_e() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert "set -eu" in text or "set -e" in text


def test_wrapper_writes_only_to_tmp_and_log() -> None:
    """The script must only write to $tmp_dir or $LOG_FILE."""
    text = "\n".join(line for line in _executable_code_lines() if "->" not in line)
    # All target paths of "> " and ">> " redirects.
    targets = re.findall(r">>?\s*\"?([^\s\"'>]+)", text)
    for target in targets:
        assert (
            target.startswith("$tmp_dir")
            or target.startswith("${tmp_dir}")
            or target.startswith("$LOG_FILE")
            or target.startswith("${LOG_FILE}")
            or target == "/dev/null"
            or target == "&2"
            or re.fullmatch(r"&[0-9]+;?", target) is not None
        ), f"unexpected write target in wrapper: {target!r}"


@pytest.mark.parametrize(
    "forbidden_command",
    [
        "sudo",
        "nvidia-installer",
        "NVIDIA-Linux-",
        "dkms install",
        "dpkg -i",
        "apt install",
        "apt-get install",
        "update-initramfs",
        "update-grub",
        "mkinitramfs",
        "nvidia-smi --gpu-reset",
        "nvidia-smi -r",
        "insmod",
        "rmmod",
        "modprobe",
        "mokutil --import",
    ],
)
def test_wrapper_is_not_a_mutator(forbidden_command: str) -> None:
    """No privileged or mutating commands in executable code."""
    for line in _executable_code_lines():
        assert forbidden_command not in line, (
            f"test-hardware.sh must not contain {forbidden_command!r} in "
            f"executable code; offending line: {line!r}"
        )


@pytest.mark.parametrize(
    "forbidden_path",
    ["/etc/modprobe.d", "/etc/initramfs-tools", "/lib/modules"],
)
def test_wrapper_does_not_write_live_boot_paths(forbidden_path: str) -> None:
    """The script may read /boot but must never write live host state."""
    for line in _executable_code_lines():
        # Allow reads (ls, test -d) but forbid redirects/touch/mkdir/cp/mv.
        if forbidden_path not in line:
            continue
        assert not re.search(
            r"(>\s*\"?" + re.escape(forbidden_path) + r"|touch\s+" +
            re.escape(forbidden_path) + r"|mkdir\s+" +
            re.escape(forbidden_path) + r"|cp\s+[^\n]*\s+" +
            re.escape(forbidden_path) + r"|mv\s+[^\n]*\s+" +
            re.escape(forbidden_path) + r")",
            line,
        ), f"test-hardware.sh must not write to {forbidden_path}: {line!r}"


# ---------------------------------------------------------------------------
# Help and argument errors
# ---------------------------------------------------------------------------


def test_help_exit_zero(monkeypatch) -> None:
    import subprocess as _sp
    result = _sp.run(
        [str(WRAPPER), "--help"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "--gpu-smoke" in result.stdout
    assert "--yes" in result.stdout


def test_unknown_argument_exit_2(monkeypatch, tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    result = _run_wrapper(repo, "--not-a-flag")
    assert result.returncode == 2
    assert "unknown argument" in result.stderr


def test_log_without_argument_exit_2(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    result = _run_wrapper(repo, "--log")
    assert result.returncode == 2
    assert "--log requires an argument" in result.stderr


# ---------------------------------------------------------------------------
# Prerequisite failures
# ---------------------------------------------------------------------------


def test_missing_python313_exits_90(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    path_override = _make_path_without_python313(tmp_path / "bin")
    result = _run_wrapper(repo, path_override=path_override)
    assert result.returncode == 90, (
        f"expected 90, got {result.returncode}; stderr={result.stderr!r}"
    )
    assert "python3.13" in result.stderr


def test_missing_src_huey_exits_91(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    (repo / "src" / "huey").rmdir()
    result = _run_wrapper(repo)
    assert result.returncode == 91, (
        f"expected 91, got {result.returncode}; stderr={result.stderr!r}"
    )
    assert "src/huey" in result.stderr


# ---------------------------------------------------------------------------
# Default (read-only) run
# ---------------------------------------------------------------------------


def test_default_run_text_ok(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    result = _run_wrapper(
        repo, extra_env={"HUEY_TEST_HARDWARE_BOOT_DIR": str(boot)},
    )
    assert result.returncode == 0, result.stderr
    assert "HueyOS host smoke report" in result.stdout
    assert "inventory" in result.stdout
    assert "boot_initramfs" in result.stdout
    assert "gpu_smoke:cuda" in result.stdout
    # GPU smoke skipped by default (no --gpu-smoke)
    cuda_line = next(
        line for line in result.stdout.splitlines() if "gpu_smoke:cuda" in line
    )
    assert "skip" in cuda_line
    assert "Result: OK" in result.stdout


def test_default_run_does_not_invoke_gpu_smoke(tmp_path: Path) -> None:
    """Without --gpu-smoke the GPU commands must not run."""
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    marker = tmp_path / "gpu-ran"
    result = _run_wrapper(
        repo,
        extra_env={
            "HUEY_TEST_HARDWARE_BOOT_DIR": str(boot),
            "HUEY_TEST_HARDWARE_CUDA_CMD": f"touch {marker} && echo ran",
            "HUEY_TEST_HARDWARE_OLLAMA_CMD": f"touch {marker} && echo ran",
            "HUEY_TEST_HARDWARE_COMFYUI_CMD": f"touch {marker} && echo ran",
        },
    )
    assert result.returncode == 0
    assert not marker.exists(), "GPU smoke commands ran without --gpu-smoke"


def test_default_json_schema(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    result = _run_wrapper(
        repo, "--json",
        extra_env={"HUEY_TEST_HARDWARE_BOOT_DIR": str(boot)},
    )
    assert result.returncode == 0, result.stderr
    doc = json.loads(result.stdout)
    assert doc["schema_version"] == 1
    assert "inventory" in doc
    assert "checks" in doc
    assert "summary" in doc
    names = {c["name"] for c in doc["checks"]}
    assert names == {
        "inventory", "boot_initramfs", "boot_config",
        "gpu_smoke:cuda", "gpu_smoke:ollama", "gpu_smoke:comfyui",
    }
    statuses = {c["name"]: c["status"] for c in doc["checks"]}
    assert statuses["inventory"] == "pass"
    assert statuses["boot_initramfs"] == "pass"
    assert statuses["boot_config"] == "pass"
    assert statuses["gpu_smoke:cuda"] == "skip"
    # Summary counts add up
    assert sum(doc["summary"].values()) == len(doc["checks"])


def test_missing_initramfs_is_warn(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path, initramfs=(), configs=("config-x",))
    result = _run_wrapper(
        repo, "--json",
        extra_env={"HUEY_TEST_HARDWARE_BOOT_DIR": str(boot)},
    )
    doc = json.loads(result.stdout)
    statuses = {c["name"]: c["status"] for c in doc["checks"]}
    assert statuses["boot_initramfs"] == "warn"
    # Warnings do not fail the run
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Inventory failure
# ---------------------------------------------------------------------------


def test_inventory_failure_is_fail(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    result = _run_wrapper(
        repo, "--json",
        extra_env={
            "HUEY_TEST_HARDWARE_BOOT_DIR": str(boot),
            "HUEY_TEST_HARDWARE_INVENTORY_CMD": "false",
        },
    )
    assert result.returncode == 4, (
        f"expected 4, got {result.returncode}; stdout={result.stdout!r}"
    )
    doc = json.loads(result.stdout)
    statuses = {c["name"]: c["status"] for c in doc["checks"]}
    assert statuses["inventory"] == "fail"


# ---------------------------------------------------------------------------
# GPU smoke: skip paths
# ---------------------------------------------------------------------------


def test_gpu_smoke_without_yes_non_tty_skips(tmp_path: Path) -> None:
    """--gpu-smoke without --yes on a non-TTY is skipped, not run."""
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    result = _run_wrapper(
        repo, "--gpu-smoke", "--json",
        extra_env={
            "HUEY_TEST_HARDWARE_BOOT_DIR": str(boot),
            "HUEY_TEST_HARDWARE_CUDA_CMD": "false",
            "HUEY_TEST_HARDWARE_OLLAMA_CMD": "false",
            "HUEY_TEST_HARDWARE_COMFYUI_CMD": "false",
        },
    )
    doc = json.loads(result.stdout)
    statuses = {c["name"]: c["status"] for c in doc["checks"]}
    assert statuses["gpu_smoke:cuda"] == "skip"
    assert statuses["gpu_smoke:ollama"] == "skip"
    assert statuses["gpu_smoke:comfyui"] == "skip"
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# GPU smoke: run paths
# ---------------------------------------------------------------------------


def test_gpu_smoke_with_yes_runs_commands(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    marker_cuda = tmp_path / "cuda-ran"
    marker_ollama = tmp_path / "ollama-ran"
    marker_comfyui = tmp_path / "comfyui-ran"
    result = _run_wrapper(
        repo, "--gpu-smoke", "--yes", "--json",
        extra_env={
            "HUEY_TEST_HARDWARE_BOOT_DIR": str(boot),
            "HUEY_TEST_HARDWARE_CUDA_CMD": f"touch {marker_cuda} && echo nvidia-v100",
            "HUEY_TEST_HARDWARE_OLLAMA_CMD": f"touch {marker_ollama} && echo ollama-ok",
            "HUEY_TEST_HARDWARE_COMFYUI_CMD": f"touch {marker_comfyui} && echo comfyui-ok",
        },
    )
    assert marker_cuda.exists(), "CUDA command did not run"
    assert marker_ollama.exists(), "Ollama command did not run"
    assert marker_comfyui.exists(), "ComfyUI command did not run"
    doc = json.loads(result.stdout)
    statuses = {c["name"]: c["status"] for c in doc["checks"]}
    assert statuses["gpu_smoke:cuda"] == "pass"
    assert statuses["gpu_smoke:ollama"] == "pass"
    assert statuses["gpu_smoke:comfyui"] == "pass"
    assert result.returncode == 0


def test_gpu_smoke_failure_is_fail(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    result = _run_wrapper(
        repo, "--gpu-smoke", "--yes", "--json",
        extra_env={
            "HUEY_TEST_HARDWARE_BOOT_DIR": str(boot),
            "HUEY_TEST_HARDWARE_CUDA_CMD": "false",
            "HUEY_TEST_HARDWARE_OLLAMA_CMD": "true",
            "HUEY_TEST_HARDWARE_COMFYUI_CMD": "echo fake-comfyui-process",
        },
    )
    assert result.returncode == 4, (
        f"expected 4, got {result.returncode}; stdout={result.stdout!r}"
    )
    doc = json.loads(result.stdout)
    statuses = {c["name"]: c["status"] for c in doc["checks"]}
    assert statuses["gpu_smoke:cuda"] == "fail"
    assert statuses["gpu_smoke:ollama"] == "pass"
    assert statuses["gpu_smoke:comfyui"] == "pass"


def test_gpu_smoke_comfyui_not_running_is_warn(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    result = _run_wrapper(
        repo, "--gpu-smoke", "--yes", "--json",
        extra_env={
            "HUEY_TEST_HARDWARE_BOOT_DIR": str(boot),
            "HUEY_TEST_HARDWARE_CUDA_CMD": "echo ok",
            "HUEY_TEST_HARDWARE_OLLAMA_CMD": "echo ok",
            # ComfyUI command succeeds but produces no output -> warn
            "HUEY_TEST_HARDWARE_COMFYUI_CMD": "true",
        },
    )
    doc = json.loads(result.stdout)
    statuses = {c["name"]: c["status"] for c in doc["checks"]}
    assert statuses["gpu_smoke:comfyui"] == "warn"
    # A warn does not fail the run
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# --log file
# ---------------------------------------------------------------------------


def test_log_file_captures_checks(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    log = tmp_path / "hw.log"
    result = _run_wrapper(
        repo, "--log", str(log),
        extra_env={"HUEY_TEST_HARDWARE_BOOT_DIR": str(boot)},
    )
    assert result.returncode == 0
    assert log.is_file()
    text = log.read_text(encoding="utf-8")
    assert "inventory:" in text
    assert "boot_initramfs:" in text
    assert "gpu_smoke:cuda:" in text


# ---------------------------------------------------------------------------
# Text mode summary
# ---------------------------------------------------------------------------


def test_text_mode_shows_all_checks(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    result = _run_wrapper(
        repo, extra_env={"HUEY_TEST_HARDWARE_BOOT_DIR": str(boot)}
    )
    for name in (
        "inventory", "boot_initramfs", "boot_config",
        "gpu_smoke:cuda", "gpu_smoke:ollama", "gpu_smoke:comfyui",
    ):
        assert name in result.stdout


def test_text_mode_failure_shows_count(tmp_path: Path) -> None:
    repo = _make_mini_repo(tmp_path)
    boot = _make_boot_dir(tmp_path)
    result = _run_wrapper(
        repo,
        extra_env={
            "HUEY_TEST_HARDWARE_BOOT_DIR": str(boot),
            "HUEY_TEST_HARDWARE_INVENTORY_CMD": "false",
        },
    )
    assert result.returncode == 4
    assert "Result: FAIL" in result.stdout
    assert "(1 failing check(s))" in result.stdout
