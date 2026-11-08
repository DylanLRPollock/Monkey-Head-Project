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
    get_launcher_support,
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
        "launcher": get_launcher_support(),
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


def _phase_prompt(phase_id: str) -> dict[str, str]:
    for phase in default_migration_phases():
        if phase.id == phase_id:
            return {"phase_id": phase_id, "prompt": generate_phase_prompt(phase)}
    raise HTTPException(status_code=404, detail=f"Unknown phase id: {phase_id}")


def register_routes(app: FastAPI) -> None:
    """Attach all read-only Command Center routes."""

    routes = (
        ("/command-center/meta", get_app_metadata),
        ("/command-center/launcher", get_launcher_support),
        ("/command-center/safety", get_safety_policy),
        ("/command-center/repos", get_repositories),
        ("/command-center/phases", get_migration_phases),
        ("/command-center/validation", get_validation_commands),
        ("/command-center/operator-panel", get_operator_panel_state),
        ("/command-center/v1-runs/sample", get_v1_sample_runs),
        ("/command-center/runtime", get_runtime_status),
        ("/command-center/memory", get_memory_status),
        ("/command-center/api-status", get_api_status),
        ("/command-center/state", get_state_payload),
        ("/command-center/prompts/phase/{phase_id}", _phase_prompt),
    )
    for path, endpoint in routes:
        app.add_api_route(path, endpoint, methods=["GET"])


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
    "get_launcher_support",
    "get_migration_phases",
    "get_operator_panel_state",
    "get_repositories",
    "get_safety_policy",
    "get_state_payload",
    "get_v1_sample_runs",
    "get_validation_commands",
    "register_routes",
]
