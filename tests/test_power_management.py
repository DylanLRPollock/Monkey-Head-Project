"""Safety and cross-platform command tests for power management."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from huey.power import management
from huey.power.management import BatteryMonitor


def test_shutdown_dry_run_and_unauthorized_call_do_not_touch_host(monkeypatch):
    monitor = BatteryMonitor()
    host_lookup = Mock(side_effect=AssertionError("host discovery must not run"))
    process = Mock(side_effect=AssertionError("power command must not run"))
    monkeypatch.setattr(management, "detect_host_platform", host_lookup)
    monkeypatch.setattr(management.subprocess, "Popen", process)

    with pytest.raises(PermissionError):
        monitor.initiate_shutdown()

    event = monitor.initiate_shutdown(dry_run=True)

    assert event.action == "shutdown"
    assert event.metadata["dry_run"] is True
    host_lookup.assert_not_called()
    process.assert_not_called()


def test_confirmed_shutdown_uses_argv_without_a_shell(monkeypatch):
    monitor = BatteryMonitor()
    host = SimpleNamespace(display_name="Linux", family="linux")
    popen = Mock()
    monkeypatch.setattr(management, "detect_host_platform", lambda: host)
    monkeypatch.setattr(
        monitor, "_resolve_command", lambda _action: ["systemctl", "poweroff"]
    )
    monkeypatch.setattr(management.subprocess, "Popen", popen)

    event = monitor.initiate_shutdown(confirmed=True, actor_role="admin")

    assert event.metadata["command"] == ["systemctl", "poweroff"]
    popen.assert_called_once_with(["systemctl", "poweroff"], shell=False)


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        ("shutdown", ["shutdown", "/s", "/t", "0"]),
        ("reboot", ["shutdown", "/r", "/t", "0"]),
        ("sleep", ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"]),
        ("hibernate", ["shutdown", "/h"]),
        ("unknown", None),
    ],
)
def test_windows_power_commands(action, expected):
    assert BatteryMonitor()._windows_command(action) == expected


def test_linux_power_commands_prefer_systemctl_and_fallback(monkeypatch):
    monitor = BatteryMonitor()
    monkeypatch.setattr(management.shutil, "which", lambda command: "/bin/systemctl")
    assert monitor._linux_command("shutdown") == ["systemctl", "poweroff"]
    assert monitor._linux_command("hibernate") == ["systemctl", "hibernate"]

    monkeypatch.setattr(management.shutil, "which", lambda _command: None)
    assert monitor._linux_command("shutdown") == ["shutdown", "-h", "now"]
    assert monitor._linux_command("sleep") is None


def test_darwin_power_commands_and_missing_pmset(monkeypatch):
    monitor = BatteryMonitor()
    assert monitor._darwin_command("shutdown") == [
        "osascript",
        "-e",
        'tell app "System Events" to shut down',
    ]
    monkeypatch.setattr(management.shutil, "which", lambda _command: None)
    assert monitor._darwin_command("sleep") is None
    monkeypatch.setattr(management.shutil, "which", lambda _command: "/usr/bin/pmset")
    assert monitor._darwin_command("hibernate") == ["pmset", "sleepnow"]


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        ("Battery 75% 01:02:03 Charging", (75.0, 3723.0, True)),
        ("Battery 14.5% 00:20:00 Discharging", (14.5, 1200.0, False)),
        ("Battery state unavailable", (None, None, None)),
    ],
)
def test_parse_acpi_line(line, expected):
    assert management._parse_acpi_line(line) == expected
