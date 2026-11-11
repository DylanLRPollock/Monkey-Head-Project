"""Exercise API handlers for sensor, resilience, AI, memory, and admin paths."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from tests.test_api_routes import api_module as api


def _request() -> SimpleNamespace:
    return SimpleNamespace()


def test_sensor_inventory_polling_and_history(monkeypatch):
    reading = SimpleNamespace(
        name="temperature", value=21.5, timestamp=123.0, provenance={"source": "mock"}
    )
    manager = SimpleNamespace(
        registry={"virtual.random": object()},
        list_sensors=lambda: [
            {
                "name": "temperature",
                "plugin": "virtual.random",
                "module": "virtual",
                "config": {"unit": "C"},
            }
        ],
        get_sensor=lambda name: object() if name == "temperature" else None,
        remove_sensor=lambda name: removed.append(name),
        poll_all=lambda: [reading],
        load_history=lambda name, limit: [
            {"name": name, "value": 21.5, "timestamp": 123.0, "provenance": {}}
        ],
    )
    removed = []
    monkeypatch.setattr(api, "SENSOR_MANAGER", manager)
    monkeypatch.setattr(
        api, "list_sensor_plugins", lambda _registry: ["virtual.random"]
    )
    monkeypatch.setattr(
        api, "list_sensor_plugin_metadata", lambda _registry: [{"id": "virtual.random"}]
    )

    assert api.sensor_plugins().plugins == ["virtual.random"]
    assert api.list_sensors().sensors[0].config == {"unit": "C"}
    assert api.remove_sensor("temperature") == {
        "status": "removed",
        "sensor": "temperature",
    }
    assert removed == ["temperature"]
    assert api.poll_all_sensors().readings[0].value == 21.5
    assert api.sensor_history("temperature", limit=3).readings[0].timestamp == 123.0
    with pytest.raises(api.HTTPException) as error:
        api.sensor_history("missing")
    assert error.value.status_code == 404


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore:The `json` method is deprecated:DeprecationWarning")
async def test_sensor_sse_stream_emits_reading_and_unsubscribes(monkeypatch):
    class Queue:
        def __init__(self):
            self.calls = 0

        async def get(self):
            self.calls += 1
            if self.calls == 1:
                return SimpleNamespace(
                    name="temperature", value=20, timestamp=1.0, provenance={}
                )
            raise RuntimeError("stop stream")

    queue = Queue()
    unsubscribed = []
    monkeypatch.setattr(
        api,
        "SENSOR_MANAGER",
        SimpleNamespace(
            subscribe=lambda name: queue,
            unsubscribe=lambda value: unsubscribed.append(value),
            get_sensor=lambda name: object() if name == "temperature" else None,
        ),
    )
    stream = api._sensor_stream("temperature")
    assert "temperature" in await anext(stream)
    with pytest.raises(RuntimeError, match="stop stream"):
        await anext(stream)
    assert unsubscribed == [queue]
    with pytest.raises(api.HTTPException) as error:
        await api.stream_sensor("missing")
    assert error.value.status_code == 404


def test_sensor_and_ai_telemetry_are_redacted(monkeypatch):
    sensor = SimpleNamespace(name="temperature", timestamp=4.0, value=22, provenance={})
    interaction = SimpleNamespace(
        timestamp=5.0,
        prompt="private prompt",
        response="private response",
        model="local",
        backend="ollama",
        instruction="private instruction",
        metadata={"secret": "value"},
        status="ok",
    )
    monkeypatch.setattr(
        api,
        "TELEMETRY_STORE",
        SimpleNamespace(
            fetch_recent_sensor_readings=lambda **kwargs: [sensor],
            fetch_recent_ai_results=lambda **kwargs: [interaction],
        ),
    )
    assert (
        api.list_recent_sensor_telemetry(limit=1, name="temperature").records[0].value
        == 22
    )
    record = api.list_recent_ai_interactions(limit=1).records[0]
    assert record.prompt == "[redacted]"
    assert record.response == "[redacted]"
    assert record.instruction is None
    assert record.metadata == {}


def test_ai_handlers_cover_models_validation_and_analysis(monkeypatch):
    processor = SimpleNamespace(
        get_model_catalog=lambda refresh=False: {
            "backend": "ollama",
            "active_model": "small-local",
            "recommended_models": ["small-local"],
            "accelerators": [],
            "total_vram": 10,
        },
        compute_mean=lambda numbers: sum(numbers) / len(numbers),
        analyze_data=lambda text: {"characters": len(text)},
        process_data=lambda text: text.upper(),
    )
    monkeypatch.setattr(api, "AI_PROCESSOR", processor)
    assert api._collect_accelerator_models(refresh=True) == []
    assert api.list_ai_models().active_model == "small-local"
    assert api.ai_compute_mean(api.ComputeMeanRequest(numbers=[2, 4])).mean == 3
    with pytest.raises(api.HTTPException) as error:
        api.ai_compute_mean(api.ComputeMeanRequest(numbers=[]))
    assert error.value.status_code == 400
    assert api.ai_analyze_text(api.AnalyzeTextRequest(text="hello")).metrics == {
        "characters": 5
    }
    with pytest.raises(api.HTTPException) as error:
        api.ai_analyze_text(api.AnalyzeTextRequest(text="  "))
    assert error.value.status_code == 400
    assert (
        asyncio.run(
            api.ai_process_text(api.ProcessTextRequest(text="hello"), stream=False)
        ).processed_text
        == "HELLO"
    )


def test_memory_sort_and_admin_service_handlers(monkeypatch):
    monkeypatch.setattr(api, "require_admin_api_auth", lambda _request: None)
    monkeypatch.setattr(
        api,
        "auto_sort_memory",
        lambda **kwargs: {
            "source": kwargs["source_dir"] or "/raw",
            "destination": kwargs["destination_root"] or "/sorted",
            "moved": ["a.txt"],
            "skipped": [],
        },
    )
    result = api.auto_sort(api.AutoSortRequest(dry_run=True), _request())
    assert result.moved == ["a.txt"]
    monkeypatch.setattr(
        api,
        "auto_sort_memory",
        lambda **_kwargs: (_ for _ in ()).throw(FileNotFoundError("missing source")),
    )
    with pytest.raises(api.HTTPException) as error:
        api.auto_sort(api.AutoSortRequest(), _request())
    assert error.value.status_code == 404

    monkeypatch.setattr(api, "_SERVICE_STATES", {})
    assert api.start_service("worker", _request()).status == "running"
    assert api.list_services().services[0].name == "worker"
    assert api.stop_service("worker", _request()).status == "stopped"
    monkeypatch.setattr(api, "system_check", lambda: {"ok": True, "warning": False})
    assert api.admin_system_check(_request()).passed is False
    assert api.admin_health_check() == api.healthz()


def test_resilience_admin_handlers_translate_missing_process(monkeypatch):
    monkeypatch.setattr(api, "require_admin_api_auth", lambda _request: None)
    manager = SimpleNamespace(
        statuses=lambda: [],
        toggle_auto_restart=lambda *args, **kwargs: (_ for _ in ()).throw(
            KeyError("unknown process")
        ),
        manual_restart=lambda name: (_ for _ in ()).throw(KeyError("unknown process")),
        ping_watchdog=lambda: True,
    )
    monkeypatch.setattr(api, "CRASH_MANAGER", manager)
    assert api.list_monitored_processes() == []
    with pytest.raises(api.HTTPException) as error:
        api.override_monitored_process(
            "missing", api.ManualOverrideRequest(auto_restart=False), _request()
        )
    assert error.value.status_code == 404
    with pytest.raises(api.HTTPException) as error:
        api.manual_restart_monitored_process("missing", _request())
    assert error.value.status_code == 404
    assert api.watchdog_ping() == {"watchdog": True}
