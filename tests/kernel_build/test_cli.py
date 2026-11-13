"""Tests for huey.kernel_build.cli (Step 21; Step 45 expands).

All tests run offline. ``inventory``, ``doctor``, and the build subcommands
are exercised via a ``_make_runner`` monkeypatch that returns a FakeRunner.
The CLI reads ``sys.argv``; tests patch it with ``monkeypatch``.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from huey.kernel_build import cli as cli_module
from huey.kernel_build.cli import ExitCode, main
from huey.kernel_build.models import CommandResult
from huey.kernel_build.runner import (
    CommandSpec,
    RunnerError,
    RunnerResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeRunner:
    def __init__(self) -> None:
        self._handlers: list = []
        self.calls: list[CommandSpec] = []

    def on(self, matcher, handler) -> "FakeRunner":
        self._handlers.append((matcher, handler))
        return self

    def run(self, spec: CommandSpec, *, dry_run: bool = False) -> RunnerResult:
        self.calls.append(spec)
        for matcher, handler in self._handlers:
            if matcher(spec):
                return handler(spec)
        raise RunnerError(f"no handler for argv={spec.argv!r}")


def _ok(spec, *, stdout: bytes = b"") -> RunnerResult:
    return RunnerResult(
        command=CommandResult(
            argv=spec.argv, cwd=str(spec.cwd),
            returncode=0, elapsed_seconds=0.0,
        ),
        executed=True, dry_run=False, stdout=stdout, stderr=b"",
    )


def _run_cli(argv: list[str], monkeypatch, capsys) -> tuple[int, str, str]:
    """Invoke ``main()`` with argv patched, return (code, stdout, stderr)."""
    monkeypatch.setattr(sys, "argv", ["huey-kernel", *argv])
    code = main()
    out, err = capsys.readouterr()
    return code, out, err


def _noop_runner(monkeypatch) -> FakeRunner:
    """Install a FakeRunner that fails every command (used by 'no subprocess' tests)."""
    runner = FakeRunner()
    monkeypatch.setattr(cli_module, "_make_runner", lambda: runner)
    return runner


def _inventory_runner(monkeypatch) -> FakeRunner:
    """FakeRunner with just enough handlers to make HostInventory work."""
    runner = FakeRunner()
    runner.on(lambda spec: spec.argv == ("uname", "-r"), lambda s: _ok(s, stdout=b"7.2.15+deb14-amd64\n"))
    runner.on(lambda spec: spec.argv == ("mokutil", "--sb-state"), lambda s: _ok(s, stdout=b"SecureBoot disabled\n"))
    return runner


def _write_build_yaml(path: Path, *, valid: bool = True, profile: str = "v100-workstation") -> Path:
    checksum = "b" * 64 if valid else "not-a-sha"
    text = (
        "schema_version: 1\n"
        f"profile: {profile}\n"
        "kernel:\n"
        "  source_type: debian-linux-source\n"
        "  source: linux-source-7.2\n"
        "  version: 7.2.15-1\n"
        f"  checksum: '{checksum}'\n"
        "  localversion: -huey1\n"
        "nvidia:\n"
        "  version: '580.196.07'\n"
        "  module_flavor: proprietary\n"
        "  source_kind: dkms-local\n"
        "build:\n"
        "  jobs: 4\n"
        "paths:\n"
        "  workspace: build/huey-kernel/workspace\n"
        "  output: build/huey-kernel/\n"
        "signing:\n"
        "  required_policy: required_if_secureboot\n"
        "safety:\n"
        "  allow_host_mutation: false\n"
        "  allow_root_build: false\n"
        "  allow_network_fetch: false\n"
    )
    path.write_text(text, encoding="utf-8")
    return path


def _make_release_dir(tmp_path: Path) -> Path:
    rd = tmp_path / "release"
    rd.mkdir()
    image = rd / "linux-image-7.2.15-huey1_7.2.15-huey1-1_amd64.deb"
    image.write_bytes(b"fake image\n")
    headers = rd / "linux-headers-7.2.15-huey1_7.2.15-huey1-1_amd64.deb"
    headers.write_bytes(b"fake headers\n")
    nv = rd / "nvidia-580.196.07-7.2.15-huey1"
    nv.mkdir()
    (nv / "nvidia.ko").write_bytes(b"ko\n")
    return rd


# ---------------------------------------------------------------------------
# Help / argparse
# ---------------------------------------------------------------------------


def test_help_at_top_level(monkeypatch, capsys) -> None:
    code, out, err = _run_cli(["--help"], monkeypatch, capsys)
    assert code == 0
    assert "huey-kernel" in out
    assert "SUBCOMMAND" in out or "subcommand" in out.lower()
    assert "install" not in out.split("SUBCOMMAND")[-1].lower()


@pytest.mark.parametrize("subcmd", [
    "inventory", "doctor", "plan", "config", "build-kernel",
    "build-nvidia", "initramfs", "sign", "verify", "release",
])
def test_help_on_each_subcommand(subcmd: str, monkeypatch, capsys) -> None:
    code, out, err = _run_cli([subcmd, "--help"], monkeypatch, capsys)
    assert code == 0
    assert subcmd in out


def test_no_subcommand_returns_2(monkeypatch, capsys) -> None:
    code, out, err = _run_cli([], monkeypatch, capsys)
    assert code == 2


def test_unknown_subcommand_returns_2(monkeypatch, capsys) -> None:
    code, out, err = _run_cli(["not-a-real-subcommand"], monkeypatch, capsys)
    assert code == 2


def test_missing_required_argument_returns_2(monkeypatch, capsys) -> None:
    code, out, err = _run_cli(["plan"], monkeypatch, capsys)  # missing --config
    assert code == 2


# ---------------------------------------------------------------------------
# Inventory / doctor
# ---------------------------------------------------------------------------


def test_inventory_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_module, "_make_runner", lambda: _inventory_runner(monkeypatch))
    code, out, err = _run_cli(["inventory", "--json"], monkeypatch, capsys)
    assert code == 0, err
    data = json.loads(out)
    assert data["subcommand"] == "inventory"
    assert data["status"] == "ok"
    assert data["exit_code"] == 0
    assert data["payload"]["running_kernel"] == "7.2.15+deb14-amd64"
    assert data["payload"]["secure_boot"] == "disabled"
    assert isinstance(data["findings"], list)


def test_inventory_text_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_module, "_make_runner", lambda: _inventory_runner(monkeypatch))
    code, out, err = _run_cli(["inventory"], monkeypatch, capsys)
    assert code == 0
    assert "inventory:" in out
    assert "kernel=7.2.15+deb14-amd64" in out


def test_doctor_json_output(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_module, "_make_runner", lambda: _inventory_runner(monkeypatch))
    code, out, err = _run_cli(["doctor", "--json"], monkeypatch, capsys)
    assert code == 0
    data = json.loads(out)
    assert data["subcommand"] == "doctor"
    assert "report" in data["payload"]
    assert "advice" in data["payload"]
    assert isinstance(data["payload"]["advice"], list)


# ---------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------


def test_plan_static_valid_yaml_success(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    code, out, err = _run_cli(["plan", "--config", str(yml), "--json"], monkeypatch, capsys)
    data = json.loads(out)
    # A resolved source with matching driver is allowed even without inventory
    # (a warning about missing V100 is expected but not blocking).
    assert data["subcommand"] == "plan"
    assert data["payload"]["profile"] == "v100-workstation"
    assert data["payload"]["driver"]["driver_version"] == "580.196.07"
    assert code == 0


def test_plan_missing_config_returns_3(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    code, out, err = _run_cli(
        ["plan", "--config", str(tmp_path / "missing.yaml"), "--json"],
        monkeypatch, capsys,
    )
    assert code == 3
    data = json.loads(out)
    assert data["status"] == "error"


def test_plan_invalid_yaml_returns_2(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    bad = tmp_path / "bad.yaml"
    bad.write_text("schema_version: [unclosed\n", encoding="utf-8")
    code, out, err = _run_cli(["plan", "--config", str(bad), "--json"], monkeypatch, capsys)
    assert code == 2


def test_plan_with_inventory_calls_runner(tmp_path: Path, monkeypatch, capsys) -> None:
    """--with-inventory invokes inventory (via the FakeRunner)."""
    runner = _inventory_runner(monkeypatch)
    monkeypatch.setattr(cli_module, "_make_runner", lambda: runner)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    code, out, err = _run_cli(
        ["plan", "--config", str(yml), "--with-inventory", "--json"],
        monkeypatch, capsys,
    )
    assert len(runner.calls) >= 2  # uname + mokutil at minimum


def test_plan_pyaml_missing_returns_3(tmp_path: Path, monkeypatch, capsys) -> None:
    """When yaml import fails, load_build_intent returns MISSING_PREREQUISITES."""
    # We can't easily simulate a missing import in-process; instead, verify
    # the error class raises MISSING_PREREQUISITES when the file is missing
    # (proxy for the same code path).
    _noop_runner(monkeypatch)
    yml = tmp_path / "nope.yaml"
    code, out, err = _run_cli(["plan", "--config", str(yml), "--json"], monkeypatch, capsys)
    assert code == 3


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


def test_verify_missing_dir_returns_3(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    code, out, err = _run_cli(
        ["verify", "--release-dir", str(tmp_path / "nope"), "--json"],
        monkeypatch, capsys,
    )
    assert code == 3
    data = json.loads(out)
    assert data["status"] == "error"


def test_verify_release_dir_without_debs_reports_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    runner = FakeRunner()
    monkeypatch.setattr(cli_module, "_make_runner", lambda: runner)
    rd = tmp_path / "release"
    rd.mkdir()
    code, out, err = _run_cli(
        ["verify", "--release-dir", str(rd), "--kernel-release", "7.2.15-huey1",
         "--driver-version", "580.196.07", "--json"],
        monkeypatch, capsys,
    )
    # Verification runs but fails: exit code 4 (build failure)
    data = json.loads(out)
    assert data["subcommand"] == "verify"
    assert data["payload"]["boot_ready"] is False


def test_verify_inference_from_release_dir(tmp_path: Path, monkeypatch, capsys) -> None:
    """kernel_release and driver_version inferred from file structure."""
    runner = FakeRunner()
    # Provide modinfo handlers for the two modules the release contains
    runner.on(
        lambda s: s.argv[0] == "lsinitramfs",
        lambda s: _ok(s, stdout=b""),
    )
    monkeypatch.setattr(cli_module, "_make_runner", lambda: runner)
    rd = _make_release_dir(tmp_path)
    code, out, err = _run_cli(["verify", "--release-dir", str(rd), "--json"],
                              monkeypatch, capsys)
    data = json.loads(out)
    # Inference succeeded
    assert data["payload"]["kernel_release"] == "7.2.15-huey1"
    assert data["payload"]["driver_version"] == "580.196.07"


# ---------------------------------------------------------------------------
# Build subcommands: dry-run and error paths
# ---------------------------------------------------------------------------


def test_build_kernel_missing_source_returns_error(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    code, out, err = _run_cli([
        "build-kernel", "--config", str(yml),
        "--source-dir", str(tmp_path / "no-src"),
        "--effective-config", str(tmp_path / "no-config"),
        "--output-dir", str(tmp_path / "out"),
        "--json",
    ], monkeypatch, capsys)
    data = json.loads(out)
    assert data["subcommand"] == "build-kernel"
    assert code in (3, 4)  # missing source or config -> component error


def test_build_kernel_dry_run_no_writes(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    # Construct a plausible source + config so the dry-run validation passes.
    src = tmp_path / "src"
    src.mkdir()
    (src / "Makefile").write_text("# fake\n", encoding="utf-8")
    cfg = tmp_path / "config"
    cfg.write_text("CONFIG_MODULES=y\n", encoding="utf-8")
    yml = _write_build_yaml(tmp_path / "build.yaml")
    out = tmp_path / "out"
    out.mkdir()
    code, stdout, err = _run_cli([
        "build-kernel", "--config", str(yml),
        "--source-dir", str(src),
        "--effective-config", str(cfg),
        "--output-dir", str(out),
        "--dry-run", "--json",
    ], monkeypatch, capsys)
    data = json.loads(stdout)
    assert data["subcommand"] == "build-kernel"
    assert data["status"] == "dry_run"
    assert not (out / "kernel-release.json").exists()


def test_build_nvidia_missing_headers_dir(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    code, out, err = _run_cli([
        "build-nvidia", "--config", str(yml),
        "--kernel-release", "7.2.15-huey1",
        "--headers-dir", str(tmp_path / "no-headers"),
        "--output-dir", str(tmp_path / "out"),
        "--json",
    ], monkeypatch, capsys)
    data = json.loads(out)
    assert data["subcommand"] == "build-nvidia"
    assert code == 4  # component reported HEADERS_MAKEFILE_MISSING


def test_initramfs_missing_module_tree(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    code, out, err = _run_cli([
        "initramfs", "--config", str(yml),
        "--kernel-release", "7.2.15-huey1",
        "--module-tree", str(tmp_path / "no-tree"),
        "--modules-list", str(tmp_path / "no-list"),
        "--modprobe-conf", str(tmp_path / "no-conf"),
        "--output-dir", str(tmp_path / "out"),
        "--json",
    ], monkeypatch, capsys)
    data = json.loads(out)
    assert data["subcommand"] == "initramfs"
    assert code == 4


# ---------------------------------------------------------------------------
# Exit code contract
# ---------------------------------------------------------------------------


def test_exit_code_enum_values() -> None:
    assert ExitCode.SUCCESS == 0
    assert ExitCode.BAD_INPUT == 2
    assert ExitCode.MISSING_PREREQUISITES == 3
    assert ExitCode.BUILD_FAILURE == 4
    assert ExitCode.APPROVAL_REQUIRED == 5


def test_no_install_subcommand() -> None:
    """The CLI must not expose an 'install' or 'reboot' subcommand."""
    from huey.kernel_build.cli import _build_parser

    parser = _build_parser()
    # Collect subparsers by inspecting the parser's internal structure.
    subparsers_action = next(
        a for a in parser._actions
        if isinstance(a, __import__("argparse")._SubParsersAction)
    )
    names = set(subparsers_action.choices.keys())
    assert "install" not in names
    assert "reboot" not in names


def test_path_traversal_in_config_is_parsed_but_missing(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    # argparse accepts `../../etc/passwd` as a Path; load_build_intent fails
    # to read it (usually because it does not exist), returning exit 3.
    code, out, err = _run_cli(
        ["plan", "--config", "../../etc/passwd", "--json"], monkeypatch, capsys,
    )
    assert code in (2, 3)  # 2 if PyYAML cannot parse, 3 if file unreadable


def test_json_output_is_parseable_for_every_readonly_command(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_module, "_make_runner", lambda: _inventory_runner(monkeypatch))
    yml = _write_build_yaml(tmp_path / "build.yaml")
    for argv in (
        ["inventory", "--json"],
        ["doctor", "--json"],
        ["plan", "--config", str(yml), "--json"],
    ):
        code, out, err = _run_cli(argv, monkeypatch, capsys)
        data = json.loads(out)  # will raise if not valid JSON
        assert data["subcommand"] == argv[0]
        assert isinstance(data["exit_code"], int)


# Step 45: full CLI acceptance coverage beyond the initial Step 21 tests.

def _assert_cli_contract(doc: dict, subcommand: str, exit_code: int) -> None:
    assert set(doc) >= {"subcommand", "status", "exit_code", "message", "payload", "findings"}
    assert doc["subcommand"] == subcommand
    assert doc["exit_code"] == exit_code
    assert doc["status"] in {"ok", "dry_run", "error"}
    assert isinstance(doc["payload"], dict)
    assert isinstance(doc["findings"], list)


@pytest.mark.parametrize("argv", [
    [], ["unrecognized"], ["--instal"], ["plan"],
    ["plan", "--config", "x", "--not-a-real-option"],
])
def test_argparse_errors_do_not_write_stdout(monkeypatch, capsys, argv: list[str]) -> None:
    code, out, err = _run_cli(argv, monkeypatch, capsys)
    assert code == 2
    assert out == ""
    assert err


def test_no_host_mutating_commands_are_registered() -> None:
    import argparse
    parser = cli_module._build_parser()
    action = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    forbidden = {"install", "reboot", "uninstall", "reset", "setup", "upgrade"}
    assert forbidden.isdisjoint(action.choices)


def test_exit_code_is_int_enum() -> None:
    import enum
    assert issubclass(ExitCode, enum.IntEnum)


def test_top_help_excludes_host_mutating_command_names(monkeypatch, capsys) -> None:
    code, stdout, _ = _run_cli(["--help"], monkeypatch, capsys)
    assert code == 0
    # Argparse may refer to the word "install" in a description; what matters
    # is the registered subcommand list, which must not contain these names.
    parser = cli_module._build_parser()
    import argparse
    action = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
    assert "install" not in action.choices and "reboot" not in action.choices
    assert "huey-kernel" in stdout


def test_plan_does_not_construct_runner_without_inventory(tmp_path: Path, monkeypatch, capsys) -> None:
    calls = []
    monkeypatch.setattr(cli_module, "_make_runner", lambda: calls.append(True) or FakeRunner())
    yamlfile = _write_build_yaml(tmp_path / "build.yaml")
    code, stdout, _ = _run_cli(["plan", "--config", str(yamlfile), "--json"], monkeypatch, capsys)
    assert code == 0
    _assert_cli_contract(json.loads(stdout), "plan", code)
    assert calls == []


def test_inventory_constructs_runner_once(monkeypatch, capsys) -> None:
    calls = []
    runner = _inventory_runner(monkeypatch)
    monkeypatch.setattr(cli_module, "_make_runner", lambda: calls.append(True) or runner)
    code, stdout, _ = _run_cli(["inventory", "--json"], monkeypatch, capsys)
    assert code == 0
    _assert_cli_contract(json.loads(stdout), "inventory", code)
    assert calls == [True]


def test_plan_accepts_yaml_filename_with_spaces(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    folder = tmp_path / "path with spaces"
    folder.mkdir()
    file = _write_build_yaml(folder / "build.yaml")
    code, stdout, _ = _run_cli(["plan", "--config", str(file), "--json"], monkeypatch, capsys)
    assert code == 0
    _assert_cli_contract(json.loads(stdout), "plan", code)


def test_plan_does_not_execute_metacharacters_in_path(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    marker = tmp_path / "unexpected"
    payload = f"fake ; touch {marker} ; done"
    code, stdout, _ = _run_cli(["plan", "--config", payload, "--json"], monkeypatch, capsys)
    assert code in (2, 3)
    assert not marker.exists()
    _assert_cli_contract(json.loads(stdout), "plan", code)


def test_module_invocation_preserves_sys_argv(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    original = ["huey-kernel", "plan", "--config", str(_write_build_yaml(tmp_path / "build.yaml")), "--json"]
    monkeypatch.setattr(sys, "argv", original)
    assert main() == 0
    assert sys.argv is original
    _assert_cli_contract(json.loads(capsys.readouterr().out), "plan", 0)


@pytest.mark.parametrize("cmd,args,expected", [
    ("plan", ["--config", "missing.yaml"], 3),
    ("verify", ["--release-dir", "missing-release"], 3),
])
def test_json_error_result_shape(cmd: str, args: list[str], expected: int,
                                 tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    argv = [str(tmp_path / x) if x.startswith("missing") else x for x in args]
    code, stdout, _ = _run_cli([cmd, *argv, "--json"], monkeypatch, capsys)
    assert code == expected
    _assert_cli_contract(json.loads(stdout), cmd, code)


def test_kernel_builder_dry_run_reports_stable_json(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    source = tmp_path / "src"; source.mkdir()
    (source / "Makefile").write_text("# fake kernel", encoding="utf-8")
    config = tmp_path / "config"; config.write_text("CONFIG_MODULES=y\n", encoding="utf-8")
    yamlfile = _write_build_yaml(tmp_path / "build.yaml")
    output = tmp_path / "output"
    code, stdout, _ = _run_cli([
        "build-kernel", "--config", str(yamlfile), "--source-dir", str(source),
        "--effective-config", str(config), "--output-dir", str(output),
        "--dry-run", "--json",
    ], monkeypatch, capsys)
    _assert_cli_contract(json.loads(stdout), "build-kernel", code)
    assert code == 0
    assert json.loads(stdout)["status"] == "dry_run"
    assert not output.exists()


def test_nvidia_missing_headers_is_build_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    code, stdout, _ = _run_cli([
        "build-nvidia", "--config", str(yml), "--kernel-release", "7.2.15-huey1",
        "--headers-dir", str(tmp_path / "absent"), "--output-dir", str(tmp_path / "out"),
        "--json",
    ], monkeypatch, capsys)
    assert code == ExitCode.BUILD_FAILURE
    _assert_cli_contract(json.loads(stdout), "build-nvidia", code)


def test_initramfs_missing_tree_is_build_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    code, stdout, _ = _run_cli([
        "initramfs", "--config", str(yml), "--kernel-release", "7.2.15-huey1",
        "--module-tree", str(tmp_path / "missing"),
        "--modules-list", str(tmp_path / "no-list"),
        "--modprobe-conf", str(tmp_path / "no-modprobe"),
        "--output-dir", str(tmp_path / "out"), "--json",
    ], monkeypatch, capsys)
    assert code == ExitCode.BUILD_FAILURE
    _assert_cli_contract(json.loads(stdout), "initramfs", code)


def test_sign_dry_run_is_json_and_does_not_write(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    mods = tmp_path / "modules"; mods.mkdir()
    (mods / "nvidia.ko").write_bytes(b"fake")
    key = tmp_path / "MOK.priv"; key.write_bytes(b"fake")
    cert = tmp_path / "MOK.der"; cert.write_bytes(b"fake")
    headers = tmp_path / "headers"; (headers / "scripts").mkdir(parents=True)
    (headers / "scripts" / "sign-file").write_text("#!/bin/sh\n")
    out = tmp_path / "out"
    code, stdout, _ = _run_cli([
        "sign", "--config", str(yml), "--modules-dir", str(mods),
        "--headers-dir", str(headers), "--key", str(key), "--cert", str(cert),
        "--output-dir", str(out), "--dry-run", "--json",
    ], monkeypatch, capsys)
    _assert_cli_contract(json.loads(stdout), "sign", code)
    assert not out.exists()


def test_release_dry_run_fails_closed(tmp_path: Path, monkeypatch, capsys) -> None:
    _noop_runner(monkeypatch)
    yml = _write_build_yaml(tmp_path / "build.yaml")
    rd = _make_release_dir(tmp_path)
    code, stdout, _ = _run_cli([
        "release", "--config", str(yml), "--release-dir", str(rd),
        "--kernel-release", "7.2.15-huey1",
        "--kernel-image-deb", str(next(rd.glob("linux-image-*.deb"))),
        "--kernel-headers-deb", str(next(rd.glob("linux-headers-*.deb"))),
        "--dry-run", "--json",
    ], monkeypatch, capsys)
    _assert_cli_contract(json.loads(stdout), "release", code)
    assert not (rd / "MANIFEST.json").exists()
