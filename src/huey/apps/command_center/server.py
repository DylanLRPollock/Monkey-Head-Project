"""Read-only FastAPI backend for the external Command Center frontend."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException
except ModuleNotFoundError:
    vendor_root = Path(__file__).resolve().parents[4] / "vendor"
    if str(vendor_root) not in sys.path:
        sys.path.insert(0, str(vendor_root))
    from fastapi import FastAPI, HTTPException

from huey.apps.command_center.static_config import export_frontend_config
from huey.gui.defaults import default_migration_phases, default_operator_panel_state
from huey.gui.models import dataclass_list_to_dicts, dataclass_to_dict
from huey.gui.prompts import generate_next_best_task_prompt, generate_phase_prompt
from huey.gui.safety import safety_banner
from huey.gui.v1_runs import sample_v1_runs
from huey.gui.validation import all_validation_commands
from huey.integrations.command_center.adapter import (
    get_api_status,
    get_memory_status,
    get_repo_status,
    get_runtime_status,
    get_v1_status,
)

APP_VERSION = "0.3.0"


def get_app_metadata() -> dict[str, object]:
    """Return metadata about the local Command Center backend."""

    return {
        "name": "HueyOS Command Center Backend",
        "version": APP_VERSION,
        "mode": "read-only",
        "safety_mode": "mock-only",
        "config": export_frontend_config(),
    }


def get_repositories() -> list[dict[str, object]]:
    """Return repository status cards."""

    return get_repo_status()


def get_migration_phases() -> list[dict[str, object]]:
    """Return migration phase data."""

    return dataclass_list_to_dicts(default_migration_phases())


def get_validation_commands() -> list[dict[str, object]]:
    """Return copy-only validation commands."""

    return dataclass_list_to_dicts(all_validation_commands())


def get_operator_panel_state() -> dict[str, object]:
    """Return the safe operator-panel state."""

    panel = default_operator_panel_state()
    runtime_status = get_runtime_status()
    api_status = get_api_status()
    services = runtime_status.get("services", {})
    ffmpeg_service = services.get("ffmpeg", {})
    pyhuey_service = services.get("pyhuey", {})
    panel.health_status = "ok" if api_status.get("ready") else "degraded"
    panel.runtime_status = "active" if runtime_status.get("started") else "standby"
    panel.ffmpeg_status = str(ffmpeg_service.get("status", panel.ffmpeg_status))
    panel.connector_status = str(pyhuey_service.get("status", panel.connector_status))
    panel.v1_status = "fixture-ready" if sample_v1_runs() else "mock"
    return dataclass_to_dict(panel)


def get_v1_sample_runs() -> list[dict[str, object]]:
    """Return sample V1 run records."""

    return dataclass_list_to_dicts(sample_v1_runs())


def get_safety_policy() -> dict[str, object]:
    """Return the safety policy banner."""

    return safety_banner()


def get_state_payload() -> dict[str, object]:
    """Return a consolidated Command Center state payload."""

    return {
        "meta": get_app_metadata(),
        "safety": get_safety_policy(),
        "repos": get_repositories(),
        "phases": get_migration_phases(),
        "validation": get_validation_commands(),
        "operator_panel": get_operator_panel_state(),
        "runtime": get_runtime_status(),
        "memory": get_memory_status(),
        "api": get_api_status(),
        "v1": get_v1_status(),
        "next_prompt": generate_next_best_task_prompt(default_migration_phases()),
    }


def register_routes(app: FastAPI) -> None:
    """Attach all Command Center routes."""

    @app.get("/command-center/meta")
    def command_center_meta() -> dict[str, object]:
        return get_app_metadata()

    @app.get("/command-center/safety")
    def command_center_safety() -> dict[str, object]:
        return get_safety_policy()

    @app.get("/command-center/repos")
    def command_center_repos() -> list[dict[str, object]]:
        return get_repositories()

    @app.get("/command-center/phases")
    def command_center_phases() -> list[dict[str, object]]:
        return get_migration_phases()

    @app.get("/command-center/validation")
    def command_center_validation() -> list[dict[str, object]]:
        return get_validation_commands()

    @app.get("/command-center/operator-panel")
    def command_center_operator_panel() -> dict[str, object]:
        return get_operator_panel_state()

    @app.get("/command-center/v1-runs/sample")
    def command_center_v1_runs() -> list[dict[str, object]]:
        return get_v1_sample_runs()

    @app.get("/command-center/runtime")
    def command_center_runtime() -> dict[str, object]:
        return get_runtime_status()

    @app.get("/command-center/memory")
    def command_center_memory() -> dict[str, object]:
        return get_memory_status()

    @app.get("/command-center/api-status")
    def command_center_api_status() -> dict[str, object]:
        return get_api_status()

    @app.get("/command-center/state")
    def command_center_state() -> dict[str, object]:
        return get_state_payload()

    @app.get("/command-center/prompts/phase/{phase_id}")
    def command_center_phase_prompt(phase_id: str) -> dict[str, str]:
        for phase in default_migration_phases():
            if phase.id == phase_id:
                return {"phase_id": phase_id, "prompt": generate_phase_prompt(phase)}
        raise HTTPException(status_code=404, detail=f"Unknown phase id: {phase_id}")


def create_app() -> FastAPI:
    """Create the read-only Command Center backend application."""

    app = FastAPI(
        title="HueyOS Command Center Backend",
        version=APP_VERSION,
        description=(
            "Read-only local backend that unifies HueyOS runtime, memory, V1, "
            "validation, and repository status for the separate Command Center UI."
        ),
    )
    register_routes(app)
    return app


app = create_app()


__all__ = [
    "app",
    "create_app",
    "get_app_metadata",
    "get_migration_phases",
    "get_operator_panel_state",
    "get_repositories",
    "get_safety_policy",
    "get_state_payload",
    "get_v1_sample_runs",
    "get_validation_commands",
    "register_routes",
]
