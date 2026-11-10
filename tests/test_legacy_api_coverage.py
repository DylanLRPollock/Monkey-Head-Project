"""Directly exercise legacy API helpers and uncovered response paths."""

from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace

import pytest

# The API module still imports these two implementations through their legacy
# package paths. Keep the aliases local to this test so it can run by itself.
sys.modules.setdefault(
    "huey.os.core.resilience", importlib.import_module("huey.core.resilience")
)
sys.modules.setdefault(
    "huey.os.core.task_scheduler",
    importlib.import_module("huey.core.task_scheduler"),
)

api = importlib.import_module("huey.memory.PY.api")


def test_dashboard_renderer_escapes_values_formats_metrics_and_renders_empty_rows():
    accelerator = SimpleNamespace(
        name="<accelerator>",
        vendor=None,
        backend="CUDA",
        vram_total=2 * 1024**2,
        vram_free=None,
    )
    system = SimpleNamespace(
        hostname="huey-host",
        system="TestOS",
        release="1.0",
        python_version="3.13",
        memory_path="/memory",
        accelerators=[accelerator],
    )
    sensor = SimpleNamespace(name="<sensor>", timestamp=0, value="<unsafe>")
    interaction = SimpleNamespace(
        timestamp="invalid timestamp",
        model="<model>",
        backend="ollama",
        status="ok",
        prompt="prompt",
        response="response",
    )

    rendered = api._render_dashboard(
        system,
        {"percent": 50, "secs_left": None, "power_plugged": False},
        [sensor],
        [interaction],
        {"recommended_models": ["<recommended>"]},
    )

    assert "&lt;accelerator&gt;" in rendered
    assert "&lt;sensor&gt;" in rendered
    assert "&lt;unsafe&gt;" in rendered
    assert "&lt;recommended&gt;" in rendered
    assert "2.0 MiB" in rendered
    assert "&mdash;" in rendered
    assert "invalid timestamp" in rendered

    empty_system = SimpleNamespace(
        hostname="host",
        system="TestOS",
        release="1.0",
        python_version="3.13",
        memory_path="/memory",
        accelerators=[],
    )
    empty = api._render_dashboard(empty_system, {}, [], [], {"recommended_models": []})
    assert "No accelerators detected" in empty
    assert "No sensor telemetry recorded yet." in empty
    assert "No AI interactions logged." in empty
    assert "<script>" not in empty


@pytest.mark.asyncio
async def test_stream_text_yields_chunks_and_empty_stream():
    async def collect(stream):
        return [chunk async for chunk in stream]

    assert await collect(api._stream_text("abcdefgh", chunk_size=3)) == [
        "abc",
        "def",
        "gh",
    ]
    assert await collect(api._stream_text("", chunk_size=3)) == []


def test_service_and_monitor_status_helpers(monkeypatch):
    monkeypatch.setitem(api._SERVICE_STATES, "coverage-service", None)
    updated = api._update_service_status("coverage-service", "running")
    assert updated.name == "coverage-service"
    assert api._SERVICE_STATES["coverage-service"] is updated

    monkeypatch.setattr(
        api,
        "CRASH_MANAGER",
        SimpleNamespace(
            statuses=lambda: [
                {
                    "name": "worker",
                    "healthy": True,
                    "restart_attempts": 0,
                    "auto_restart": True,
                    "last_heartbeat": None,
                    "last_restart": None,
                    "manual_override_reason": None,
                }
            ]
        ),
    )
    assert api._monitor_status("worker").name == "worker"
    with pytest.raises(KeyError, match="Unknown monitored process"):
        api._monitor_status("missing")


