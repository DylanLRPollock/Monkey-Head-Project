"""Offline coverage for network discovery, failover, and platform commands."""

from __future__ import annotations

import socket
from pathlib import Path
from types import SimpleNamespace

import pytest

import huey.network.manager as network_module
from huey.network.manager import NetworkManager, NetworkStatus
from huey.os.core.platform_support import HostPlatform


def _host(family: str) -> HostPlatform:
    names = {"linux": "Linux", "macos": "Darwin", "windows": "Windows"}
    return HostPlatform(
        family=family,  # type: ignore[arg-type]
        system=names[family],
        release="",
        version="",
        machine="x86_64",
        sys_platform=family,
        display_name=names[family],
        is_windows=family == "windows",
        is_macos=family == "macos",
        is_linux=family == "linux",
        is_unknown=False,
        is_wsl=False,
    )


def _status(
    *,
    connected: bool,
    active: str | None = None,
    wired: bool = False,
    wifi: bool = False,
) -> NetworkStatus:
    return NetworkStatus(
        active_interface=active,
        interfaces={},
        wired_available=wired,
        wifi_available=wifi,
        connected=connected,
        last_checked=0.0,
    )


def test_interface_stats_uses_psutil_and_records_categories(monkeypatch) -> None:
    manager = NetworkManager()
    monkeypatch.setattr(
        network_module,
        "psutil",
        SimpleNamespace(
            net_if_stats=lambda: {
                "eth0": SimpleNamespace(isup=True, speed=1000, duplex=2, mtu=1500),
                "wlan0": SimpleNamespace(isup=False, speed=0, duplex=0, mtu=0),
                "lo": SimpleNamespace(isup=True, speed=0, duplex=0, mtu=65536),
            }
        ),
    )

    assert manager._interface_stats() == {
        "eth0": {"isup": True, "speed": 1000.0, "duplex": 2.0, "mtu": 1500.0},
        "wlan0": {"isup": False, "speed": None, "duplex": None, "mtu": None},
        "lo": {"isup": True, "speed": None, "duplex": None, "mtu": 65536.0},
    }
    assert manager._interface_categories == {
        "eth0": "wired",
        "wlan0": "wifi",
        "lo": "loopback",
    }


def test_interface_stats_reads_sysfs_when_psutil_has_no_interfaces(
    tmp_path, monkeypatch
) -> None:
    root = tmp_path / "net"
    ethernet = root / "enp2s0"
    wifi = root / "wlan0"
    loopback = root / "lo"
    for path in (ethernet, wifi, loopback):
        path.mkdir(parents=True)
    (ethernet / "operstate").write_text("up\n")
    (ethernet / "speed").write_text("2500\n")
    (ethernet / "mtu").write_text("1500\n")
    (wifi / "operstate").write_text("down\n")
    (wifi / "speed").write_text("not-a-number\n")
    (wifi / "mtu").write_text("\n")
    monkeypatch.setattr(
        network_module, "psutil", SimpleNamespace(net_if_stats=lambda: {})
    )
    real_path = Path
    monkeypatch.setattr(
        network_module,
        "Path",
        lambda value: root if str(value) == "/sys/class/net" else real_path(value),
    )

    manager = NetworkManager()
    assert manager._interface_stats() == {
        "enp2s0": {"isup": True, "speed": 2500.0, "mtu": 1500.0, "duplex": None},
        "wlan0": {"isup": False, "speed": None, "mtu": None, "duplex": None},
    }
    assert manager._interface_categories == {"enp2s0": "wired", "wlan0": "wifi"}


def test_sysfs_readers_handle_io_and_invalid_values(tmp_path, monkeypatch) -> None:
    manager = NetworkManager()
    missing = tmp_path / "missing"
    assert manager._read_sysfs_flag(missing) is False
    assert manager._read_sysfs_float(missing) is None
    invalid = tmp_path / "invalid"
    invalid.write_text("not-a-number")
    assert manager._read_sysfs_float(invalid) is None
    monkeypatch.setattr(Path, "read_text", lambda *_args, **_kwargs: "YES\n")
    assert manager._read_sysfs_flag(invalid) is True


