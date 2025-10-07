import pytest

from monkey_head.core.resilience import (
    CrashRecoveryManager,
    EmergencyGovernanceController,
    EmergencyState,
)


class DummyWatchdog:
    def __init__(self) -> None:
        self.pings = 0

    def ping(self) -> bool:
        self.pings += 1
        return True


def test_crash_recovery_manager_restarts_crashed_process():
    state = {"healthy": False, "restart_calls": 0}

    def health_check() -> bool:
        return state["healthy"]

    def restart() -> None:
        state["restart_calls"] += 1
        state["healthy"] = True

    manager = CrashRecoveryManager(watchdog=DummyWatchdog())
    manager.register_process("spark-loop", health_check=health_check, restart=restart)

    events = manager.poll()
    assert events
    assert events[0].restarted is True
    assert state["restart_calls"] == 1

    status = manager.statuses()[0]
    assert status["restart_attempts"] == 1
    assert status["auto_restart"] is True


def test_crash_recovery_manual_override_prevents_restart():
    state = {"healthy": False}

    def health_check() -> bool:
        return state["healthy"]

    def restart() -> None:
        state["healthy"] = True

    manager = CrashRecoveryManager(watchdog=DummyWatchdog())
    manager.register_process("zap-loop", health_check=health_check, restart=restart)
    manager.set_auto_restart("zap-loop", False, reason="maintenance window")

    events = manager.poll()
    assert events[0].restarted is False
    assert events[0].metadata["manual_override"] == "maintenance window"


def test_emergency_governance_controller_requires_quorum():
    controller = EmergencyGovernanceController(required_approvals=2)

    stop_calls: list[str] = []
    start_calls: list[str] = []

    controller.register_service(
        "ollama",
        stop=lambda: stop_calls.append("stop"),
        start=lambda: start_calls.append("start"),
    )

    with pytest.raises(PermissionError):
        controller.enter_emergency_mode(triggered_by="spark", reason="grid", approvals=[])

    controller.enter_emergency_mode(triggered_by="spark", reason="grid", approvals=["zap"])
    assert controller.state is EmergencyState.EMERGENCY
    assert stop_calls == ["stop"]

    controller.exit_emergency_mode(requested_by="spark", approvals=["zap"])
    assert controller.state is EmergencyState.NORMAL
    assert start_calls == ["start"]

    controller.enter_emergency_mode(triggered_by="spark", reason="grid", approvals=["zap"])
    controller.request_authorised_action(actor="spark", approvals=["zap"], action="shed-load")