def test_battery_hooks_log_events_and_schedule_once(monkeypatch):
    hooks = {}
    events = []
    scheduled = []

    class BatteryMonitor:
        def register_hook(self, name, callback):
            hooks[name] = callback

    class Scheduler:
        def __init__(self):
            self.active = []

        def list_tasks(self, statuses):
            assert statuses == [api.TaskStatus.PENDING, api.TaskStatus.RUNNING]
            return self.active

        def schedule_task(self, **kwargs):
            scheduled.append(kwargs)

    monkeypatch.setattr(api, "BATTERY_MONITOR", BatteryMonitor())
    monkeypatch.setattr(api, "SCHEDULER", Scheduler())
    monkeypatch.setattr(
        api.TELEMETRY_STORE,
        "log_event",
        lambda name, status: events.append((name, status)),
    )
    api._register_battery_hooks()

    low_status = {"percent": 5, "source": "battery"}
    hooks["battery_low"](low_status)
    hooks["battery_low"](low_status)
    assert len(scheduled) == 2
    assert all(item["command"] == "activate_power_saving" for item in scheduled)

    api.SCHEDULER.active = [SimpleNamespace(metadata={"power_event": "battery_low"})]
    hooks["battery_low"](low_status)
    assert len(scheduled) == 2

    hooks["battery_recovered"]({"percent": 50})
    hooks["power_connected"]({"source": "ac"})
    hooks["power_disconnected"]({"source": "battery"})
    assert [name for name, _status in events] == [
        "battery_low",
        "battery_low",
        "battery_low",
        "battery_recovered",
        "power_connected",
        "power_disconnected",
    ]


def test_sensor_helpers_cover_missing_and_error_paths(monkeypatch):
    request = api.SensorRegistrationRequest(
        plugin="virtual.random", name="sensor", config={}
    )
    monkeypatch.setattr(
        api,
        "SENSOR_MANAGER",
        SimpleNamespace(
            add_sensor=lambda *_a: None,
            get_sensor=lambda _name: None,
            remove_sensor=lambda _name: None,
            poll_sensor=lambda _name: None,
            poll_all=lambda: [],
            load_history=lambda *_a, **_k: [],
        ),
    )
    assert api.register_sensor(request).name == "sensor"

    def unknown(*_args):
        raise KeyError("missing plugin")

    monkeypatch.setattr(api.SENSOR_MANAGER, "add_sensor", unknown)
    with pytest.raises(api.HTTPException) as error:
        api.register_sensor(request)
    assert error.value.status_code == 404

    def invalid(*_args):
        raise ValueError("invalid configuration")

    monkeypatch.setattr(api.SENSOR_MANAGER, "add_sensor", invalid)
    with pytest.raises(api.HTTPException) as error:
        api.register_sensor(request)
    assert error.value.status_code == 400

    monkeypatch.setattr(api.SENSOR_MANAGER, "get_sensor", lambda _name: None)
    with pytest.raises(api.HTTPException) as error:
        api.remove_sensor("missing")
    assert error.value.status_code == 404

    reading = SimpleNamespace(name="sensor", value=4.0, timestamp=12.0, provenance={})
    monkeypatch.setattr(api.SENSOR_MANAGER, "poll_sensor", lambda _name: reading)
    monkeypatch.setattr(api.SENSOR_MANAGER, "get_sensor", lambda _name: object())
    assert api.poll_sensor("sensor").value == 4.0
    monkeypatch.setattr(api.SENSOR_MANAGER, "poll_sensor", unknown)
    with pytest.raises(api.HTTPException) as error:
        api.poll_sensor("missing")
    assert error.value.status_code == 404


def test_pdf_helpers_and_admin_system_check(monkeypatch, tmp_path):
    pdf = tmp_path / "guide.pdf"
    pdf.touch()
    monkeypatch.setattr(api, "list_available_pdfs", lambda **_kwargs: ["guide.pdf"])
    monkeypatch.setattr(api, "find_pdf", lambda _name, **_kwargs: pdf)
    assert api.list_pdfs().directory == str(tmp_path)
    assert api.locate_pdf("guide.pdf").found is True
    monkeypatch.setattr(api, "find_pdf", lambda *_a, **_kwargs: None)
    assert api.locate_pdf("missing.pdf").found is False

    monkeypatch.setattr(api, "require_admin_api_auth", lambda _request: None)
    monkeypatch.setattr(
        api, "system_check", lambda: {"database": True, "warning": "ok"}
    )
    response = api.admin_system_check(SimpleNamespace())
    assert response.passed is True
    assert response.results["database"] is True


def test_api_main_parses_flags_and_uses_environment(monkeypatch):
    calls = []
    uvicorn = SimpleNamespace(run=lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setitem(sys.modules, "uvicorn", uvicorn)
    monkeypatch.setenv("HUEY_HOST", "0.0.0.0")
    monkeypatch.setenv("HUEY_PORT", "2500")
    monkeypatch.setenv("HUEY_RELOAD", "true")

    api.main([])

    assert calls == [
        (
            ("huey.api:app",),
            {"host": "0.0.0.0", "port": 2500, "reload": True},
        )
    ]
