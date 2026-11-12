"""Safe, host-isolated tests for the legacy installer command line."""

import importlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def installer_module():
    return importlib.import_module("huey.memory.PY.installer")


def paths_for(module, path=None, *, command=None):
    installer_path = path or (module.PROJECT_ROOT / "scripts/automation/sh/install.sh")
    return SimpleNamespace(
        host=SimpleNamespace(system="Linux"),
        install=installer_path,
        command_for=lambda operation: command or ["sh", str(installer_path)],
    )


def test_argument_parsing_and_selection_files(installer_module, monkeypatch, tmp_path):
    module = installer_module
    args = module.parse_args(["--yes", "--hardware", "iMac", "--software", "git"])
    assert args.yes and args.hardware == "iMac" and args.software == ["git"]
    monkeypatch.setattr(module, "SCRIPT_DIR", str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda _prompt: "2")
    assert module.select_hardware() == module.HARDWARE_OPTIONS[1]
    assert (
        tmp_path / "config/hardware.txt"
    ).read_text().strip() == module.HARDWARE_OPTIONS[1]
    answers = iter(["2", "1 3 bad 999"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert module.select_software() == "git python3"
    assert (tmp_path / "config/software.txt").read_text().strip() == "git python3"


def test_selection_falls_back_for_invalid_and_empty_choices(
    installer_module, monkeypatch, tmp_path
):
    module = installer_module
    monkeypatch.setattr(module, "SCRIPT_DIR", str(tmp_path))
    answers = iter(["2", "bad", "2", "bad 999"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    assert module.select_hardware() == "general"
    assert module.select_software() == "auto"


def test_admin_error_is_reported_and_reraised(installer_module, monkeypatch, capsys):
    module = installer_module
    monkeypatch.setattr(
        module, "require_admin_privileges", Mock(side_effect=PermissionError("no"))
    )
    with pytest.raises(PermissionError):
        module.ensure_admin_privileges()
    assert "Administrator privileges required" in capsys.readouterr().out


def test_display_license_falls_back_to_cli(installer_module, monkeypatch):
    module = installer_module
    cli = Mock()
    monkeypatch.setattr(
        module, "show_license_gui", Mock(side_effect=RuntimeError("no display"))
    )
    monkeypatch.setattr(module, "show_license_cli", cli)
    module.display_license()
    cli.assert_called_once_with()


def test_submodule_failure_is_reported_and_reraised(
    installer_module, monkeypatch, capsys
):
    module = installer_module
    failure = module.subprocess.CalledProcessError(1, ["git"])
    monkeypatch.setattr(module.subprocess, "run", Mock(side_effect=failure))
    with pytest.raises(module.subprocess.CalledProcessError):
        module.update_submodules()
    assert "Failed to update submodules: 1" in capsys.readouterr().out


def test_run_installer_handles_authorization_and_unsupported_platform(
    installer_module, monkeypatch
):
    module = installer_module
    authorize = Mock(return_value=False)
    monkeypatch.setattr(module, "authorize_privileged_operation", authorize)
    assert module.run_installer(dry_run=True) == 0
    authorize.assert_called_once()
    monkeypatch.setattr(
        module,
        "authorize_privileged_operation",
        Mock(side_effect=PermissionError("denied")),
    )
    assert module.run_installer() == 2
    monkeypatch.setattr(
        module, "authorize_privileged_operation", Mock(return_value=True)
    )
    monkeypatch.setattr(
        module,
        "resolve_platform_script_paths",
        Mock(
            return_value=SimpleNamespace(
                host=SimpleNamespace(system="Plan9"), install=None
            )
        ),
    )
    assert module.run_installer(confirmed=True) == 1


@pytest.mark.parametrize(
    "bad_path, expected", [("missing", 1), ("escape", 2), ("symlink", 1)]
)
def test_run_installer_rejects_unsafe_paths(
    installer_module, monkeypatch, tmp_path, bad_path, expected
):
    module = installer_module
    monkeypatch.setattr(
        module, "authorize_privileged_operation", Mock(return_value=True)
    )
    root = module.PROJECT_ROOT
    if bad_path == "missing":
        script = tmp_path / "missing.sh"
        path_result = paths_for(module, script)
    elif bad_path == "escape":
        script = tmp_path / "outside.sh"
        script.write_text("placeholder")
        path_result = paths_for(module, script)
    else:
        script = tmp_path / "linked.sh"
        script.symlink_to(root / "scripts/automation/sh/install.sh")
        path_result = paths_for(module, script)
    monkeypatch.setattr(
        module, "resolve_platform_script_paths", Mock(return_value=path_result)
    )
    assert module.run_installer(confirmed=True) == expected


@pytest.mark.parametrize(
    "outcome, expected",
    [(None, 0), ("timeout", 124), ("failed", 7)],
)
def test_run_installer_executes_and_reports_results(
    installer_module, monkeypatch, outcome, expected
):
    module = installer_module
    script = module.PROJECT_ROOT / "scripts/automation/sh/install.sh"
    monkeypatch.setattr(
        module, "authorize_privileged_operation", Mock(return_value=True)
    )
    monkeypatch.setattr(
        module,
        "resolve_platform_script_paths",
        Mock(return_value=paths_for(module, script)),
    )
    monkeypatch.setattr(module, "ensure_admin_privileges", Mock())
    monkeypatch.setattr(module, "update_submodules", Mock())
    monkeypatch.setattr(module, "display_license", Mock())
    if outcome == "timeout":
        run = Mock(side_effect=module.subprocess.TimeoutExpired("install", 1))
    elif outcome == "failed":
        run = Mock(side_effect=module.subprocess.CalledProcessError(7, "install"))
    else:
        run = Mock()
    monkeypatch.setattr(module.subprocess, "run", run)
    assert (
        module.run_installer(confirmed=True, hardware="manual", software=["git"])
        == expected
    )
    run.assert_called_once()
