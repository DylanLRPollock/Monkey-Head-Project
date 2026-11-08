"""Deny-by-default host-operation tests with no real machine side effects."""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from huey.os.core.privileged_operations import authorize_privileged_operation
from huey.power import management


@pytest.mark.parametrize(
    "operation",
    [
        "host.shutdown",
        "host.reboot",
        "host.sleep",
        "host.hibernate",
        "project.uninstall",
    ],
)
def test_privileged_operation_requires_confirmation_and_authority(operation):
    with pytest.raises(PermissionError, match="confirmation"):
        authorize_privileged_operation(operation)
    with pytest.raises(PermissionError, match="role"):
        authorize_privileged_operation(operation, confirmed=True, actor_role="operator")
    assert authorize_privileged_operation(operation, dry_run=True) is False


@pytest.mark.parametrize(
    ("method", "action"),
    [
        ("initiate_shutdown", "shutdown"),
        ("initiate_reboot", "reboot"),
        ("initiate_sleep", "sleep"),
        ("initiate_hibernate", "hibernate"),
    ],
)
def test_power_denied_and_dry_run_never_touch_host(monkeypatch, method, action):
    monitor = management.BatteryMonitor()
    launch = Mock(side_effect=AssertionError("unexpected subprocess"))
    monkeypatch.setattr(management.subprocess, "Popen", launch)
    monkeypatch.setattr(
        management,
        "detect_host_platform",
        Mock(side_effect=AssertionError("host touched")),
    )
    with pytest.raises(PermissionError, match="confirmation"):
        getattr(monitor, method)()
    event = getattr(monitor, method)(dry_run=True)
    assert event.action == action
    assert event.metadata["dry_run"] is True
    launch.assert_not_called()


def test_power_confirmed_admin_executes_argv_not_shell(monkeypatch):
    monitor = management.BatteryMonitor()
    launch = Mock()
    monkeypatch.setattr(management.subprocess, "Popen", launch)
    monkeypatch.setattr(
        management,
        "detect_host_platform",
        lambda: SimpleNamespace(display_name="Linux", family="linux"),
    )
    monkeypatch.setattr(
        monitor, "_resolve_command", lambda action: ["systemctl", action]
    )
    with pytest.raises(PermissionError, match="role"):
        monitor.initiate_reboot(confirmed=True, actor_role="operator")
    launch.assert_not_called()
    event = monitor.initiate_reboot(confirmed=True, actor_role="admin")
    assert event.metadata["command"] == ["systemctl", "reboot"]
    launch.assert_called_once_with(["systemctl", "reboot"], shell=False)


@pytest.mark.parametrize(
    ("platform", "action", "expected"),
    [
        ("windows", "shutdown", ["shutdown", "/s", "/t", "0"]),
        ("windows", "hibernate", ["shutdown", "/h"]),
        ("linux", "shutdown", ["systemctl", "poweroff"]),
        ("linux", "sleep", ["systemctl", "suspend"]),
        (
            "macos",
            "shutdown",
            ["osascript", "-e", 'tell app "System Events" to shut down'],
        ),
    ],
)
def test_platform_command_construction(monkeypatch, platform, action, expected):
    monkeypatch.setattr(management.shutil, "which", lambda name: "/bin/" + name)
    monitor = management.BatteryMonitor()
    fn = {
        "windows": monitor._windows_command,
        "linux": monitor._linux_command,
        "macos": monitor._darwin_command,
    }[platform]
    assert fn(action) == expected


def test_uninstaller_denial_and_dry_run_never_probe_files(monkeypatch):
    module = importlib.import_module("huey.memory.PY.uninstaller")
    run = Mock(side_effect=AssertionError("unexpected subprocess"))
    monkeypatch.setattr(module.subprocess, "run", run)
    monkeypatch.setattr(
        module,
        "resolve_platform_script_paths",
        Mock(side_effect=AssertionError("unexpected filesystem probe")),
    )
    assert module.run_uninstaller() == 2
    assert module.run_uninstaller(confirmed=True) == 2
    assert module.run_uninstaller(dry_run=True) == 0
    run.assert_not_called()


def test_uninstaller_confirmed_executes_only_project_script(monkeypatch, tmp_path):
    module = importlib.import_module("huey.memory.PY.uninstaller")
    script = tmp_path / "uninstall.sh"
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    paths = SimpleNamespace(
        uninstall=script,
        command_for=lambda action: ["bash", str(script)],
        host=SimpleNamespace(system="Linux"),
    )
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(module, "resolve_platform_script_paths", lambda root: paths)
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.run_uninstaller(confirmed=True, actor_role="admin") == 0
    run.assert_called_once_with(
        ["bash", str(script)], check=True, cwd=tmp_path, shell=False, timeout=1200
    )


def test_uninstaller_rejects_symlink(monkeypatch, tmp_path):
    module = importlib.import_module("huey.memory.PY.uninstaller")
    target = tmp_path / "target.sh"
    target.write_text("exit 0\n", encoding="utf-8")
    script = tmp_path / "uninstall.sh"
    try:
        script.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlink support unavailable")
    paths = SimpleNamespace(uninstall=script, host=SimpleNamespace(system="Linux"))
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(module, "resolve_platform_script_paths", lambda root: paths)
    run = Mock(side_effect=AssertionError("unexpected subprocess"))
    monkeypatch.setattr(module.subprocess, "run", run)
    assert module.run_uninstaller(confirmed=True, actor_role="admin") == 1
    run.assert_not_called()