@pytest.mark.parametrize(
    ("family", "name", "expected"),
    [
        ("linux", "eno1", "wired"),
        ("linux", "enx001122", "other"),
        ("linux", "wlan0", "wifi"),
        ("linux", "wlx001122", "wifi"),
        ("linux", "lo0", "loopback"),
        ("linux", "docker0", "other"),
        ("windows", "Ethernet 2", "wired"),
        ("windows", "Wi-Fi 2", "wifi"),
        ("windows", "VPN", "other"),
        ("macos", "en0", "wifi"),
        ("macos", "en1", "other"),
    ],
)
def test_interface_category_handles_host_names(monkeypatch, family, name, expected):
    manager = NetworkManager()
    monkeypatch.setattr(network_module, "detect_host_platform", lambda: _host(family))
    if family == "macos":
        manager._macos_device_categories = {"en0": "wifi"}
    assert manager._interface_category(name) == expected


def test_macos_hardware_port_parser_maps_devices_and_uses_first_mapping(
    monkeypatch,
) -> None:
    manager = NetworkManager()
    monkeypatch.setattr(
        network_module.shutil, "which", lambda name: "/usr/sbin/networksetup"
    )
    monkeypatch.setattr(
        network_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=(
                "Unrecognized line\n"
                "Hardware Port: Wi-Fi\nDevice: en0\n\n"
                "Hardware Port: Ethernet\nDevice: en7\n"
                "Hardware Port: USB\nDevice: en7\n"
                "Hardware Port: Bluetooth PAN\nDevice:\n"
            ),
        ),
    )
    assert manager._load_macos_device_categories() == {"en0": "wifi", "en7": "wired"}


@pytest.mark.parametrize("result", [1, OSError("not installed")])
def test_macos_hardware_port_parser_returns_empty_on_tool_failure(
    monkeypatch, result
) -> None:
    manager = NetworkManager()
    monkeypatch.setattr(network_module.shutil, "which", lambda _name: "/networksetup")
    if isinstance(result, Exception):

        def run(*_args, **_kwargs):
            raise result

    else:

        def run(*_args, **_kwargs):
            return SimpleNamespace(returncode=result, stdout="ignored")

    monkeypatch.setattr(network_module.subprocess, "run", run)
    assert manager._load_macos_device_categories() == {}


def test_macos_hardware_port_parser_returns_empty_without_networksetup(monkeypatch):
    manager = NetworkManager()
    monkeypatch.setattr(network_module.shutil, "which", lambda _name: None)
    assert manager._load_macos_device_categories() == {}


def test_preferred_interface_prioritizes_wired_then_wifi() -> None:
    manager = NetworkManager()
    manager._interface_categories = {"wlan0": "wifi", "eth1": "wired", "eth0": "wired"}
    interfaces = {
        "wlan0": {"isup": True},
        "eth1": {"isup": True},
        "eth0": {"isup": True},
    }
    assert manager._preferred_interface(interfaces) == "eth1"
    interfaces["eth1"]["isup"] = False
    interfaces["eth0"]["isup"] = False
    assert manager._preferred_interface(interfaces) == "wlan0"
    interfaces["wlan0"]["isup"] = False
    assert manager._preferred_interface(interfaces) is None


def test_attempt_connectivity_returns_local_ip_and_handles_socket_errors(monkeypatch):
    manager = NetworkManager(
        check_host="example.invalid", check_port=123, check_timeout=0.5
    )

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def getsockname(self):
            return ("192.0.2.10", 12345)

    monkeypatch.setattr(
        network_module.socket, "create_connection", lambda *a, **k: Connection()
    )
    assert manager._attempt_connectivity() == (True, "192.0.2.10")
    monkeypatch.setattr(
        network_module.socket,
        "create_connection",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("offline")),
    )
    assert manager._attempt_connectivity() == (False, None)


def test_detect_active_interface_uses_socket_ip_then_preferred_fallback(monkeypatch):
    manager = NetworkManager()
    interfaces = {"eth0": {"isup": True}, "wlan0": {"isup": True}}
    manager._interface_categories = {"eth0": "wired", "wlan0": "wifi"}
    monkeypatch.setattr(
        network_module,
        "psutil",
        SimpleNamespace(
            net_if_addrs=lambda: {
                "wlan0": [SimpleNamespace(family=socket.AF_INET, address="192.0.2.10")]
            }
        ),
    )
    assert manager._detect_active_interface(interfaces, "192.0.2.10") == "wlan0"
    assert manager._detect_active_interface(interfaces, "192.0.2.11") == "eth0"
    assert manager._detect_active_interface(interfaces, None) == "eth0"
    monkeypatch.setattr(network_module, "psutil", None)
    assert manager._detect_active_interface(interfaces, None) == "eth0"


