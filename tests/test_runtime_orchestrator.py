"""Tests for the runtime orchestrator."""

import pytest

from huey.runtime.orchestrator import RuntimeOrchestrator


def test_orchestrator_registers_default_services():
    orchestrator = RuntimeOrchestrator()
    status = orchestrator.status()

    assert "ffmpeg" in status["services"]
    assert "command_center" in status["services"]
    assert "transcription" in status["dependencies"]
    assert "ffmpeg" in status["dependencies"]["transcription"]


def test_orchestrator_health_check_updates_service_status():
    orchestrator = RuntimeOrchestrator(bootstrap_defaults=False)
    orchestrator.register_service(
        "memory",
        "Memory subsystem",
        healthcheck=lambda: {"ready": True, "path": "memory"},
    )

    results = orchestrator.health_check()

    assert results["memory"]["ready"] is True
    assert orchestrator.registry.get("memory").status == "ready"


def test_orchestrator_registers_pipeline_and_model_with_copied_metadata():
    orchestrator = RuntimeOrchestrator(bootstrap_defaults=False)
    steps = ["load", "infer"]
    pipeline_metadata = {"owner": "test"}
    model_metadata = {"quantized": True}

    pipeline = orchestrator.register_pipeline(
        "chat",
        description="Run a chat response",
        steps=steps,
        metadata=pipeline_metadata,
    )
    model = orchestrator.register_model(
        "local-model", provider="ollama", metadata=model_metadata
    )

    steps.append("unexpected")
    pipeline_metadata["owner"] = "caller"
    model_metadata["quantized"] = False

    assert pipeline == {
        "name": "chat",
        "description": "Run a chat response",
        "steps": ["load", "infer"],
        "metadata": {"owner": "test"},
    }
    assert model == {
        "name": "local-model",
        "provider": "ollama",
        "metadata": {"quantized": True},
    }
    assert orchestrator.status()["pipelines"]["chat"] == pipeline
    assert orchestrator.status()["models"]["local-model"] == model


def test_orchestrator_start_stop_and_restart_preserve_blocked_services():
    orchestrator = RuntimeOrchestrator(bootstrap_defaults=False)
    orchestrator.register_service("base", "Base service", status="stopped")
    orchestrator.register_service(
        "dependent", "Dependent service", dependencies=("base",)
    )
    orchestrator.register_service("blocked", "Blocked service", status="blocked")

    started = orchestrator.start()

    assert started == {
        "started": True,
        "startup_order": ["base", "blocked", "dependent"],
    }
    assert orchestrator.registry.get("base").status == "ready"
    assert orchestrator.registry.get("dependent").status == "ready"
    assert orchestrator.registry.get("blocked").status == "blocked"

    stopped = orchestrator.stop()
    assert stopped == {"started": False}
    assert orchestrator.status()["started"] is False
    assert orchestrator.registry.get("base").status == "stopped"
    assert orchestrator.registry.get("dependent").status == "stopped"
    assert orchestrator.registry.get("blocked").status == "blocked"

    restarted = orchestrator.restart()
    assert restarted["started"] is True
    assert orchestrator.status()["started"] is True
    assert orchestrator.registry.get("base").status == "ready"
    assert orchestrator.registry.get("blocked").status == "blocked"


@pytest.mark.parametrize(
    ("healthcheck", "expected"),
    [
        (None, {"ready": False}),
        (lambda: True, {"ready": True}),
        (lambda: False, {"ready": False}),
        (lambda: "ok", {"ready": True, "status": "ok"}),
        (lambda: "", {"ready": False, "status": ""}),
        (lambda: {"status": "ok"}, {"status": "ok", "ready": True}),
        (lambda: {"status": "degraded"}, {"status": "degraded", "ready": False}),
    ],
)
def test_orchestrator_normalizes_health_payloads(healthcheck, expected):
    if healthcheck is None:
        actual = RuntimeOrchestrator._normalise_health_payload(None)
    else:
        actual = RuntimeOrchestrator._normalise_health_payload(healthcheck())

    assert actual == expected


@pytest.mark.parametrize("error_type", [ImportError, OSError, RuntimeError, ValueError])
def test_orchestrator_healthcheck_converts_expected_errors_to_blocked(
    error_type,
):
    orchestrator = RuntimeOrchestrator(bootstrap_defaults=False)
    orchestrator.register_service(
        "fragile",
        "Service with a failing health check",
        healthcheck=lambda: _raise(error_type("dependency unavailable")),
    )

    result = orchestrator.health_check()["fragile"]

    assert result == {"ready": False, "error": "dependency unavailable"}
    assert orchestrator.registry.get("fragile").status == "blocked"
    assert orchestrator.registry.get("fragile").metadata["error"] == (
        "dependency unavailable"
    )


def _raise(error):
    raise error
