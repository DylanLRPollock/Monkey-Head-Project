"""Coverage for migration prompts and empty-phase fallback wording."""

from __future__ import annotations

import pytest

from huey.gui.models import MigrationPhase
from huey.gui.prompts import (
    dependency_security_prompt,
    generate_next_best_task_prompt,
    generate_phase_prompt,
    generate_pr_body,
    generate_review_checklist,
    phase_2_5_prompt,
    phase_3_prompt,
)


def _phase(**overrides) -> MigrationPhase:
    values = {
        "id": "phase-test",
        "title": "Cover connectors",
        "target_repo": "Monkey-Head-Project",
        "status": "ready_for_pr",
        "risk": "high",
        "checklist": ["Add tests", "Keep scope focused"],
        "validation_commands": ["pytest -q", "ruff check"],
        "blockers": ["Need review"],
    }
    values.update(overrides)
    return MigrationPhase(**values)


def test_phase_prompt_and_pr_draft_include_work_and_validation_details() -> None:
    phase = _phase()
    prompt = generate_phase_prompt(phase)
    assert "Work phase: Cover connectors" in prompt
    assert "- Add tests" in prompt
    assert "- pytest -q" in prompt
    assert "- Need review" in prompt
    body = generate_pr_body(phase)
    assert "Advance **Cover connectors**" in body
    assert "`pytest -q`" in body
    checklist = generate_review_checklist(phase)
    assert "- [ ] Keep scope focused" in checklist
    assert "- [ ] Run `ruff check`" in checklist


def test_prompt_helpers_supply_fallbacks_and_skip_completed_phases() -> None:
    phase = _phase(checklist=[], validation_commands=[], blockers=[])
    prompt = generate_phase_prompt(phase)
    assert "No checklist yet." in prompt
    assert "No validation commands recorded." in prompt
    assert "No blockers recorded." in prompt
    body = generate_pr_body(phase)
    assert "- No checklist" in body
    assert "- No validation commands recorded" in body
    assert (
        generate_review_checklist(phase)
        == "- [ ] Review the changed code paths for compatibility."
    )
    assert generate_next_best_task_prompt(
        [_phase(status="merged"), _phase(status="blocked")]
    ) == ("All current migration phases are merged or blocked.")
    assert "Cover connectors" in generate_next_best_task_prompt(
        [
            _phase(id="z", status="ready_for_pr", risk="low"),
            _phase(id="a", status="in_progress", risk="critical"),
        ]
    )


def test_prompt_priority_handles_unknown_status_and_risk() -> None:
    selected = generate_next_best_task_prompt(
        [
            _phase(id="unknown", status="unknown", risk="unknown"),
            _phase(id="ready", status="ready_for_pr", risk="low"),
        ]
    )
    assert "Work phase: Cover connectors" in selected
    assert "Phase" not in generate_next_best_task_prompt([])


def test_default_phase_prompts_and_dependency_security_prompt() -> None:
    assert "Reconcile PyHuey connector integration" in phase_2_5_prompt()
    assert "PyHuey" in phase_3_prompt()
    assert "requirements.txt" in dependency_security_prompt()


def test_unknown_phase_id_raises_key_error(monkeypatch) -> None:
    from huey.gui import prompts

    monkeypatch.setattr(prompts, "default_migration_phases", lambda: [])
    with pytest.raises(KeyError, match="unknown-phase"):
        prompts._phase_by_id("unknown-phase")
