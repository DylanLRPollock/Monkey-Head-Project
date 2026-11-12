"""Failure and recovery behavior for the Banana Brain watchdog."""

import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from huey.banana_brain.watchdog import (
    HealthSignal,
    Severity,
    Watchdog,
    _cfg_get,
    _resolve_probe,
)


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


@pytest.mark.asyncio
async def test_lifecycle_rejects_duplicate_start_and_stop_is_idempotent():
    wd = make_watchdog(config={"watchdog_check_interval_seconds": 60})
    await wd.stop()
    await wd.start()
    with pytest.raises(RuntimeError, match="already started"):
        await wd.start()
    assert (await wd.snapshot())["running"] is True
    await wd.stop()
    await wd.stop()
    assert (await wd.snapshot())["running"] is False


@pytest.mark.asyncio
async def test_loop_continues_after_iteration_error_and_stops_on_event(monkeypatch):
    wd = make_watchdog(config={"watchdog_check_interval_seconds": 0.01})
    attempts = 0

    async def run_once():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("transient iteration failure")
        wd._stop_event.set()
        return []

    wd.run_once = run_once
    await wd._loop()
    assert attempts == 2


@pytest.mark.asyncio
async def test_loop_propagates_cancellation():
    wd = make_watchdog()
    task = asyncio.create_task(wd._loop())
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    async def cancelled_iteration():
        raise asyncio.CancelledError

    wd.run_once = cancelled_iteration
    with pytest.raises(asyncio.CancelledError):
        await wd._loop()


@pytest.mark.asyncio
async def test_run_once_propagates_cancelled_check():
    wd = make_watchdog()

    async def cancelled():
        raise asyncio.CancelledError

    wd._check_gpu_visibility = cancelled
    with pytest.raises(asyncio.CancelledError):
        await wd.run_once()


@pytest.mark.asyncio
async def test_temperature_absent_status_and_missing_temperature_are_safe():
    wd = make_watchdog(status=None)
    assert await wd._check_temperature() == []


@pytest.mark.asyncio
async def test_gpu_visibility_waits_for_warn_threshold_before_reporting():
    wd = make_watchdog(
        status=None,
        config={
            "watchdog_gpu_unavailable_warn_s": 30,
            "watchdog_gpu_unavailable_critical_s": 60,
        },
    )
    assert await wd._check_gpu_visibility() == []
    wd._gpu_monitor.status = SimpleNamespace(temperature_c=None, health=None)
    assert await wd._check_temperature() == []


@pytest.mark.asyncio
async def test_temperature_warning_clears_and_invalid_threshold_is_reported(caplog):
    wd = make_watchdog(
        status=SimpleNamespace(temperature_c=75, health=None),
        config={
            "watchdog_temperature_warn_c": 90,
            "watchdog_temperature_ceiling_c": 80,
        },
    )
    assert "warn-level temperature alerts will not fire" in caplog.text
    wd._temperature_warn_active = True
    wd._gpu_monitor.status = SimpleNamespace(temperature_c=40, health=None)
    assert await wd._check_temperature() == []
    assert wd._temperature_warn_active is False
    assert wd._temperature_cleared_at is not None


@pytest.mark.asyncio
async def test_stuck_job_without_start_time_and_cancel_failure():
    scheduler = SchedulerStub()
    scheduler.current_job = SimpleNamespace(id="not-started", started_at=None)
    wd = make_watchdog(scheduler=scheduler)
    assert await wd._check_stuck_job() == []

    scheduler.current_job = SimpleNamespace(id="stuck", started_at=0)
    scheduler.cancel.return_value = False
    signal = (await wd._check_stuck_job())[0]
    assert signal.action == "cancel_request_failed"
    assert "stuck" not in wd._cancel_requested

    scheduler.cancel.side_effect = RuntimeError("scheduler unavailable")
    assert (await wd._check_stuck_job())[0].action == "cancel_request_failed"


@pytest.mark.asyncio
async def test_stuck_job_age_and_cancel_grace_boundaries():
    scheduler = SchedulerStub()
    scheduler.current_job = SimpleNamespace(id="young", started_at=time.time())
    wd = make_watchdog(
        scheduler=scheduler,
        config={
            "watchdog_stuck_job_seconds": 100,
            "watchdog_cancel_grace_seconds": 100,
        },
    )
    assert await wd._check_stuck_job() == []

    wd._stuck_job_s = 0
    wd._cancel_requested["young"] = time.monotonic()
    assert await wd._check_stuck_job() == []


