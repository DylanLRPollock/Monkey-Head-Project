# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Management module (huey/power)

"""Battery monitoring and safe shutdown routines."""

from __future__ import annotations

import contextlib
import logging
import re
import shutil
import subprocess
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, DefaultDict, Dict, List, Optional

try:  # pragma: no cover - optional dependency
    import psutil  # type: ignore
except ImportError:  # pragma: no cover - degrade gracefully
    psutil = None  # type: ignore[assignment]

from huey.os.core.platform_support import detect_host_platform

LOGGER = logging.getLogger(__name__)


@dataclass
class PowerEvent:
    """Represents a power management action."""

    timestamp: float
    action: str
    metadata: Dict[str, Any]


class BatteryMonitor:
    """High level helper for querying battery status and issuing shutdowns."""

    def __init__(self, *, shutdown_threshold: float = 5.0) -> None:
        self.shutdown_threshold = shutdown_threshold
        self._last_event: Optional[PowerEvent] = None
        self._listeners: DefaultDict[str, List[Callable[[Dict[str, Any]], None]]] = (
            defaultdict(list)
        )
        self._last_status: Optional[Dict[str, Any]] = None
        self._low_battery_triggered = False

    # ------------------------------------------------------------------
    def get_status(self) -> Dict[str, Any]:
        """Return current battery metrics.

        The monitor prefers :mod:`psutil` when available but can fall back to
        Linux ``/sys`` data or ``acpi`` command output. The returned mapping
        always contains the keys required by :class:`BatteryStatusResponse`.
        """

        status = (
            self._status_from_psutil()
            or self._status_from_sysfs()
            or self._status_from_acpi()
            or self._empty_status()
        )

        secs_left = status.get("secs_left")
        if isinstance(secs_left, (int, float)) and secs_left >= 0:
            status["estimated_runtime_minutes"] = secs_left / 60.0
        else:
            status["estimated_runtime_minutes"] = None
        return self.observe(status)

    # ------------------------------------------------------------------
    def should_shutdown(self) -> bool:
        status = self.get_status()
        percent = status.get("percent")
        if percent is None:
            return False
        if status.get("power_plugged"):
            return False
        return percent <= self.shutdown_threshold

    # ------------------------------------------------------------------
    def initiate_shutdown(self) -> PowerEvent:
        """Trigger a safe shutdown sequence using available system tools."""

        return self._execute_power_action(
            "shutdown", {"threshold": self.shutdown_threshold}
        )

    def initiate_hibernate(self) -> PowerEvent:
        """Put the system into hibernation if supported."""

        return self._execute_power_action("hibernate", {})

    def initiate_sleep(self) -> PowerEvent:
        """Suspend the system to RAM if supported."""

        return self._execute_power_action("sleep", {})

    def initiate_reboot(self) -> PowerEvent:
        """Reboot the system using the preferred toolchain."""

        return self._execute_power_action("reboot", {})

    # ------------------------------------------------------------------
    def register_hook(
        self, event: str, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Register ``callback`` to be invoked when ``event`` occurs."""

        self._listeners[event].append(callback)

    def remove_hook(
        self, event: str, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        listeners = self._listeners.get(event)
        if not listeners:
            return
        with contextlib.suppress(ValueError):
            listeners.remove(callback)

    def observe(self, status: Dict[str, Any]) -> Dict[str, Any]:
        """Process an externally supplied ``status`` dictionary."""

        enriched = dict(status)
        enriched.setdefault("threshold", self.shutdown_threshold)
        enriched.setdefault("timestamp", time.time())
        self._dispatch_events(enriched)
        self._last_status = enriched
        return enriched

    def _dispatch_events(self, status: Dict[str, Any]) -> None:
        percent = status.get("percent")
        plugged = status.get("power_plugged")
        threshold = status.get("threshold", self.shutdown_threshold)

        if percent is not None and not bool(plugged) and percent <= threshold:
            if not self._low_battery_triggered:
                self._low_battery_triggered = True
                self._emit("battery_low", status)
        elif self._low_battery_triggered and (
            plugged or percent is None or percent > threshold
        ):
            self._low_battery_triggered = False
            self._emit("battery_recovered", status)

        previous_plugged = None
        if self._last_status is not None:
            previous_plugged = self._last_status.get("power_plugged")
        if plugged is not None and plugged != previous_plugged:
            event = "power_connected" if plugged else "power_disconnected"
            self._emit(event, status)

        self._emit("status", status)

    def _emit(self, event: str, status: Dict[str, Any]) -> None:
        for callback in list(self._listeners.get(event, [])):
            try:
                callback(status)
            except Exception:  # pragma: no cover - callbacks should not break monitor
                LOGGER.exception("Battery event hook '%s' failed", event)

    # ------------------------------------------------------------------
    def _status_from_psutil(self) -> Optional[Dict[str, Any]]:
        if not psutil or not hasattr(psutil, "sensors_battery"):
            return None
        try:
            battery = psutil.sensors_battery()  # type: ignore[attr-defined]
        except (OSError, AttributeError):  # pragma: no cover - psutil can raise
            LOGGER.debug("psutil.sensors_battery raised an exception", exc_info=True)
            return None
        if battery is None:
            return None

        secs_left = getattr(battery, "secsleft", None)
        unknown = getattr(psutil, "POWER_TIME_UNKNOWN", -1)
        unlimited = getattr(psutil, "POWER_TIME_UNLIMITED", -2)
        if secs_left in (unknown, unlimited):
            secs_left = None

        percent = getattr(battery, "percent", None)
        plugged = getattr(battery, "power_plugged", None)
        return {
            "percent": float(percent) if percent is not None else None,
            "secs_left": (
                float(secs_left) if isinstance(secs_left, (int, float)) else None
            ),
            "power_plugged": bool(plugged) if plugged is not None else None,
            "source": "psutil",
        }

    def _status_from_sysfs(self) -> Optional[Dict[str, Any]]:
        sysfs_root = Path("/sys/class/power_supply")
        if not sysfs_root.exists():  # pragma: no cover - platform specific
            return None

        battery_dirs = [
            path
            for path in sysfs_root.iterdir()
            if path.is_dir() and path.name.lower().startswith(("bat", "battery"))
        ]
        if not battery_dirs:
            return None

        battery = battery_dirs[0]
        percent = self._read_sysfs_float(battery / "capacity")
        status_text = self._read_sysfs_text(battery / "status")
        power_now = self._read_sysfs_float(battery / "power_now")
        if power_now is None:
            power_now = self._read_sysfs_float(battery / "current_now")
        energy_now = self._read_sysfs_float(battery / "energy_now")
        if energy_now is None:
            energy_now = self._read_sysfs_float(battery / "charge_now")

        secs_left = None
        if (
            energy_now is not None
            and power_now is not None
            and power_now > 0
            and status_text
            and status_text.lower().startswith("dis")
        ):
            secs_left = float(energy_now / power_now * 3600.0)

        ac_online = self._ac_adapter_online(sysfs_root)
        if ac_online is None and status_text:
            ac_online = status_text.lower() in {"charging", "full"}

        return {
            "percent": percent,
            "secs_left": secs_left,
            "power_plugged": ac_online,
            "source": "sysfs",
        }

    def _status_from_acpi(self) -> Optional[Dict[str, Any]]:
        acpi_cmd = shutil.which("acpi")
        if not acpi_cmd:  # pragma: no cover - depends on tooling
            return None
        try:
            output = subprocess.check_output(
                [acpi_cmd, "-b"], text=True, stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, OSError) as e:
            LOGGER.debug("acpi command failed: %s", e)
            return None
        if not output:
            return None

        percent: Optional[float] = None
        secs_left: Optional[float] = None
        power_plugged: Optional[bool] = None
        for line in output.splitlines():
            percent_match = re.search(r"(\d+(?:\.\d+)?)%", line)
            if percent_match:
                with contextlib.suppress(ValueError):
                    percent = float(percent_match.group(1))
            time_match = re.search(r"(\d+):(\d+):(\d+)", line)
            if time_match:
                hours, minutes, seconds = map(int, time_match.groups())
                secs_left = float(hours * 3600 + minutes * 60 + seconds)
            if "Charging" in line or "Full" in line:
                power_plugged = True
            elif "Discharging" in line:
                power_plugged = False

        if percent is None and secs_left is None and power_plugged is None:
            return None
        return {
            "percent": percent,
            "secs_left": secs_left,
            "power_plugged": power_plugged,
            "source": "acpi",
        }

    def _empty_status(self) -> Dict[str, Any]:
        return {
            "percent": None,
            "secs_left": None,
            "power_plugged": None,
            "source": "unknown",
            "estimated_runtime_minutes": None,
        }

    # ------------------------------------------------------------------
    def _read_sysfs_text(self, path: Path) -> Optional[str]:
        try:
            value = path.read_text().strip()
        except OSError:
            return None
        return value or None

    def _read_sysfs_float(self, path: Path) -> Optional[float]:
        text = self._read_sysfs_text(path)
        if text is None:
            return None
        with contextlib.suppress(ValueError):
            return float(text)

    def _ac_adapter_online(self, root: Path) -> Optional[bool]:
        for supply in root.iterdir():
            if not supply.is_dir():
                continue
            name = supply.name.lower()
            if not name.startswith(("ac", "mains", "adp", "psu")):
                continue
            try:
                text = (supply / "online").read_text().strip()
            except OSError:
                continue
            if text == "":
                continue
            if text in {"1", "on", "online", "yes", "true"}:
                return True
            if text in {"0", "off", "offline", "no", "false"}:
                return False
        return None

    # ------------------------------------------------------------------
    def _execute_power_action(
        self, action: str, base_metadata: Dict[str, Any]
    ) -> PowerEvent:
        timestamp = time.time()
        host = detect_host_platform()
        command = self._resolve_command(action)
        metadata: Dict[str, Any] = {
            "action": action,
            "platform": host.display_name,
            "platform_family": host.family,
        }
        metadata.update(base_metadata)
        if command:
            metadata["command"] = command
            try:
                subprocess.Popen(command)  # pragma: no cover - system side effects
            except (OSError, subprocess.CalledProcessError) as exc:
                LOGGER.exception("Failed to execute %s command %s", action, command)
                metadata["error"] = str(exc)
        else:
            metadata["error"] = "no supported command found"

        event = PowerEvent(timestamp=timestamp, action=action, metadata=metadata)
        self._last_event = event
        return event

    def _resolve_command(self, action: str) -> Optional[List[str]]:
        action = action.lower()
        host = detect_host_platform()
        if host.is_windows:
            return self._windows_command(action)
        if host.is_macos:
            return self._darwin_command(action)
        if host.is_linux:
            return self._linux_command(action)
        LOGGER.warning(
            "No power action implementation is available for %s", host.system
        )
        return None

    def _linux_command(self, action: str) -> Optional[List[str]]:
        if action == "shutdown":
            if shutil.which("systemctl"):
                return ["systemctl", "poweroff"]
            return ["shutdown", "-h", "now"]
        if action == "reboot":
            if shutil.which("systemctl"):
                return ["systemctl", "reboot"]
            return ["shutdown", "-r", "now"]
        if action in {"hibernate", "sleep"}:
            subcommand = "hibernate" if action == "hibernate" else "suspend"
            if shutil.which("systemctl"):
                return ["systemctl", subcommand]
            legacy = "pm-hibernate" if action == "hibernate" else "pm-suspend"
            if shutil.which(legacy):
                return [legacy]
        return None

    def _darwin_command(self, action: str) -> Optional[List[str]]:
        if action == "shutdown":
            return ["osascript", "-e", 'tell app "System Events" to shut down']
        if action == "reboot":
            return ["osascript", "-e", 'tell app "System Events" to restart']
        if action in {"sleep", "hibernate"} and shutil.which("pmset"):
            return ["pmset", "sleepnow"]
        return None

    def _windows_command(self, action: str) -> Optional[List[str]]:
        if action == "shutdown":
            return ["shutdown", "/s", "/t", "0"]
        if action == "reboot":
            return ["shutdown", "/r", "/t", "0"]
        if action == "sleep":
            return ["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"]
        if action == "hibernate":
            return ["shutdown", "/h"]
        return None

    @property
    def last_event(self) -> Optional[PowerEvent]:
        return self._last_event


__all__ = ["BatteryMonitor", "PowerEvent"]
