"""Safe tests for legacy installer prompts, policy gates, and dispatch."""

from __future__ import annotations

import importlib
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.memory.PY import installer


@pytest.fixture(autouse=True)
def load_installer_source_for_coverage():
    """Load the legacy source under a unique name after tracing has started."""
    global installer
    source = Path(installer.__file__).resolve()
    spec = importlib.util.spec_from_file_location(
        "huey.memory.PY._installer_coverage_probe", source
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    installer = module


def test_manual_hardware_selection_and_invalid_selection_are_saved(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(installer, "SCRIPT_DIR", str(tmp_path))
    answers = iter(["2", "3"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    selected = installer.select_hardware()

    assert selected == "iMac 5K 2017"
    assert (tmp_path / "config" / "hardware.txt").read_text() == f"{selected}\n"
    assert "Available hardware options" in capsys.readouterr().out

    monkeypatch.setattr(
        "builtins.input", lambda _prompt: "2" if "choice [1/2]" in _prompt else "bad"
    )
    assert installer.select_hardware() == "general"
    assert "Invalid choice" in capsys.readouterr().out


def test_automatic_hardware_and_software_selection_persist_defaults(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(installer, "SCRIPT_DIR", str(tmp_path))
    answers = iter(["1", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert installer.select_hardware() == "general"
    assert installer.select_software() == "auto"
    assert (tmp_path / "config" / "hardware.txt").read_text() == "general\n"
    assert (tmp_path / "config" / "software.txt").read_text() == "auto\n"


def test_manual_software_selection_keeps_valid_items_and_reports_invalid(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(installer, "SCRIPT_DIR", str(tmp_path))
    answers = iter(["2", "1 invalid 8 3"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert installer.select_software() == "git python3"
    assert (tmp_path / "config" / "software.txt").read_text() == "git python3\n"
    assert "Invalid selection: invalid" in capsys.readouterr().out

    answers = iter(["2", "8"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert installer.select_software() == "auto"


def test_parse_args_supports_confirmed_dry_run_and_install_overrides():
    args = installer.parse_args(
        ["--yes", "--dry-run", "--hardware", "iMac", "--software", "git", "ffmpeg"]
    )
    assert args.yes is True
    assert args.dry_run is True
    assert args.hardware == "iMac"
    assert args.software == ["git", "ffmpeg"]


def test_admin_and_license_helpers_report_and_fallback(monkeypatch, capsys):
    monkeypatch.setattr(installer, "require_admin_privileges", lambda **_kwargs: None)
    installer.ensure_admin_privileges()

    def denied(**_kwargs):
        raise PermissionError("admin required")

    monkeypatch.setattr(installer, "require_admin_privileges", denied)
    with pytest.raises(PermissionError, match="admin required"):
        installer.ensure_admin_privileges()
    assert "Administrator privileges required" in capsys.readouterr().out

    calls = []
    monkeypatch.setattr(installer, "show_license_gui", lambda: calls.append("gui"))
    monkeypatch.setattr(installer, "show_license_cli", lambda: calls.append("cli"))
    installer.display_license()
    monkeypatch.setattr(
        installer, "show_license_gui", lambda: (_ for _ in ()).throw(RuntimeError())
    )
    installer.display_license()
    assert calls == ["gui", "cli"]


def test_update_submodules_runs_git_and_sync_without_shell(monkeypatch):
    calls = []
    monkeypatch.setattr(
        installer.subprocess,
        "run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    installer.update_submodules()

    assert len(calls) == 2
    assert calls[0][0][0] == ["git", "submodule", "update", "--init", "--recursive"]
    assert calls[0][1]["check"] is True
    assert calls[0][1]["shell"] is False
    assert calls[1][0][0][0] == sys.executable
    assert calls[1][1]["cwd"] == installer.PROJECT_ROOT


def test_update_submodules_reports_command_failure(monkeypatch, capsys):
    def fail(*_args, **_kwargs):
        raise subprocess.CalledProcessError(5, "git")

    monkeypatch.setattr(installer.subprocess, "run", fail)
    with pytest.raises(subprocess.CalledProcessError):
        installer.update_submodules()
    assert "Failed to update submodules: 5" in capsys.readouterr().out


def _successful_install_setup(tmp_path, monkeypatch, *, command=None):
    root = tmp_path / "project"
    root.mkdir()
    script = root / "install.sh"
    script.write_text("#!/bin/sh\nexit 0\n")
    host = SimpleNamespace(system="Linux")
    paths = SimpleNamespace(
        install=script,
        host=host,
        command_for=lambda _action: command,
    )
    monkeypatch.setattr(installer, "PROJECT_ROOT", root)
    monkeypatch.setattr(installer, "resolve_platform_script_paths", lambda _root: paths)
    monkeypatch.setattr(
        installer, "authorize_privileged_operation", lambda *_a, **_k: True
    )
    monkeypatch.setattr(installer, "ensure_admin_privileges", lambda: None)
    monkeypatch.setattr(installer, "update_submodules", lambda: None)
    monkeypatch.setattr(installer, "display_license", lambda: None)
    calls = []
    monkeypatch.setattr(
        installer.subprocess, "run", lambda *a, **k: calls.append((a, k))
    )
    return root, script, paths, calls


def test_run_installer_noninteractive_sets_environment_and_uses_platform_command(
    tmp_path, monkeypatch
):
    _root, _script, _paths, calls = _successful_install_setup(
        tmp_path, monkeypatch, command=["bash", "safe-install.sh"]
    )
    monkeypatch.setattr(installer.sys, "stdin", SimpleNamespace(isatty=lambda: False))

    result = installer.run_installer(
        hardware="iMac",
        software=["git", "ffmpeg"],
        confirmed=True,
        actor_role="operator",
    )

    assert result == 0
    args, kwargs = calls[0]
    assert args[0] == ["bash", "safe-install.sh"]
    assert kwargs["env"]["MHP_HARDWARE"] == "iMac"
    assert kwargs["env"]["MHP_SOFTWARE"] == "git ffmpeg"
    assert kwargs["check"] is True
    assert kwargs["shell"] is False


def test_run_installer_defaults_to_general_and_auto_noninteractively(
    tmp_path, monkeypatch
):
    _successful_install_setup(tmp_path, monkeypatch)
    monkeypatch.setattr(installer.sys, "stdin", SimpleNamespace(isatty=lambda: False))

    assert installer.run_installer(confirmed=True) == 0


def test_run_installer_dry_run_and_authorization_denial_do_not_touch_host(
    monkeypatch, capsys
):
    calls = []
    monkeypatch.setattr(
        installer, "authorize_privileged_operation", lambda *_a, **_k: False
    )
    monkeypatch.setattr(
        installer, "ensure_admin_privileges", lambda: calls.append("admin")
    )

    assert installer.run_installer(dry_run=True) == 0
    assert calls == []
    assert "no host changes" in capsys.readouterr().out

    def reject(*_args, **_kwargs):
        raise PermissionError("approval required")

    monkeypatch.setattr(installer, "authorize_privileged_operation", reject)
    assert installer.run_installer() == 2
    assert calls == []
    assert "approval required" in capsys.readouterr().out


@pytest.mark.parametrize(
    "path_kind,expected", [("missing", 1), ("symlink", 1), ("outside", 2)]
)
def test_run_installer_rejects_untrusted_script_paths(
    tmp_path, monkeypatch, path_kind, expected
):
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside.sh"
    outside.write_text("safe")
    if path_kind == "missing":
        script = root / "missing.sh"
    elif path_kind == "symlink":
        script = root / "link.sh"
        script.symlink_to(outside)
    else:
        script = outside
    paths = SimpleNamespace(
        install=script,
        host=SimpleNamespace(system="Linux"),
        command_for=lambda _a: None,
    )
    monkeypatch.setattr(installer, "PROJECT_ROOT", root)
    monkeypatch.setattr(installer, "resolve_platform_script_paths", lambda _root: paths)
    monkeypatch.setattr(
        installer, "authorize_privileged_operation", lambda *_a, **_k: True
    )
    monkeypatch.setattr(installer.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    assert installer.run_installer(confirmed=True) == expected


def test_run_installer_unsupported_platform_returns_one(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(installer, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        installer,
        "resolve_platform_script_paths",
        lambda _root: SimpleNamespace(
            install=None, host=SimpleNamespace(system="Plan9")
        ),
    )
    monkeypatch.setattr(
        installer, "authorize_privileged_operation", lambda *_a, **_k: True
    )
    monkeypatch.setattr(installer.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    assert installer.run_installer(confirmed=True) == 1
    assert "Unsupported operating system: Plan9" in capsys.readouterr().out


@pytest.mark.parametrize(
    "exception,expected,text",
    [
        (subprocess.TimeoutExpired("installer", 1200), 124, "Installer timed out"),
        (subprocess.CalledProcessError(7, "installer"), 7, "return code 7"),
    ],
)
def test_run_installer_reports_process_failures(
    tmp_path, monkeypatch, capsys, exception, expected, text
):
    _successful_install_setup(tmp_path, monkeypatch)
    monkeypatch.setattr(installer.sys, "stdin", SimpleNamespace(isatty=lambda: False))
    monkeypatch.setattr(installer, "ensure_admin_privileges", lambda: None)
    monkeypatch.setattr(installer, "update_submodules", lambda: None)
    monkeypatch.setattr(installer, "display_license", lambda: None)
    monkeypatch.setattr(
        installer.subprocess, "run", lambda *_a, **_k: (_ for _ in ()).throw(exception)
    )

    assert installer.run_installer(confirmed=True) == expected
    assert text in capsys.readouterr().out


def test_run_installer_interactive_selection_and_auto_package_list(
    tmp_path, monkeypatch
):
    _successful_install_setup(tmp_path, monkeypatch)
    monkeypatch.setattr(installer.sys, "stdin", SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr(installer, "select_hardware", lambda: "Framework Laptop 13")
    monkeypatch.setattr(installer, "select_software", lambda: "git ffmpeg")

    assert installer.run_installer(confirmed=True) == 0


def test_run_installer_maps_auto_software_selection_to_keyword(tmp_path, monkeypatch):
    _root, _script, _paths, calls = _successful_install_setup(tmp_path, monkeypatch)
    monkeypatch.setattr(installer.sys, "stdin", SimpleNamespace(isatty=lambda: False))

    assert installer.run_installer(software=["auto"], confirmed=True) == 0
    assert calls[0][1]["env"]["MHP_SOFTWARE"] == "auto"


def test_installer_cli_entry_point_supports_safe_dry_run():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(installer.__file__).resolve().parents[3])
    result = subprocess.run(
        [sys.executable, installer.__file__, "--dry-run"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "no host changes" in result.stdout


def test_installer_module_reloads_from_the_covered_source_file():
    source_path = Path(installer.__file__).resolve()

    installer.__loader__.exec_module(installer)

    assert Path(installer.__file__).resolve() == source_path
    assert installer.parse_args(["--dry-run"]).dry_run is True
