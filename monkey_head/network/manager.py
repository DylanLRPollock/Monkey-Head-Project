"""Network manager that prefers wired connections with Wi-Fi failover."""

from __future__ import annotations

import logging
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import psutil  # type: ignore
except Exception:  # pragma: no cover - degrade gracefully
    psutil = None  # type: ignore[assignment]


LOGGER = logging.getLogger(__name__)


WIRED_PREFIXES = ("eth", "enp", "eno", "ens")
WIFI_PREFIXES = ("wlan", "wlx", "wifi", "ath")


@dataclass
class NetworkStatus:
    """Status snapshot returned by :class:`NetworkManager`."""

    active_interface: Optional[str]
    interfaces: Dict[str, Dict[str, Optional[float]]]
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

    # ------------------------------------------------------------------
    def _interface_stats(self) -> Dict[str, Dict[str, Optional[float]]]:
        info: Dict[str, Dict[str, Optional[float]]] = {}
        if psutil is None:
            return info
        for name, stats in psutil.net_if_stats().items():
            info[name] = {
                "isup": float(stats.isup),
                "speed": float(stats.speed or 0),
                "duplex": float(getattr(stats, "duplex", 0) or 0),
            }
        return info

    def _preferred_interface(self, interfaces: Dict[str, Dict[str, Optional[float]]]) -> Optional[str]:
        wired = [name for name in interfaces if name.startswith(WIRED_PREFIXES) and interfaces[name]["isup"]]
        wifi = [name for name in interfaces if name.startswith(WIFI_PREFIXES) and interfaces[name]["isup"]]
        return wired[0] if wired else (wifi[0] if wifi else None)

    def _attempt_connectivity(self) -> bool:
        try:
            with socket.create_connection(
                (self.check_host, self.check_port), timeout=self.check_timeout
            ):
                return True
        except OSError:
            return False

    def check_status(self) -> NetworkStatus:
        interfaces = self._interface_stats()
        preferred = self._preferred_interface(interfaces)
        connected = self._attempt_connectivity()
        status = NetworkStatus(
            active_interface=preferred,
            interfaces=interfaces,
            wired_available=any(
                name.startswith(WIRED_PREFIXES) and details.get("isup")
                for name, details in interfaces.items()
            ),
            wifi_available=any(
                name.startswith(WIFI_PREFIXES) and details.get("isup")
                for name, details in interfaces.items()
            ),
            connected=connected,
            last_checked=time.time(),
        )
        self._last_status = status
        if not connected and status.wifi_available and preferred and preferred.startswith(WIFI_PREFIXES):
            LOGGER.warning("Connectivity degraded while using Wi-Fi interface %s", preferred)
        return status

    # ------------------------------------------------------------------
    def ensure_connectivity(self) -> NetworkStatus:
        status = self.check_status()
        if status.connected and status.active_interface and status.active_interface.startswith(WIRED_PREFIXES):
            return status

        if status.connected and status.wired_available:
            # Wi-Fi is up but wired exists - attempt to switch.
            wired_interface = self._find_first_available(WIRED_PREFIXES, status.interfaces)
            if wired_interface and status.active_interface != wired_interface:
                self._bring_up_interface(wired_interface)
                status = self.check_status()
        elif not status.connected:
            # Attempt Wi-Fi failover.
            wifi_interface = self._find_first_available(WIFI_PREFIXES, status.interfaces)
            if wifi_interface:
                self._bring_up_interface(wifi_interface)
                status = self.check_status()
        return status

    def _find_first_available(
        self, prefixes: tuple[str, ...], interfaces: Dict[str, Dict[str, Optional[float]]]
    ) -> Optional[str]:
        for name, details in interfaces.items():
            if name.startswith(prefixes) and details.get("isup"):
                return name
        return None

    def _bring_up_interface(self, interface: str) -> None:
        LOGGER.info("Attempting to prioritise interface %s", interface)
        if shutil.which("nmcli"):
            try:
                subprocess.run(["nmcli", "device", "connect", interface], check=False, capture_output=True)
            except Exception:  # pragma: no cover - environment specific
                LOGGER.exception("Failed to invoke nmcli for interface %s", interface)
        elif sys.platform.startswith("darwin") and shutil.which("networksetup"):
            try:
                subprocess.run(
                    ["networksetup", "-setairportpower", interface, "on"],
                    check=False,
                    capture_output=True,
                )
            except Exception:  # pragma: no cover
                LOGGER.exception("Failed to invoke networksetup for interface %s", interface)
        else:
            LOGGER.debug("No supported network management tool available")

    @property
    def last_status(self) -> Optional[NetworkStatus]:
        return self._last_status


__all__ = ["NetworkManager", "NetworkStatus"]