def test_check_status_caches_snapshot_and_warns_for_degraded_wifi(monkeypatch):
    manager = NetworkManager()
    monkeypatch.setattr(manager, "_interface_stats", lambda: {"wlan0": {"isup": True}})
    manager._interface_categories = {"wlan0": "wifi"}
    monkeypatch.setattr(manager, "_attempt_connectivity", lambda: (False, None))
    monkeypatch.setattr(network_module.time, "time", lambda: 42.5)
    warnings = []
    monkeypatch.setattr(
        network_module.LOGGER, "warning", lambda *args: warnings.append(args)
    )

    status = manager.check_status()
    assert status == NetworkStatus(
        active_interface="wlan0",
        interfaces={"wlan0": {"isup": True}},
        wired_available=False,
        wifi_available=True,
        connected=False,
        last_checked=42.5,
    )
    assert manager.last_status is status
    assert warnings and "wlan0" in warnings[0]


def test_check_status_does_not_warn_when_wired_is_preferred(monkeypatch):
    manager = NetworkManager()
    monkeypatch.setattr(
        manager,
        "_interface_stats",
        lambda: {"eth0": {"isup": True}, "wlan0": {"isup": True}},
    )
    manager._interface_categories = {"eth0": "wired", "wlan0": "wifi"}
    monkeypatch.setattr(manager, "_attempt_connectivity", lambda: (False, None))
    warnings = []
    monkeypatch.setattr(
        network_module.LOGGER, "warning", lambda *args: warnings.append(args)
    )
    status = manager.check_status()
    assert status.wired_available and status.wifi_available
    assert warnings == []


def test_ensure_connectivity_switches_to_wired_and_rechecks(monkeypatch):
    manager = NetworkManager()
    manager._interface_categories = {"eth0": "wired"}
    sequence = iter(
        [
            NetworkStatus(
                active_interface="wlan0",
                interfaces={"eth0": {"isup": True}},
                wired_available=True,
                wifi_available=True,
                connected=True,
                last_checked=0.0,
            ),
            _status(connected=True, active="eth0", wired=True, wifi=True),
        ]
    )
    monkeypatch.setattr(manager, "check_status", lambda: next(sequence))
    brought_up = []
    monkeypatch.setattr(manager, "_bring_up_interface", brought_up.append)

    result = manager.ensure_connectivity()
    assert brought_up == ["eth0"]
    assert result.active_interface == "eth0"


def test_ensure_connectivity_fails_over_to_wifi_and_keeps_existing_wired(monkeypatch):
    manager = NetworkManager()
    sequence = iter(
        [
            _status(connected=False, wifi=True),
            _status(connected=True, active="wlan0", wifi=True),
            _status(connected=True, active="eth0", wired=True),
        ]
    )
    monkeypatch.setattr(manager, "check_status", lambda: next(sequence))
    brought_up = []
    monkeypatch.setattr(manager, "_bring_up_interface", brought_up.append)
    monkeypatch.setattr(
        manager,
        "_find_first_available",
        lambda prefixes, _interfaces: (
            "wlan0" if prefixes == network_module.WIFI_PREFIXES else None
        ),
    )
    assert manager.ensure_connectivity().active_interface == "wlan0"
    assert brought_up == ["wlan0"]

    monkeypatch.setattr(
        manager, "check_status", lambda: _status(connected=True, active="eth0")
    )
    assert manager.ensure_connectivity().active_interface == "eth0"


def test_ensure_connectivity_keeps_status_when_no_wifi_interface_is_up(monkeypatch):
    manager = NetworkManager()
    original = _status(connected=False, wifi=True)
    monkeypatch.setattr(manager, "check_status", lambda: original)
    brought_up = []
    monkeypatch.setattr(manager, "_bring_up_interface", brought_up.append)
    assert manager.ensure_connectivity() is original
    assert brought_up == []


