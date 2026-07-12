# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Manager module (huey/network)

"""Network manager that prefers wired connections with Wi-Fi failover."""

from __future__ import annotations

import contextlib
import logging
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:  # pragma: no cover - optional dependency
    import psutil  # type: ignore
except Exception:  # pragma: no cover - degrade gracefully
    psutil = None  # type: ignore[assignment]

from huey.os.core.platform_support import detect_host_platform

LOGGER = logging.getLogger(__name__)


WIRED_PREFIXES = ("eth", "enp", "eno", "ens", "em")
WIFI_PREFIXES = ("wlan", "wlx", "wifi", "ath", "wl")
WINDOWS_WIRED_PREFIXES = ("ethernet", "local area connection", "lan")
WINDOWS_WIFI_PREFIXES = ("wi-fi", "wifi", "wlan", "wireless")
LOOPBACK_INTERFACES = {"lo", "lo0"}
MACOS_WIRED_PORT_MARKERS = ("ethernet", "thunderbolt bridge")
MACOS_WIFI_PORT_MARKERS = ("wi-fi", "airport")


InterfaceInfo = Dict[str, Any]


@dataclass
class NetworkStatus:
    """Status snapshot returned by :class:`NetworkManager`."""

    active_interface: Optional[str]
    interfaces: Dict[str, InterfaceInfo]
    wired_available: bool
    wifi_available: bool
    connected: bool
    last_checked: float