def test_config_object_and_ok_signal_logging(caplog):
    wd = make_watchdog(config={"watchdog_signal_cooldown_seconds": 2})
    assert wd._signal_cooldown_s == 2
    assert _cfg_get(SimpleNamespace(value=1), "value") == 1
    with caplog.at_level("DEBUG", logger="banana_brain.watchdog"):
        wd._log_signal(HealthSignal("check", Severity.OK, "healthy", "ok"))
    assert "healthy" in caplog.text


@pytest.mark.asyncio
async def test_initially_available_gpu_does_not_log_recovery(caplog):
    wd = make_watchdog(status=SimpleNamespace(temperature_c=40))
    assert await wd._check_gpu_visibility() == []
    assert "visibility restored" not in caplog.text


@pytest.mark.asyncio
async def test_service_probe_fallbacks_skip_missing_and_preserve_cancellation():
    cancelled = AsyncMock(side_effect=asyncio.CancelledError)
    wd = make_watchdog(
        adapters={
            "empty": object(),
            "private": SimpleNamespace(_probe=AsyncMock()),
            "cancel": SimpleNamespace(probe=cancelled),
        }
    )
    with pytest.raises(asyncio.CancelledError):
        await wd._check_services()
    wd._adapters.pop("cancel")
    assert await wd._check_services() == []
    assert wd._service_failures["private"] == 0


@pytest.mark.asyncio
async def test_reservation_snapshot_errors_and_legitimate_reservations(caplog):
    wd = make_watchdog(reservations=[])

    async def failed_snapshot():
        raise RuntimeError("store unavailable")

    wd._vram_manager.snapshot = failed_snapshot
    assert await wd._check_reservations() == []
    assert "snapshot() raised" in caplog.text

    wd._vram_manager.snapshot = AsyncMock(
        return_value={
            "reservations": [
                {"job_id": "", "age_seconds": 99},
                {"job_id": "young", "age_seconds": 1},
                {"job_id": "running", "age_seconds": 99},
            ]
        }
    )
    wd._scheduler.current_job = SimpleNamespace(id="running")
    assert await wd._check_reservations() == []


@pytest.mark.asyncio
async def test_notification_absence_invalid_method_and_failure_are_safe(caplog):
    signal = HealthSignal("error", Severity.ERROR, "failed", "e")
    wd = make_watchdog()
    await wd._notify(signal)
    wd._notifications = SimpleNamespace(notify=None)
    await wd._notify(signal)

    notify = AsyncMock(side_effect=RuntimeError("notification backend down"))
    wd._notifications = SimpleNamespace(notify=notify)
    await wd._notify(signal)
    assert "notification failed" in caplog.text


@pytest.mark.asyncio
async def test_safety_halt_unavailable_and_failed_modes_are_reported(caplog):
    wd = make_watchdog()
    assert await wd._trigger_safety_halt("x", reason="test") == "no_mode_manager"

    wd._mode_manager = SimpleNamespace(force_safety_halt=False)
    assert (
        await wd._trigger_safety_halt("y", reason="test") == "mode_manager_api_missing"
    )

    wd._mode_manager.force_safety_halt = AsyncMock(
        side_effect=RuntimeError("halt failed")
    )
    assert await wd._trigger_safety_halt("z", reason="test") == "halt_failed"
    assert "force_safety_halt raised" in caplog.text
    assert "z" not in wd._halt_triggered_for


@pytest.mark.asyncio
async def test_signal_cooldown_expires_and_notification_errors_do_not_escape():
    notify = AsyncMock(side_effect=RuntimeError("offline"))
    wd = make_watchdog(
        notifications=SimpleNamespace(notify=notify),
        config={"watchdog_signal_cooldown_seconds": 0},
    )
    signal = HealthSignal("warning", Severity.WARN, "watch", "same")
    error = HealthSignal("error", Severity.ERROR, "failed", "err")
    await wd._handle_signals([signal, signal, error])
    assert notify.await_count == 1
    await wd._handle_signals([signal])
    assert wd._signal_last_logged["same"]
