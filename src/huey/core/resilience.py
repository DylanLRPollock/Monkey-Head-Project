# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Resilience module (huey/core)

"""Resilience and emergency management utilities for HueyOS.

This module centralises the logic required to monitor long running
processes, automatically recover from crashes, interface with watchdog
facilities provided by systemd/Kubernetes and coordinate emergency
powers that require quorum style approval.
"""

from __future__ import annotations

import logging
import os
import socket
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterable, List, Optional

LOGGER = logging.getLogger(__name__)

__all__ = [
    "CrashEvent",
    "MonitoredProcess",
    "SystemdWatchdogClient",
    "EmergencyState",
    "RegisteredService",
    "EmergencyServiceStatus",
    "EmergencyGovernanceController",
    "CrashRecoveryManager",
    "HealthCheck",
    "RestartCallback",
]

HealthCheck = Callable[[], bool]
RestartCallback = Callable[[], None]


@dataclass
class CrashEvent:
    """Represents a crash or health failure detected for a monitored process."""

    process: str
    timestamp: float
    restarted: bool
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a serialisable representation of the crash event."""

        return {
            "process": self.process,
            "timestamp": self.timestamp,
            "restarted": self.restarted,
            "message": self.message,
            "metadata": dict(self.metadata),
        }


@dataclass
class MonitoredProcess:
    """A process tracked by :class:`CrashRecoveryManager`."""

    name: str
    health_check: HealthCheck
    restart_callback: RestartCallback
    auto_restart_enabled: bool = True
    last_heartbeat: float = field(default_factory=lambda: time.time())
    last_restart: Optional[float] = None
    restart_attempts: int = 0
    healthy: bool = True
    manual_override_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def check_health(self) -> bool:
        """Execute the configured health check and update cached state."""

        try:
            healthy = bool(self.health_check())
        except Exception as exc:  # pragma: no cover - defensive logging path
            healthy = False
            self.metadata["health_error"] = str(exc)
            LOGGER.exception("Health check for %%s raised an exception", self.name)
        self.healthy = healthy
        self.last_heartbeat = time.time()
        return healthy

    def restart(self) -> None:
        """Invoke the restart callback and update counters."""

        self.restart_callback()
        self.restart_attempts += 1
        self.last_restart = time.time()


class SystemdWatchdogClient:
    """Best-effort interface to the systemd watchdog notification socket."""

    def __init__(self, notify_socket: Optional[str] = None) -> None:
        self.notify_socket = notify_socket or os.environ.get("NOTIFY_SOCKET")

    def _send(self, payload: bytes) -> bool:
        if not self.notify_socket:
            return False
        address = self.notify_socket
        if address.startswith("@"):
            address = "\0" + address[1:]
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            sock.connect(address)
            sock.sendall(payload)
            return True
        except OSError as exc:  # pragma: no cover - environment dependent
            LOGGER.debug("Failed to notify systemd watchdog: %s", exc)
            return False
        finally:
            try:
                sock.close()
            except Exception:  # pragma: no cover - defensive cleanup
                pass

    def ready(self) -> bool:
        """Signal to systemd that the service initialisation completed."""

        return self._send(b"READY=1")

    def ping(self) -> bool:
        """Send a watchdog heartbeat. Returns ``True`` when delivered."""

        return self._send(b"WATCHDOG=1")


class EmergencyState(str, Enum):
    """Operational modes for the emergency governance controller."""

    NORMAL = "normal"
    EMERGENCY = "emergency"


@dataclass
class RegisteredService:
    """Represents a service managed during emergency transitions."""

    name: str
    stop: Callable[[], None]
    start: Optional[Callable[[], None]] = None
    essential: bool = False


@dataclass
class EmergencyServiceStatus:
    """Serialisable status for a service managed by the controller."""

    name: str
    essential: bool
    managed: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "essential": self.essential,
            "managed": self.managed,
        }


class EmergencyGovernanceController:
    """Coordinate the HueyOS emergency powers workflow."""

    def __init__(self, required_approvals: int = 2) -> None:
        if required_approvals < 1:
            raise ValueError("required_approvals must be at least 1")
        self.required_approvals = required_approvals
        self.state = EmergencyState.NORMAL
        self.active_since: Optional[float] = None
        self.reason: Optional[str] = None
        self.triggered_by: Optional[str] = None
        self.approvals: List[str] = []
        self._services: Dict[str, RegisteredService] = {}
        self._lock = threading.RLock()

    def register_service(
        self,
        name: str,
        *,
        stop: Callable[[], None],
        start: Optional[Callable[[], None]] = None,
        essential: bool = False,
    ) -> None:
        """Track a service that should be managed during emergency transitions."""

        with self._lock:
            self._services[name] = RegisteredService(
                name=name, stop=stop, start=start, essential=essential
            )

    def _validate_approvals(
        self, approvals: Iterable[str], initiator: str
    ) -> List[str]:
        unique = {initiator}
        for approval in approvals:
            if approval:
                unique.add(approval)
        if len(unique) < self.required_approvals:
            raise PermissionError(
                "Emergency actions require at least "
                f"{self.required_approvals} distinct approvals"
            )
        return sorted(unique)

    def enter_emergency_mode(
        self, *, triggered_by: str, reason: str, approvals: Iterable[str] = ()
    ) -> None:
        """Activate emergency mode and halt non-essential services."""

        if not reason:
            raise ValueError("An emergency reason must be provided")
        with self._lock:
            if self.state is EmergencyState.EMERGENCY:
                LOGGER.info("Emergency mode already active; ignoring duplicate request")
                return
            self.approvals = self._validate_approvals(approvals, triggered_by)
            self.state = EmergencyState.EMERGENCY
            self.active_since = time.time()
            self.reason = reason
            self.triggered_by = triggered_by
            LOGGER.warning(
                "Emergency mode activated by %s with reason: %s", triggered_by, reason
            )
            for service in self._services.values():
                if service.essential:
                    continue
                try:
                    service.stop()
                    LOGGER.info("Stopped non-essential service: %s", service.name)
                except Exception:  # pragma: no cover - defensive logging
                    LOGGER.exception(
                        "Failed to stop non-essential service %s", service.name
                    )

    def exit_emergency_mode(
        self, *, requested_by: str, approvals: Iterable[str] = ()
    ) -> None:
        """Return HueyOS to normal operations."""

        with self._lock:
            if self.state is EmergencyState.NORMAL:
                LOGGER.info(
                    "Exit request ignored because system is not in emergency mode"
                )
                return
            approval_identities = self._validate_approvals(approvals, requested_by)
            LOGGER.warning(
                "Emergency mode exit authorised by %s (approvals=%s)",
                requested_by,
                approval_identities,
            )
            for service in self._services.values():
                if service.start is None:
                    continue
                try:
                    service.start()
                    LOGGER.info("Restarted service after emergency: %s", service.name)
                except Exception:  # pragma: no cover - defensive logging
                    LOGGER.exception(
                        "Failed to restart service %s after emergency", service.name
                    )
            self.state = EmergencyState.NORMAL
            self.active_since = None
            self.reason = None
            self.triggered_by = None
            self.approvals = []

    def request_authorised_action(
        self, *, actor: str, approvals: Iterable[str], action: str
    ) -> None:
        """Validate quorum before allowing an emergency-only action."""

        self._validate_approvals(approvals, actor)
        LOGGER.info(
            "Action '%s' authorised by %s with approvals %s",
            action,
            actor,
            sorted(set(approvals) | {actor}),
        )

    def status(self) -> Dict[str, Any]:
        """Return a serialisable snapshot of the emergency state."""

        with self._lock:
            services = [
                EmergencyServiceStatus(
                    name=service.name,
                    essential=service.essential,
                    managed=True,
                )
                for service in self._services.values()
            ]
            return {
                "state": self.state.value,
                "active_since": self.active_since,
                "reason": self.reason,
                "triggered_by": self.triggered_by,
                "approvals": list(self.approvals),
                "services": [service.to_dict() for service in services],
            }


class CrashRecoveryManager:
    """Monitor a set of processes and restart them when crashes occur."""

    def __init__(
        self,
        watchdog: Optional[SystemdWatchdogClient] = None,
        *,
        history_limit: int = 100,
    ) -> None:
        if history_limit < 1:
            raise ValueError("history_limit must be at least 1")
        self._watchdog = watchdog or SystemdWatchdogClient()
        self._processes: Dict[str, MonitoredProcess] = {}
        self._lock = threading.RLock()
        self._event_log: deque[CrashEvent] = deque(maxlen=history_limit)

    def register_process(
        self,
        name: str,
        *,
        health_check: HealthCheck,
        restart: RestartCallback,
        auto_restart: bool = True,
    ) -> None:
        """Register a process for monitoring and automatic recovery."""

        with self._lock:
            self._processes[name] = MonitoredProcess(
                name=name,
                health_check=health_check,
                restart_callback=restart,
                auto_restart_enabled=auto_restart,
            )
            LOGGER.debug("Registered monitored process: %s", name)

    def unregister_process(self, name: str) -> None:
        """Stop monitoring a previously registered process."""

        with self._lock:
            self._processes.pop(name, None)
            LOGGER.debug("Unregistered monitored process: %s", name)

    def poll(self) -> List[CrashEvent]:
        """Check the health of all processes and restart crashed ones."""

        events: List[CrashEvent] = []
        with self._lock:
            for process in self._processes.values():
                healthy = process.check_health()
                if healthy:
                    continue
                metadata: Dict[str, Any] = {}
                restarted = False
                message = "Process reported unhealthy state"
                if process.auto_restart_enabled:
                    try:
                        process.restart()
                        restarted = True
                        message = "Process restarted after crash"
                    except Exception as exc:  # pragma: no cover - defensive logging
                        metadata["restart_error"] = str(exc)
                        message = f"Automatic restart failed: {exc}"
                        LOGGER.exception(
                            "Automatic restart failed for process %s", process.name
                        )
                else:
                    metadata["manual_override"] = process.manual_override_reason or True
                    message = "Automatic restart bypassed due to manual override"
                event = CrashEvent(
                    process=process.name,
                    timestamp=time.time(),
                    restarted=restarted,
                    message=message,
                    metadata=metadata,
                )
                events.append(event)
                self._event_log.append(event)
                LOGGER.warning(
                    "Crash detected for process %s (auto_restart=%s, restarted=%s)",
                    process.name,
                    process.auto_restart_enabled,
                    restarted,
                )
        self.ping_watchdog()
        return events

    def ping_watchdog(self) -> bool:
        """Notify systemd that the watchdog is still alive."""

        return self._watchdog.ping()

    def _serialise_process(self, process: MonitoredProcess) -> Dict[str, Any]:
        return {
            "name": process.name,
            "healthy": process.healthy,
            "auto_restart": process.auto_restart_enabled,
            "last_heartbeat": process.last_heartbeat,
            "last_restart": process.last_restart,
            "restart_attempts": process.restart_attempts,
            "manual_override_reason": process.manual_override_reason,
        }

    def toggle_auto_restart(
        self, name: str, enabled: bool, *, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enable or disable automatic restarts and return updated status."""

        with self._lock:
            process = self._processes.get(name)
            if process is None:
                raise KeyError(f"Unknown monitored process: {name}")
            process.auto_restart_enabled = enabled
            process.manual_override_reason = reason if not enabled else None
            LOGGER.info(
                "Manual override for %s set to %s (reason=%s)",
                name,
                enabled,
                reason,
            )
            return self._serialise_process(process)

    def set_auto_restart(
        self, name: str, enabled: bool, *, reason: Optional[str] = None
    ) -> None:
        """Compatibility wrapper for :meth:`toggle_auto_restart`."""

        self.toggle_auto_restart(name, enabled, reason=reason)

    def manual_restart(self, name: str) -> None:
        """Force restart a process even when auto-restart is disabled."""

        with self._lock:
            process = self._processes.get(name)
            if process is None:
                raise KeyError(f"Unknown monitored process: {name}")
            process.restart()
            name_sanitized = name.replace('\r', '').replace('\n', '')
            LOGGER.info("Manual restart executed for process %s", name_sanitized)

    def statuses(self) -> List[Dict[str, Any]]:
        """Return serialisable status information for each process."""

        with self._lock:
            return [
                self._serialise_process(process) for process in self._processes.values()
            ]

    def has_process(self, name: str) -> bool:
        """Return ``True`` when a process is registered."""

        with self._lock:
            return name in self._processes

    def event_log(self) -> List[CrashEvent]:
        """Return a copy of the recorded crash events."""

        with self._lock:
            return list(self._event_log)
