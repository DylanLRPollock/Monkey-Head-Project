"""Read-only adapters that prepare HueyOS state for Command Center."""

from __future__ import annotations

import os

from huey.gui.defaults import default_migration_phases, default_repositories
from huey.gui.github_client import client_from_env, summarize_repo_status
from huey.gui.models import dataclass_list_to_dicts, dataclass_to_dict
from huey.gui.v1_runs import sample_v1_runs
from huey.integrations.command_center.launcher import get_launcher_support
from huey.integrations.command_center.serializers import memory_to_json, state_to_json
from huey.memory.pipeline.indexing import default_index_path
from huey.runtime.orchestrator import RuntimeOrchestrator
from huey.utils.paths import get_memory_path
from huey.v1.fixture_registry import list_fixtures


def get_repo_status(*, live: bool | None = None) -> list[dict[str, object]]:
    """Return repository status cards from mock or live sources."""

    use_live = live
    if use_live is None:
        use_live = os.environ.get("HUEY_COMMAND_CENTER_LIVE_REPOS", "").lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
    if not use_live:
        return dataclass_list_to_dicts(default_repositories())

    client = client_from_env()
    statuses = []
    for repo in default_repositories():
        try:
            statuses.append(
                dataclass_to_dict(summarize_repo_status(client, repo.full_name))
            )
        except Exception as exc:
            fallback = dataclass_to_dict(repo)
            fallback["data_mode"] = "mock"
            fallback["live_error"] = str(exc)
            statuses.append(fallback)
    return statuses


def get_runtime_status() -> dict[str, object]:
    """Return orchestrator-driven runtime status."""

    orchestrator = RuntimeOrchestrator()
    orchestrator.health_check()
    return state_to_json(orchestrator.status())


def get_v1_status() -> dict[str, object]:
    """Return V1 proof-loop status and sample data."""

    fixtures = list_fixtures()
    runs = sample_v1_runs()
    return {
        "fixtures_registered": len(fixtures),
        "fixtures": fixtures,
        "sample_runs": dataclass_list_to_dicts(runs),
        "phases": dataclass_list_to_dicts(default_migration_phases()),
    }


def get_memory_status() -> dict[str, object]:
    """Return memory root and index status."""

    memory_root = get_memory_path(create=True)
    index_path = default_index_path()
    indexed_entries = 0
    if index_path.exists():
        indexed_entries = len(
            __import__("json").loads(index_path.read_text(encoding="utf-8"))
        )
    payload = {
        "root_path": str(memory_root),
        "exists": memory_root.exists(),
        "index_path": str(index_path),
        "indexed_entries": indexed_entries,
        "subdirectories": sorted(
            entry.name for entry in memory_root.iterdir() if entry.is_dir()
        ),
    }
    return memory_to_json(payload)


def get_api_status() -> dict[str, object]:
    """Return local API health information."""

    from huey.os.api.routers.system import healthz

    payload = dict(healthz())
    payload["ready"] = payload.get("status") == "ok"
    return payload


__all__ = [
    "get_api_status",
    "get_launcher_support",
    "get_memory_status",
    "get_repo_status",
    "get_runtime_status",
    "get_v1_status",
]
