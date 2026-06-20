"""Workspace storage helpers for GUI-facing Python surfaces."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from huey.gui.defaults import (
    default_migration_phases,
    default_operator_panel_state,
    default_repositories,
    default_validation_commands,
)
from huey.gui.models import dataclass_list_to_dicts, dataclass_to_dict
from huey.utils.paths import ensure_subdirectory


@dataclass
class WorkspaceData:
    repositories: list[dict[str, object]]
    phases: list[dict[str, object]]
    validation_commands: list[dict[str, object]]
    operator_panel: dict[str, object]
    notes: str = ""
    version: str = "0.1.0"


def _default_workspace_data() -> WorkspaceData:
    return WorkspaceData(
        repositories=dataclass_list_to_dicts(default_repositories()),
        phases=dataclass_list_to_dicts(default_migration_phases()),
        validation_commands=dataclass_list_to_dicts(default_validation_commands()),
        operator_panel=dataclass_to_dict(default_operator_panel_state()),
    )


def default_workspace_path() -> Path:
    """Return the default local workspace JSON path."""

    return ensure_subdirectory("GUI") / "command-center-workspace.json"


def load_workspace(path: Path | None = None) -> WorkspaceData:
    """Load workspace JSON or return defaults."""

    selected = path or default_workspace_path()
    if not selected.exists():
        return _default_workspace_data()
    return import_workspace(selected.read_text(encoding="utf-8"))


def save_workspace(data: WorkspaceData, path: Path | None = None) -> Path:
    """Save workspace JSON."""

    selected = path or default_workspace_path()
    selected.parent.mkdir(parents=True, exist_ok=True)
    selected.write_text(export_workspace(data), encoding="utf-8")
    return selected


def export_workspace(data: WorkspaceData) -> str:
    """Return a pretty JSON string."""

    payload = {
        "repositories": data.repositories,
        "phases": data.phases,
        "validation_commands": data.validation_commands,
        "operator_panel": data.operator_panel,
        "notes": data.notes,
        "version": data.version,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def import_workspace(text: str) -> WorkspaceData:
    """Parse workspace JSON text."""

    payload = json.loads(text)
    defaults = _default_workspace_data()
    return WorkspaceData(
        repositories=list(payload.get("repositories", defaults.repositories)),
        phases=list(payload.get("phases", defaults.phases)),
        validation_commands=list(
            payload.get("validation_commands", defaults.validation_commands)
        ),
        operator_panel=dict(payload.get("operator_panel", defaults.operator_panel)),
        notes=str(payload.get("notes", "")),
        version=str(payload.get("version", defaults.version)),
    )


def reset_workspace(path: Path | None = None) -> WorkspaceData:
    """Overwrite workspace with default data."""

    defaults = _default_workspace_data()
    save_workspace(defaults, path=path)
    return defaults


__all__ = [
    "WorkspaceData",
    "default_workspace_path",
    "export_workspace",
    "import_workspace",
    "load_workspace",
    "reset_workspace",
    "save_workspace",
]
