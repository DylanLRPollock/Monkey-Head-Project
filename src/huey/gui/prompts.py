"""Prompt generators for migration phases and review flows."""

from __future__ import annotations

from huey.gui.defaults import default_migration_phases
from huey.gui.models import MigrationPhase

_STATUS_PRIORITY = {
    "in_progress": 0,
    "ready_for_pr": 1,
    "not_started": 2,
    "blocked": 3,
    "merged": 4,
}
_RISK_PRIORITY = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def generate_phase_prompt(phase: MigrationPhase) -> str:
    """Generate a Copilot/task-agent prompt for a migration phase."""

    checklist = (
        "\n".join(f"- {item}" for item in phase.checklist) or "- No checklist yet."
    )
    blockers = (
        "\n".join(f"- {item}" for item in phase.blockers) or "- No blockers recorded."
    )
    validation = (
        "\n".join(f"- {item}" for item in phase.validation_commands)
        or "- No validation commands recorded."
    )
    return (
        f"Work phase: {phase.title}\n"
        f"Target repository: {phase.target_repo}\n"
        f"Current status: {phase.status}\n"
        f"Risk: {phase.risk}\n\n"
        f"Checklist:\n{checklist}\n\n"
        f"Validation commands:\n{validation}\n\n"
        f"Blockers:\n{blockers}\n\n"
        "Implement the phase end-to-end, preserve compatibility, and keep all new "
        "surfaces read-only unless the phase explicitly says otherwise."
    )


def generate_next_best_task_prompt(phases: list[MigrationPhase]) -> str:
    """Pick the highest-priority unblocked phase and generate its prompt."""

    candidates = [
        phase for phase in phases if phase.status not in {"merged", "blocked"}
    ]
    if not candidates:
        return "All current migration phases are merged or blocked."
    selected = min(
        candidates,
        key=lambda phase: (
            _STATUS_PRIORITY.get(phase.status, 99),
            _RISK_PRIORITY.get(phase.risk, 99),
            phase.id,
        ),
    )
    return generate_phase_prompt(selected)


def generate_pr_body(phase: MigrationPhase) -> str:
    """Generate a PR body draft for the phase."""

    checklist = "\n".join(f"- {item}" for item in phase.checklist) or "- No checklist"
    validation = (
        "\n".join(f"- `{item}`" for item in phase.validation_commands)
        or "- No validation commands recorded"
    )
    return (
        f"## Summary\n\n"
        f"- Advance **{phase.title}** for `{phase.target_repo}`.\n"
        f"- Keep the surface compatible while moving toward canonical HueyOS layers.\n\n"
        f"## Checklist\n\n{checklist}\n\n"
        f"## Validation\n\n{validation}\n"
    )


def generate_review_checklist(phase: MigrationPhase) -> str:
    """Generate a reviewer checklist for the phase."""

    items = list(phase.checklist) or [
        "Review the changed code paths for compatibility."
    ]
    lines = [f"- [ ] {item}" for item in items]
    if phase.validation_commands:
        lines.extend(f"- [ ] Run `{command}`" for command in phase.validation_commands)
    return "\n".join(lines)


def _phase_by_id(phase_id: str) -> MigrationPhase:
    for phase in default_migration_phases():
        if phase.id == phase_id:
            return phase
    raise KeyError(f"Unknown phase id: {phase_id}")


def phase_2_5_prompt() -> str:
    """Prompt for PyHuey connector reconciliation in the Monkey repo."""

    return generate_phase_prompt(_phase_by_id("phase-2-5-pyhuey-connector"))


def phase_3_prompt() -> str:
    """Prompt for the later PyHuey package rename phase."""

    return generate_phase_prompt(_phase_by_id("phase-3-pyhuey-rename"))


def dependency_security_prompt() -> str:
    """Prompt for dependency and security refresh work."""

    return (
        "Audit the active dependency surface, archived snapshots, and direct pins. "
        "Keep requirements.txt, constraints.txt, and pyproject.toml aligned while "
        "preserving the current HueyOS runtime contract."
    )


__all__ = [
    "dependency_security_prompt",
    "generate_next_best_task_prompt",
    "generate_phase_prompt",
    "generate_pr_body",
    "generate_review_checklist",
    "phase_2_5_prompt",
    "phase_3_prompt",
]
