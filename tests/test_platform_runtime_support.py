"""Tests for platform-specific runtime command selection."""

from __future__ import annotations

from types import SimpleNamespace

from huey.network.manager import NetworkManager
from huey.os.core.platform_support import HostPlatform
from huey.power.management import BatteryMonitor


def _host(*, family: str, system: str) -> HostPlatform:
    display_name = {"windows": "Windows", "macos": "macOS", "linux": "Linux"}.get(
        family, system
    )
    return HostPlatform(
        family=family,  # type: ignore[arg-type]
        system=system,
        release="",
        version="",
        machine="x86_64",
        sys_platform=family,
        display_name=display_name,
        is_windows=family == "windows",
        is_macos=family == "macos",
        is_linux=family == "linux",
        is_unknown=family == "unknown",
        is_wsl=False,
    )


def test_network_manager_linux_uses_nmcli(monkeypatch) -> None:
    commands: list[list[str]] = []
    manager = NetworkManager()

    monkeypatch.setattr(
        "huey.network.manager.detect_host_platform",
        lambda: _host(family="linux", system="Linux"),
    )
    monkeypatch.setattr(
        "huey.network.manager.shutil.which",
        lambda tool: "/usr/bin/nmcli" if tool == "nmcli" else None,
    )
    monkeypatch.setattr(
        "huey.network.manager.subprocess.run",
        lambda command, **kwargs: commands.append(command)
        or SimpleNamespace(returncode=0, stdout=""),
    )

    manager._bring_up_interface("wlan0")

    assert commands == [["nmcli", "device", "connect", "wlan0"]]


def test_network_manager_macos_uses_networksetup(monkeypatch) -> None:
    commands: list[list[str]] = []
    manager = NetworkManager()

    monkeypatch.setattr(
        "huey.network.manager.detect_host_platform",
        lambda: _host(family="macos", system="Darwin"),
    )
    monkeypatch.setattr(
        "huey.network.manager.shutil.which",
        lambda tool: "/usr/sbin/networksetup" if tool == "networksetup" else None,
    )
    monkeypatch.setattr(
        "huey.network.manager.subprocess.run",
        lambda command, **kwargs: commands.append(command)
        or SimpleNamespace(returncode=0, stdout=""),
    )

    manager._bring_up_interface("en0")

    assert commands == [["networksetup", "-setairportpower", "en0", "on"]]


def test_network_manager_windows_uses_powershell(monkeypatch) -> None:
    commands: list[list[str]] = []
    manager = NetworkManager()

    monkeypatch.setattr(
        "huey.network.manager.detect_host_platform",
        lambda: _host(family="windows", system="Windows"),
    )
    monkeypatch.setattr(
        "huey.network.manager.shutil.which",
        lambda tool: (
            "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"
            if tool == "powershell"
            else None
        ),
    )
    monkeypatch.setattr(
        "huey.network.manager.subprocess.run",
        lambda command, **kwargs: commands.append(command)
        or SimpleNamespace(returncode=0, stdout=""),
    )

    manager._bring_up_interface("Wi-Fi")

    assert commands
    assert commands[0][0].endswith("powershell.exe")
    assert commands[0][1:3] == ["-NoProfile", "-Command"]
    assert "Enable-NetAdapter" in commands[0][3]


def test_network_manager_macos_interface_category_uses_hardware_port_map(
    monkeypatch,
) -> None:
    manager = NetworkManager()
    monkeypatch.setattr(
        "huey.network.manager.detect_host_platform",
        lambda: _host(family="macos", system="Darwin"),
    )
    monkeypatch.setattr(
        manager,
        "_load_macos_device_categories",
        lambda: {"en0": "wifi", "en7": "wired"},
    )

    assert manager._interface_category("en0") == "wifi"
    assert manager._interface_category("en7") == "wired"


def test_power_monitor_resolves_commands_for_each_platform(monkeypatch) -> None:
    monitor = BatteryMonitor()

    monkeypatch.setattr(
        "huey.power.management.detect_host_platform",
        lambda: _host(family="windows", system="Windows"),
    )
    assert monitor._resolve_command("hibernate") == ["shutdown", "/h"]

    monkeypatch.setattr(
        "huey.power.management.detect_host_platform",
        lambda: _host(family="macos", system="Darwin"),
    )
    monkeypatch.setattr(
        "huey.power.management.shutil.which",
        lambda tool: "/usr/bin/pmset" if tool == "pmset" else None,
    )
    assert monitor._resolve_command("sleep") == ["pmset", "sleepnow"]

    monkeypatch.setattr(
        "huey.power.management.detect_host_platform",
        lambda: _host(family="linux", system="Linux"),
    )
    monkeypatch.setattr(
        "huey.power.management.shutil.which",
        lambda tool: "/usr/bin/systemctl" if tool == "systemctl" else None,
    )
    assert monitor._resolve_command("reboot") == ["systemctl", "reboot"]
