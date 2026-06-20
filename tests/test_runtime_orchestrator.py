"""Tests for the runtime orchestrator."""

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