class NetworkManager:
    """Monitor connectivity and ensure wired-first network availability."""

    def __init__(
        self,
        *,
        check_host: str = "8.8.8.8",
        check_port: int = 53,
        check_timeout: float = 2.0,
    ) -> None:
        self.check_host = check_host
        self.check_port = check_port
        self.check_timeout = check_timeout
        self._last_status: Optional[NetworkStatus] = None
        self._interface_categories: Dict[str, str] = {}
        self._macos_device_categories: Dict[str, str] = {}

    # ------------------------------------------------------------------
    def _interface_stats(self) -> Dict[str, InterfaceInfo]:
        """Gather interface information from :mod:`psutil` or sysfs."""

        self._interface_categories = {}
        info: Dict[str, InterfaceInfo] = {}
        if psutil is not None:
            stats = psutil.net_if_stats()
        else:  # pragma: no cover - psutil is optional dependency
            stats = {}

        for name, stat in stats.items():
            category = self._interface_category(name)
            self._interface_categories[name] = category
            info[name] = self._build_interface_entry(name, stat)

        if info:
            return info

        # Fallback to sysfs when psutil is not available.
        sysfs_root = Path("/sys/class/net")
        if not sysfs_root.exists():  # pragma: no cover - platform specific
            return info

        for path in sysfs_root.iterdir():  # pragma: no cover - requires linux sysfs
            if not path.is_dir():
                continue
            name = path.name
            if name in LOOPBACK_INTERFACES:
                continue
            category = self._interface_category(name)
            self._interface_categories[name] = category
            info[name] = {
                "isup": self._read_sysfs_flag(path / "operstate"),
                "speed": self._read_sysfs_float(path / "speed"),
                "mtu": self._read_sysfs_float(path / "mtu"),
                "duplex": None,
            }
        return info

    def _build_interface_entry(self, name: str, stat: Any) -> InterfaceInfo:
        """Compose a serialisable structure for a network interface."""

        # Import locally to keep typing flexible when psutil is missing.
        entry: InterfaceInfo = {
            "isup": bool(getattr(stat, "isup", False)),
            "speed": float(getattr(stat, "speed", 0)) or None,
            "duplex": float(getattr(stat, "duplex", 0)) or None,
            "mtu": float(getattr(stat, "mtu", 0)) or None,
        }
        return entry

    def _read_sysfs_flag(self, path: Path) -> bool:
        try:
            value = path.read_text().strip()
        except OSError:
            return False
        return value.lower() in {"up", "1", "yes", "true"}

    def _read_sysfs_float(self, path: Path) -> Optional[float]:
        try:
            value = path.read_text().strip()
        except OSError:
            return None
        if not value:
            return None
        with contextlib.suppress(ValueError):
            return float(value)

    def _interface_category(self, name: str) -> str:
        host = detect_host_platform()
        lowered = name.casefold()
        if name in LOOPBACK_INTERFACES:
            return "loopback"

        if host.is_macos:
            category = self._macos_interface_category(name)
            if category:
                return category
        elif host.is_windows:
            if lowered.startswith(WINDOWS_WIRED_PREFIXES):
                return "wired"
            if lowered.startswith(WINDOWS_WIFI_PREFIXES):
                return "wifi"

        if lowered.startswith(WIRED_PREFIXES + WINDOWS_WIRED_PREFIXES):
            return "wired"
        if lowered.startswith(WIFI_PREFIXES + WINDOWS_WIFI_PREFIXES):
            return "wifi"
        return "other"

    def _macos_interface_category(self, name: str) -> str | None:
        if not self._macos_device_categories:
            self._macos_device_categories = self._load_macos_device_categories()
        return self._macos_device_categories.get(name)

    def _load_macos_device_categories(self) -> Dict[str, str]:
        if not shutil.which("networksetup"):
            return {}

        try:
            result = subprocess.run(
                ["networksetup", "-listallhardwareports"],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:  # pragma: no cover - environment specific
            LOGGER.debug("Unable to inspect macOS hardware ports", exc_info=True)
            return {}

        if result.returncode != 0:
            return {}

        categories: Dict[str, str] = {}
        current_port = ""
        for raw_line in result.stdout.splitlines():
            line = raw_line.strip()
            if not line:
                current_port = ""
                continue
            if line.startswith("Hardware Port:"):
                current_port = line.partition(":")[2].strip().casefold()
                continue
            if not line.startswith("Device:"):
                continue

            device = line.partition(":")[2].strip()
            if not device:
                continue
            if any(marker in current_port for marker in MACOS_WIFI_PORT_MARKERS):
                categories[device] = "wifi"
            elif any(marker in current_port for marker in MACOS_WIRED_PORT_MARKERS):
                categories[device] = "wired"
            else:
                categories.setdefault(device, "other")

        return categories

    def _preferred_interface(
        self, interfaces: Dict[str, InterfaceInfo]
    ) -> Optional[str]:
        wired = [
            name
            for name, details in interfaces.items()
            if self._interface_categories.get(name) == "wired" and details.get("isup")
        ]
        wifi = [
            name
            for name, details in interfaces.items()
            if self._interface_categories.get(name) == "wifi" and details.get("isup")
        ]
        return wired[0] if wired else (wifi[0] if wifi else None)

    def _attempt_connectivity(self) -> Tuple[bool, Optional[str]]:
        try:
            with socket.create_connection(
                (self.check_host, self.check_port), timeout=self.check_timeout
            ) as sock:
                local_ip = sock.getsockname()[0]
            return True, local_ip
        except OSError:
            return False, None

    def _detect_active_interface(
        self,
        interfaces: Dict[str, InterfaceInfo],
        local_ip: Optional[str],
    ) -> Optional[str]:
        if psutil is None:
            return self._preferred_interface(interfaces)

        if local_ip:
            addrs = psutil.net_if_addrs()
            for name, iface_addrs in addrs.items():
                for addr in iface_addrs:
                    if (
                        getattr(addr, "family", None) == socket.AF_INET
                        and addr.address == local_ip
                    ):
                        return name

        # Fall back to simply returning the preferred active interface.
        return self._preferred_interface(interfaces)

    def check_status(self) -> NetworkStatus:
        interfaces = self._interface_stats()
        connected, local_ip = self._attempt_connectivity()
        active_interface = self._detect_active_interface(interfaces, local_ip)
        preferred = self._preferred_interface(interfaces)
        status = NetworkStatus(
            active_interface=active_interface,
            interfaces=interfaces,
            wired_available=any(
                self._interface_categories.get(name) == "wired" and details.get("isup")
                for name, details in interfaces.items()
            ),
            wifi_available=any(
                self._interface_categories.get(name) == "wifi" and details.get("isup")
                for name, details in interfaces.items()
            ),
            connected=connected,
            last_checked=time.time(),
        )
        self._last_status = status
        if (
            not connected
            and status.wifi_available
            and preferred
            and preferred.startswith(WIFI_PREFIXES)
        ):
            LOGGER.warning(
                "Connectivity degraded while using Wi-Fi interface %s", preferred
            )
        return status

    # ------------------------------------------------------------------
    def ensure_connectivity(self) -> NetworkStatus:
        status = self.check_status()
        if (
            status.connected
            and status.active_interface
            and self._interface_categories.get(status.active_interface) == "wired"
        ):
            return status

        if status.connected and status.wired_available:
            # Wi-Fi is up but wired exists - attempt to switch.
            wired_interface = self._find_first_available(
                WIRED_PREFIXES, status.interfaces
            )
            if wired_interface and status.active_interface != wired_interface:
                self._bring_up_interface(wired_interface)
                status = self.check_status()
        elif not status.connected:
            # Attempt Wi-Fi failover.
            wifi_interface = self._find_first_available(
                WIFI_PREFIXES, status.interfaces
            )
            if wifi_interface:
                self._bring_up_interface(wifi_interface)
                status = self.check_status()
        return status

    def _find_first_available(
        self, prefixes: tuple[str, ...], interfaces: Dict[str, InterfaceInfo]
    ) -> Optional[str]:
        for name, details in interfaces.items():
            if name.startswith(prefixes) and details.get("isup"):
                return name
        return None

    def _bring_up_interface(self, interface: str) -> None:
        LOGGER.info("Attempting to prioritise interface %s", interface)
        host = detect_host_platform()
        if host.is_windows:
            self._bring_up_windows_interface(interface)
        elif host.is_macos:
            self._bring_up_macos_interface(interface)
        else:
            self._bring_up_linux_interface(interface)

    def _bring_up_linux_interface(self, interface: str) -> None:
        if not shutil.which("nmcli"):
            LOGGER.debug("No supported Linux network management tool available")
            return
        try:
            subprocess.run(
                ["nmcli", "device", "connect", interface],
                check=False,
                capture_output=True,
            )
        except Exception:  # pragma: no cover - environment specific
            LOGGER.exception("Failed to invoke nmcli for interface %s", interface)

    def _bring_up_macos_interface(self, interface: str) -> None:
        if not shutil.which("networksetup"):
            LOGGER.debug("No supported macOS network management tool available")
            return
        try:
            subprocess.run(
                ["networksetup", "-setairportpower", interface, "on"],
                check=False,
                capture_output=True,
            )
        except Exception:  # pragma: no cover
            LOGGER.exception(
                "Failed to invoke networksetup for interface %s", interface
            )

    def _bring_up_windows_interface(self, interface: str) -> None:
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if powershell:
            escaped_interface = interface.replace("'", "''")
            try:
                subprocess.run(
                    [
                        powershell,
                        "-NoProfile",
                        "-Command",
                        f"Enable-NetAdapter -Name '{escaped_interface}' -Confirm:$false",
                    ],
                    check=False,
                    capture_output=True,
                )
            except Exception:  # pragma: no cover - environment specific
                LOGGER.exception(
                    "Failed to invoke PowerShell for interface %s", interface
                )
            return

        if shutil.which("netsh"):
            try:
                subprocess.run(
                    [
                        "netsh",
                        "interface",
                        "set",
                        "interface",
                        f"name={interface}",
                        "admin=enabled",
                    ],
                    check=False,
                    capture_output=True,
                )
            except Exception:  # pragma: no cover - environment specific
                LOGGER.exception("Failed to invoke netsh for interface %s", interface)
            return

        LOGGER.debug("No supported Windows network management tool available")

    @property
    def last_status(self) -> Optional[NetworkStatus]:
        return self._last_status


__all__ = ["NetworkManager", "NetworkStatus"]
