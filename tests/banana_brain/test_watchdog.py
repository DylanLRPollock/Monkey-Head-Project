"""Failure and recovery behavior for the Banana Brain watchdog."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from huey.banana_brain.watchdog import HealthSignal, Severity, Watchdog, _resolve_probe


class Monitor:
    def __init__(self, status=None):
        self.status = status

    async def get_status(self):
        return self.status


class VRAM:
    def __init__(self, reservations=None):
        self.reservations = reservations or []

    async def snapshot(self):
        return {"reservations": self.reservations}


class SchedulerStub:
    current_job = None

    def __init__(self):
        self.cancel = AsyncMock(return_value=True)


def make_watchdog(
    *,
    status=None,
    scheduler=None,
    reservations=None,
    adapters=None,
    mode_manager=None,
    config=None,
    notifications=None,
):
    defaults = {
        "watchdog_gpu_unavailable_warn_s": 0,
        "watchdog_gpu_unavailable_critical_s": 1000,
        "watchdog_temperature_warn_c": 70,
        "watchdog_temperature_ceiling_c": 85,
        "watchdog_stuck_job_seconds": 0,
        "watchdog_cancel_grace_seconds": 0,
        "watchdog_service_failure_threshold": 2,
        "watchdog_lease_expiry_seconds": 10,
        "watchdog_signal_cooldown_seconds": 600,
    }
    defaults.update(config or {})
    return Watchdog(
        defaults,
        scheduler=scheduler or SchedulerStub(),
        gpu_monitor=Monitor(status),
        vram_manager=VRAM(reservations),
        job_store=None,
        adapters=adapters or {},
        mode_manager=mode_manager,
        notifications=notifications,
    )


@pytest.mark.asyncio
async def test_visibility_escalates_once_and_restoration_resets_timer():
    halt = AsyncMock()
    wd = make_watchdog(
        mode_manager=SimpleNamespace(force_safety_halt=halt),
        config={"watchdog_gpu_unavailable_critical_s": 0},
    )
    signals = await wd._check_gpu_visibility()
    assert signals[0].severity is Severity.CRITICAL
    assert signals[0].action == "safety_halt_engaged"
    assert len(await wd._check_gpu_visibility()) == 1
    assert halt.await_count == 1
    wd._gpu_monitor.status = SimpleNamespace(temperature_c=40)
    assert await wd._check_gpu_visibility() == []
    assert wd._gpu_unavailable_since is None


@pytest.mark.asyncio
async def test_temperature_ceiling_and_clear_signal_keep_halt_engaged():
    halt = AsyncMock()
    monitor = Monitor(SimpleNamespace(temperature_c=90, health=None))
    wd = make_watchdog(
        status=monitor.status, mode_manager=SimpleNamespace(force_safety_halt=halt)
    )
    assert (await wd._check_temperature())[0].severity is Severity.CRITICAL
    wd._gpu_monitor.status = SimpleNamespace(temperature_c=50, health=None)
    signals = await wd._check_temperature()
    assert signals[0].key == "temperature_clearable"
    assert halt.await_count == 1


@pytest.mark.asyncio
async def test_temperature_warn_and_hardware_health_signals():
    health = SimpleNamespace(
        thermal_slowdown=True, power_brake=True, device_lost=True, throttle_reasons=5
    )
    wd = make_watchdog(status=SimpleNamespace(temperature_c=75, health=health))
    signals = await wd._check_temperature()
    assert {s.key for s in signals} == {
        "temperature_warn:70",
        "thermal_slowdown",
        "power_brake",
        "device_lost",
    }
    assert signals[-1].action == "no_mode_manager"


@pytest.mark.asyncio
async def test_stuck_job_requests_cancel_then_escalates_after_grace():
    scheduler = SchedulerStub()
    scheduler.current_job = SimpleNamespace(id="job-1", adapter="audio", started_at=1)
    wd = make_watchdog(scheduler=scheduler)
    first = await wd._check_stuck_job()
    assert first[0].action == "cancel_requested"
    assert scheduler.cancel.await_count == 1
    wd._cancel_requested["job-1"] -= 1
    second = await wd._check_stuck_job()
    assert second[0].severity is Severity.CRITICAL
    scheduler.current_job = None
    assert await wd._check_stuck_job() == []
    assert wd._cancel_requested == {}


@pytest.mark.asyncio
async def test_service_failures_escalate_and_recovery_resets_count():
    probe = AsyncMock(side_effect=RuntimeError("offline"))
    adapter = SimpleNamespace(probe=probe)
    wd = make_watchdog(adapters={"ollama": adapter})
    assert (await wd._check_services())[0].severity is Severity.WARN
    assert (await wd._check_services())[0].severity is Severity.ERROR
    probe.side_effect = None
    assert await wd._check_services() == []
    assert wd._service_failures["ollama"] == 0


@pytest.mark.asyncio
async def test_reservation_lease_report_is_deduplicated_and_cleared():
    wd = make_watchdog(reservations=[{"job_id": "stale", "age_seconds": 12}])
    assert (await wd._check_reservations())[0].key == "lease_expiry:stale"
    assert await wd._check_reservations() == []
    wd._vram_manager.reservations.clear()
    await wd._check_reservations()
    wd._vram_manager.reservations.append({"job_id": "stale", "age_seconds": 12})
    assert len(await wd._check_reservations()) == 1


@pytest.mark.asyncio
async def test_signal_cooldown_notifies_only_errors_and_critical():
    notify = AsyncMock()
    wd = make_watchdog(notifications=SimpleNamespace(notify=notify))
    warn = HealthSignal("warn", Severity.WARN, "warn", "same")
    error = HealthSignal("error", Severity.ERROR, "error", "err")
    await wd._handle_signals([warn, warn, error])
    assert notify.await_count == 1


@pytest.mark.asyncio
async def test_run_once_isolates_check_exceptions_and_snapshot_tracks_state():
    wd = make_watchdog()

    async def fail_check():
        raise RuntimeError("probe bug")

    wd._check_services = fail_check
    signals = await wd.run_once()
    assert any(signal.key == "check_error:fail_check" for signal in signals)
    snapshot = await wd.snapshot()
    assert snapshot["run_count"] == 1
    assert snapshot["signals"]
    await wd.acknowledge("operator-known")
    assert "operator-known" in wd._signal_last_logged


def test_probe_resolution_prefers_public_then_private_fallbacks():
    def public():
        return None

    def private():
        return None

    assert _resolve_probe(SimpleNamespace(probe=public, _probe=private)) is public
    assert _resolve_probe(SimpleNamespace(_probe_stt=private)) is private
    assert _resolve_probe(None) is None
