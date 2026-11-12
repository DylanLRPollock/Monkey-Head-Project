"""Safety-focused coverage for the legacy installer entry point."""

from __future__ import annotations

import importlib
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

installer = importlib.import_module("huey.memory.PY.installer")


def _script_paths(script: Path, system: str = "Linux") -> SimpleNamespace:
    return SimpleNamespace(
        install=script,
        host=SimpleNamespace(system=system),
        command_for=lambda _name: [str(script)],
    )


def _authorize(monkeypatch, authorized=True):
    monkeypatch.setattr(
        installer, "authorize_privileged_operation", lambda *a, **k: authorized
    )


def _mock_install_prerequisites(monkeypatch):
    monkeypatch.setattr(installer, "ensure_admin_privileges", lambda: None)
    monkeypatch.setattr(installer, "update_submodules", lambda: None)
    monkeypatch.setattr(installer, "display_license", lambda: None)


def test_run_installer_authorization_denial_and_dry_run(monkeypatch, capsys):
    _authorize(monkeypatch, False)
    assert installer.run_installer() == 0
    assert "dry-run" in capsys.readouterr().out
    monkeypatch.setattr(
        installer,
        "authorize_privileged_operation",
        lambda *a, **k: (_ for _ in ()).throw(PermissionError("approval needed")),
    )
    assert installer.run_installer(confirmed=False) == 2
    assert "approval needed" in capsys.readouterr().out


def test_run_installer_unsupported_and_missing_script(monkeypatch, tmp_path, capsys):
    _authorize(monkeypatch, True)
    monkeypatch.setattr(
        installer,
        "resolve_platform_script_paths",
        lambda _root: _script_paths(None, "Plan9"),
    )
    assert installer.run_installer(confirmed=True) == 1
    assert "Unsupported operating system" in capsys.readouterr().out

    missing = tmp_path / "missing.sh"
    monkeypatch.setattr(
        installer,
        "resolve_platform_script_paths",
        lambda _root: _script_paths(missing),
    )
    assert installer.run_installer(confirmed=True) == 1
    assert "Installer script not found" in capsys.readouterr().out


def test_run_installer_rejects_symlink_and_path_escape(monkeypatch, tmp_path, capsys):
    _authorize(monkeypatch, True)
    root = tmp_path / "project"
    root.mkdir()
    inside = root / "install.sh"
    inside.write_text("#!/bin/sh\n", encoding="utf-8")
    outside = tmp_path / "outside.sh"
    outside.write_text("#!/bin/sh\n", encoding="utf-8")
    link = root / "link.sh"
    link.symlink_to(outside)
    monkeypatch.setattr(installer, "PROJECT_ROOT", root)
    monkeypatch.setattr(
        installer,
        "resolve_platform_script_paths",
        lambda _root: _script_paths(link),
    )
    assert installer.run_installer(confirmed=True) == 1
    assert "not found" in capsys.readouterr().out

    monkeypatch.setattr(
        installer,
        "resolve_platform_script_paths",
        lambda _root: _script_paths(outside),
    )
    assert installer.run_installer(confirmed=True) == 2
    assert "inside the project" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (subprocess.TimeoutExpired("installer", 1200), 124),
        (subprocess.CalledProcessError(7, "installer"), 7),
    ],
)
def test_run_installer_reports_process_failures(
    monkeypatch, tmp_path, capsys, failure, expected
):
    script = tmp_path / "install.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(installer, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        installer,
        "resolve_platform_script_paths",
        lambda _root: _script_paths(script),
    )
    _authorize(monkeypatch, True)
    _mock_install_prerequisites(monkeypatch)
    monkeypatch.setattr(
        installer.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(failure)
    )
    assert installer.run_installer(confirmed=True) == expected
    assert capsys.readouterr().out


def test_run_installer_success_sets_child_environment(monkeypatch, tmp_path, capsys):
    script = tmp_path / "install.sh"
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    monkeypatch.setattr(installer, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        installer,
        "resolve_platform_script_paths",
        lambda _root: _script_paths(script),
    )
    _authorize(monkeypatch, True)
    _mock_install_prerequisites(monkeypatch)
    calls = []
    monkeypatch.setattr(
        installer.subprocess, "run", lambda *a, **k: calls.append((a, k))
    )
    assert (
        installer.run_installer(
            hardware="V100 host", software=["ollama", "comfyui"], confirmed=True
        )
        == 0
    )
    _, kwargs = calls[0]
    assert kwargs["env"]["MHP_HARDWARE"] == "V100 host"
    assert kwargs["env"]["MHP_SOFTWARE"] == "ollama comfyui"
    assert "Thank you" in capsys.readouterr().out


def test_interactive_selections_and_argument_parser(monkeypatch, tmp_path):
    monkeypatch.setattr(installer, "SCRIPT_DIR", str(tmp_path))
    answers = iter(("2", "1", "2", "1 3 bad 99"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert installer.select_hardware() == installer.HARDWARE_OPTIONS[0]
    assert installer.select_software() == "git python3"
    assert (
        tmp_path / "config" / "hardware.txt"
    ).read_text() == "SuperMicro X9 qri-f+\n"
    assert (tmp_path / "config" / "software.txt").read_text() == "git python3\n"
    args = installer.parse_args(["--yes", "--dry-run", "--hardware", "V100"])
    assert args.yes and args.dry_run and args.hardware == "V100"


def test_invalid_and_automatic_interactive_selections(monkeypatch, tmp_path):
    monkeypatch.setattr(installer, "SCRIPT_DIR", str(tmp_path))
    answers = iter(("2", "bad", "1"))
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert installer.select_hardware() == "general"
    assert installer.select_software() == "auto"
    assert (tmp_path / "config" / "hardware.txt").read_text() == "general\n"
    assert (tmp_path / "config" / "software.txt").read_text() == "auto\n"
    monkeypatch.setattr("builtins.input", lambda _prompt: "1")
    assert installer.select_hardware() == "general"


def test_admin_denial_and_submodule_failure_are_reported(monkeypatch, capsys):
    monkeypatch.setattr(
        installer,
        "require_admin_privileges",
        lambda **_kwargs: (_ for _ in ()).throw(PermissionError("need root")),
    )
    with pytest.raises(PermissionError, match="need root"):
        installer.ensure_admin_privileges()
    assert "Administrator privileges required" in capsys.readouterr().out

    monkeypatch.setattr(
        installer.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(subprocess.CalledProcessError(9, "git")),
    )
    with pytest.raises(subprocess.CalledProcessError):
        installer.update_submodules()
    assert "Failed to update submodules: 9" in capsys.readouterr().out


def test_update_submodules_runs_both_commands(monkeypatch, tmp_path):
    monkeypatch.setattr(installer, "PROJECT_ROOT", tmp_path)
    commands = []
    monkeypatch.setattr(
        installer.subprocess, "run", lambda command, **kwargs: commands.append(command)
    )
    installer.update_submodules()
    assert commands[0][:4] == ["git", "submodule", "update", "--init"]
    assert commands[1][0] == installer.sys.executable


def test_license_falls_back_to_cli(monkeypatch):
    seen = []
    monkeypatch.setattr(
        installer,
        "show_license_gui",
        lambda: (_ for _ in ()).throw(RuntimeError("no GUI")),
    )
    monkeypatch.setattr(installer, "show_license_cli", lambda: seen.append("cli"))
    installer.display_license()
    assert seen == ["cli"]