def test_ensure_connectivity_returns_when_wired_is_already_active(monkeypatch):
    manager = NetworkManager()
    manager._interface_categories = {"eth0": "wired"}
    original = NetworkStatus(
        active_interface="eth0",
        interfaces={"eth0": {"isup": True}},
        wired_available=True,
        wifi_available=False,
        connected=True,
        last_checked=1.0,
    )
    monkeypatch.setattr(manager, "check_status", lambda: original)
    monkeypatch.setattr(
        manager,
        "_bring_up_interface",
        lambda _interface: pytest.fail(
            "already active wired interface must not be reset"
        ),
    )
    assert manager.ensure_connectivity() is original


def test_ensure_connectivity_does_not_reconnect_same_wired_interface(monkeypatch):
    manager = NetworkManager()
    original = NetworkStatus(
        active_interface="eth0",
        interfaces={"eth0": {"isup": True}},
        wired_available=True,
        wifi_available=True,
        connected=True,
        last_checked=1.0,
    )
    monkeypatch.setattr(manager, "check_status", lambda: original)
    monkeypatch.setattr(
        manager,
        "_bring_up_interface",
        lambda _interface: pytest.fail("no switch needed"),
    )
    assert manager.ensure_connectivity() is original


def test_find_first_available_requires_up_and_matching_prefix():
    manager = NetworkManager()
    assert (
        manager._find_first_available(
            network_module.WIFI_PREFIXES,
            {"wlan0": {"isup": False}, "wlx1": {"isup": True}},
        )
        == "wlx1"
    )
    assert manager._find_first_available(("eth",), {"eth0": {"isup": False}}) is None


@pytest.mark.parametrize(
    ("family", "tools", "expected"),
    [
        ("linux", {"nmcli": "/nmcli"}, ["nmcli", "device", "connect", "eth0"]),
        (
            "macos",
            {"networksetup": "/networksetup"},
            ["networksetup", "-setairportpower", "en0", "on"],
        ),
        (
            "windows",
            {"netsh": "/netsh"},
            ["netsh", "interface", "set", "interface", "name=Wi-Fi", "admin=enabled"],
        ),
    ],
)
def test_bring_up_uses_expected_command_and_escapes_windows_name(
    monkeypatch, family, tools, expected
):
    manager = NetworkManager()
    calls = []
    monkeypatch.setattr(network_module, "detect_host_platform", lambda: _host(family))
    monkeypatch.setattr(network_module.shutil, "which", lambda tool: tools.get(tool))
    monkeypatch.setattr(
        network_module.subprocess,
        "run",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )
    interface = (
        "en0" if family == "macos" else "Wi-Fi" if family == "windows" else "eth0"
    )
    manager._bring_up_interface(interface)
    assert calls[0][0] == expected
    assert calls[0][1]["check"] is False
    assert calls[0][1]["capture_output"] is True

    if family == "windows":
        monkeypatch.setattr(
            network_module.shutil,
            "which",
            lambda tool: "/pwsh" if tool == "pwsh" else None,
        )
        calls.clear()
        manager._bring_up_windows_interface("Guest's Wi-Fi")
        assert "Guest''s Wi-Fi" in calls[0][0][3]


@pytest.mark.parametrize("family,interface", [("linux", "eth0"), ("macos", "en0")])
def test_bring_up_without_platform_tool_is_a_noop(monkeypatch, family, interface):
    manager = NetworkManager()
    monkeypatch.setattr(network_module, "detect_host_platform", lambda: _host(family))
    monkeypatch.setattr(network_module.shutil, "which", lambda _tool: None)
    monkeypatch.setattr(
        network_module.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("must not invoke a missing tool"),
    )
    manager._bring_up_interface(interface)


def test_windows_bring_up_without_powershell_or_netsh_is_a_noop(monkeypatch):
    manager = NetworkManager()
    monkeypatch.setattr(network_module.shutil, "which", lambda _tool: None)
    monkeypatch.setattr(
        network_module.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("must not invoke a missing tool"),
    )
    manager._bring_up_windows_interface("Ethernet")


def test_bring_up_logs_subprocess_errors_without_raising(monkeypatch):
    manager = NetworkManager()
    monkeypatch.setattr(network_module.shutil, "which", lambda _tool: "/tool")
    monkeypatch.setattr(
        network_module.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("denied")),
    )
    for host, method in (
        ("linux", manager._bring_up_linux_interface),
        ("macos", manager._bring_up_macos_interface),
        ("windows", manager._bring_up_windows_interface),
    ):
        monkeypatch.setattr(
            network_module, "detect_host_platform", lambda host=host: _host(host)
        )
        method("eth0")
