"""Default mock and local data for GUI-oriented surfaces."""

from __future__ import annotations

from huey.gui.models import (
    MigrationPhase,
    OperatorPanelState,
    RepoStatus,
    ValidationCommand,
)


def default_repositories() -> list[RepoStatus]:
    """Return default Monkey-Head-Project umbrella repo cards."""

    return [
        RepoStatus(
            name="Monkey-Head-Project",
            full_name="DylanLRPollock/Monkey-Head-Project",
            role="runtime",
            description="Canonical HueyOS runtime, memory, API, and tooling repository.",
            url="https://github.com/DylanLRPollock/Monkey-Head-Project",
            data_mode="mock",
        ),
        RepoStatus(
            name="PyHuey",
            full_name="DylanLRPollock/PyHuey",
            role="cockpit",
            description="Cockpit-side UI and future operator surface integration repo.",
            url="https://github.com/DylanLRPollock/PyHuey",
            data_mode="mock",
        ),
        RepoStatus(
            name="command-center",
            full_name="DylanLRPollock/command-center",
            role="dashboard",
            description="Separate frontend repo for the read-only Command Center operator UI.",
            url="https://github.com/DylanLRPollock/command-center",
            data_mode="mock",
        ),
        RepoStatus(
            name="dlrp.ca",
            full_name="DylanLRPollock/dlrp.ca",
            role="website",
            description="Website and outward-facing documentation surface for the project.",
            url="https://github.com/DylanLRPollock/dlrp.ca",
            data_mode="mock",
        ),
    ]


def default_migration_phases() -> list[MigrationPhase]:
    """Return canonical current migration phases."""

    return [
        MigrationPhase(
            id="phase-1-layout",
            title="Lock repository layout and package boundaries",
            target_repo="DylanLRPollock/Monkey-Head-Project",
            status="merged",
            risk="low",
            notes="Compatibility shims are in place and the canonical src layout is active.",
            checklist=[
                "Preserve the existing memory tree.",
                "Keep legacy import bridges operational.",
            ],
        ),
        MigrationPhase(
            id="phase-2-huey-os-canonical",
            title="Consolidate canonical HueyOS Python surfaces",
            target_repo="DylanLRPollock/Monkey-Head-Project",
            status="in_progress",
            risk="high",
            owner="Copilot",
            checklist=[
                "Unify GUI theme, state, and validation metadata.",
                "Add runtime orchestration and FFmpeg media helpers.",
                "Expose safe integration adapters for Command Center.",
            ],
            validation_commands=[
                "python scripts/repo/check_dependency_sync.py",
                "python scripts/check_command_center_contract.py",
                "python -m pytest -q tests/test_command_center_backend.py",
            ],
        ),
        MigrationPhase(
            id="phase-2-5-pyhuey-connector",
            title="Reconcile PyHuey connector integration",
            target_repo="DylanLRPollock/Monkey-Head-Project",
            status="in_progress",
            risk="medium",
            checklist=[
                "Detect local/vendored PyHuey sources.",
                "Expose adapter status and event forwarding hooks.",
                "Keep the cockpit surface opt-in and local-only.",
            ],
        ),
        MigrationPhase(
            id="phase-3-pyhuey-rename",
            title="Prepare PyHuey naming and repo alignment",
            target_repo="DylanLRPollock/PyHuey",
            status="not_started",
            risk="high",
            checklist=[
                "Document compatibility boundaries before any rename.",
                "Preserve import compatibility for shipped tooling.",
            ],
        ),
        MigrationPhase(
            id="phase-4-remove-compat-shims",
            title="Retire temporary compatibility shims",
            target_repo="DylanLRPollock/Monkey-Head-Project",
            status="not_started",
            risk="high",
            blockers=[
                "Wait until Command Center, runtime, and PyHuey adapters stabilize."
            ],
        ),
        MigrationPhase(
            id="phase-5-v1-run-dashboard",
            title="Surface V1 proof-loop status in the dashboard",
            target_repo="DylanLRPollock/command-center",
            status="in_progress",
            risk="medium",
            checklist=[
                "Normalize structured run logs.",
                "Expose copy-only prompts and reviewer checklists.",
                "Provide safe sample runs to the frontend.",
            ],
        ),
    ]


def default_validation_commands() -> list[ValidationCommand]:
    """Return copy-only validation commands grouped by repo."""

    from huey.gui.validation import all_validation_commands

    return all_validation_commands()


def default_operator_panel_state() -> OperatorPanelState:
    """Return safe mock operator-panel state."""

    return OperatorPanelState(
        api_url="http://127.0.0.1:1995",
        health_status="read-only",
        memory_status="local",
        governance_status="documentation-only",
        connector_status="partial",
        runtime_status="standby",
        ffmpeg_status="unknown",
        v1_status="fixture-ready",
        mock_only=True,
    )


__all__ = [
    "default_migration_phases",
    "default_operator_panel_state",
    "default_repositories",
    "default_validation_commands",
]
