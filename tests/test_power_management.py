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


def test_status_falls_back_to_empty_and_does_not_request_shutdown(monkeypatch):
    monitor = BatteryMonitor()
    monkeypatch.setattr(monitor, "_status_from_psutil", lambda: None)
    monkeypatch.setattr(monitor, "_status_from_sysfs", lambda: None)
    monkeypatch.setattr(monitor, "_status_from_acpi", lambda: None)

    status = monitor.get_status()
    assert status["percent"] is None
    assert status["secs_left"] is None
    assert status["power_plugged"] is None
    assert status["source"] == "unknown"
    assert status["estimated_runtime_minutes"] is None
    assert status["threshold"] == 5.0
    assert isinstance(status["timestamp"], float)
    assert monitor.should_shutdown() is False


def test_psutil_status_normalizes_unknown_runtime_and_handles_errors(monkeypatch):
    fake_psutil = SimpleNamespace(
        POWER_TIME_UNKNOWN=-1,
        POWER_TIME_UNLIMITED=-2,
        sensors_battery=lambda: SimpleNamespace(
            percent=37.5, secsleft=-1, power_plugged=False
        ),
    )
    monkeypatch.setattr(management, "psutil", fake_psutil)

    status = BatteryMonitor()._status_from_psutil()

    assert status == {
        "percent": 37.5,
        "secs_left": None,
        "power_plugged": False,
        "source": "psutil",
    }
    fake_psutil.sensors_battery = Mock(side_effect=OSError("sensor unavailable"))
    assert BatteryMonitor()._status_from_psutil() is None


def test_acpi_status_parses_output_and_handles_command_failure(monkeypatch):
    monkeypatch.setattr(management.shutil, "which", lambda _name: "/usr/bin/acpi")

    def fake_check_output(*_args, **_kwargs):
        return "\n".join(
            [
                "Battery 1: Discharging, 45%, 01:02:03 remaining",
                "AC Adapter 0: on-line",
            ]
        )

    monkeypatch.setattr(management.subprocess, "check_output", fake_check_output)

    status = BatteryMonitor()._status_from_acpi()

    assert status == {
        "percent": 45.0,
        "secs_left": 3723.0,
        "power_plugged": False,
        "source": "acpi",
    }
    monkeypatch.setattr(
        management.subprocess,
        "check_output",
        Mock(side_effect=management.subprocess.CalledProcessError(1, "acpi")),
    )
    assert BatteryMonitor()._status_from_acpi() is None


def test_observe_emits_low_recovery_and_connection_events_once():
    monitor = BatteryMonitor(shutdown_threshold=10)
    events = {name: [] for name in ("battery_low", "battery_recovered", "status")}
    for name in events:
        monitor.register_hook(
            name, lambda status, event=name: events[event].append(status)
        )

    monitor.observe({"percent": 5, "power_plugged": False})
    monitor.observe({"percent": 4, "power_plugged": False})
    monitor.observe({"percent": 20, "power_plugged": True})

    assert len(events["battery_low"]) == 1
    assert len(events["battery_recovered"]) == 1
    assert len(events["status"]) == 3


def test_remove_hook_and_listener_failure_do_not_break_observation():
    monitor = BatteryMonitor()
    received = []

    def callback(status):
        received.append(status)

    def failing_callback(_status):
        raise ValueError("bad hook")

    monitor.register_hook("status", callback)
    monitor.remove_hook("status", callback)
    monitor.register_hook("status", failing_callback)

    observed = monitor.observe({"percent": 50})

    assert observed["percent"] == 50
    assert received == []


def test_sysfs_readers_and_adapter_status_handle_missing_and_invalid_values(tmp_path):
    monitor = BatteryMonitor()
    numeric = tmp_path / "capacity"
    numeric.write_text(" 42.5 ", encoding="utf-8")
    empty = tmp_path / "empty"
    empty.write_text("  ", encoding="utf-8")
    invalid = tmp_path / "invalid"
    invalid.write_text("unknown", encoding="utf-8")

    assert monitor._read_sysfs_text(numeric) == "42.5"
    assert monitor._read_sysfs_float(numeric) == 42.5
    assert monitor._read_sysfs_text(empty) is None
    assert monitor._read_sysfs_float(invalid) is None
    assert monitor._read_sysfs_float(tmp_path / "missing") is None

    root = tmp_path / "power"
    (root / "battery0").mkdir(parents=True)
    adapter = root / "AC"
    adapter.mkdir()
    online = adapter / "online"
    online.write_text("1", encoding="utf-8")
    assert monitor._ac_adapter_online(root) is True
    online.write_text("0", encoding="utf-8")
    assert monitor._ac_adapter_online(root) is False
    online.write_text("unknown", encoding="utf-8")
    assert monitor._ac_adapter_online(root) is None


def test_psutil_status_without_battery_returns_none(monkeypatch):
    fake_psutil = SimpleNamespace(
        POWER_TIME_UNKNOWN=-1,
        POWER_TIME_UNLIMITED=-2,
        sensors_battery=lambda: None,
    )
    monkeypatch.setattr(management, "psutil", fake_psutil)

    assert BatteryMonitor()._status_from_psutil() is None


def test_power_action_without_supported_command_records_error(monkeypatch):
    monitor = BatteryMonitor()
    popen = Mock()

    def unknown_host():
        return SimpleNamespace(display_name="Unknown", family="unknown")

    monkeypatch.setattr(management, "detect_host_platform", unknown_host)
    monkeypatch.setattr(monitor, "_resolve_command", lambda _action: None)
    monkeypatch.setattr(management.subprocess, "Popen", popen)

    event = monitor.initiate_reboot(confirmed=True, actor_role="admin")

    assert event.metadata["error"] == "no supported command found"
    popen.assert_not_called()
