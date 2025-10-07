"""Battery monitoring and safe shutdown routines."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency
    import psutil  # type: ignore
except Exception:  # pragma: no cover - degrade gracefully
    psutil = None  # type: ignore[assignment]


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

    def get_status(self) -> Dict[str, Any]:
        """Return battery metrics using :mod:`psutil` when available."""

        if psutil and hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()  # type: ignore[attr-defined]
        else:  # pragma: no cover - running without psutil
            battery = None
        if battery is None:
            return {
                "percent": None,
                "secs_left": None,
                "power_plugged": None,
                "estimated_runtime_minutes": None,
            }
        secs_left = battery.secsleft if battery.secsleft not in (psutil.POWER_TIME_UNKNOWN, psutil.POWER_TIME_UNLIMITED) else None  # type: ignore[attr-defined]
        return {
            "percent": float(battery.percent),
            "secs_left": secs_left,
            "power_plugged": bool(battery.power_plugged),
            "estimated_runtime_minutes": (secs_left / 60) if secs_left else None,
        }

    def should_shutdown(self) -> bool:
        status = self.get_status()
        percent = status.get("percent")
        if percent is None:
            return False
        if status.get("power_plugged"):
            return False
        return percent <= self.shutdown_threshold

    def initiate_shutdown(self) -> PowerEvent:
        """Trigger a safe shutdown sequence using available system tools."""

        timestamp = time.time()
        metadata = {"threshold": self.shutdown_threshold}
        if shutil.which("systemctl"):
            cmd = ["systemctl", "poweroff"]
        elif sys.platform.startswith("darwin"):
            cmd = ["osascript", "-e", 'tell app "System Events" to shut down']
        else:
            cmd = ["shutdown", "-h", "now"]
        metadata["command"] = cmd
        try:
            subprocess.Popen(cmd)  # pragma: no cover - side effect heavy
        except Exception as exc:  # pragma: no cover - best effort logging
            LOGGER.exception("Failed to execute shutdown command %s", cmd)
            metadata["error"] = str(exc)
        event = PowerEvent(timestamp=timestamp, action="shutdown", metadata=metadata)
        self._last_event = event
        return event

    @property
    def last_event(self) -> Optional[PowerEvent]:
        return self._last_event


__all__ = ["BatteryMonitor", "PowerEvent"]

