"""Cover GUI state transitions for each published event type."""

from __future__ import annotations

from huey.gui.events import Event, EventType
from huey.gui.state import build_default_state


def test_state_applies_runtime_memory_model_and_repository_events():
    state = build_default_state()
    state.apply_event(Event(EventType.API_CONNECTED, {"status": "healthy"}))
    assert state.runtime.api_connected is True
    assert state.runtime.health_status == "healthy"

    state.apply_event(Event(EventType.RUN_STARTED))
    assert state.runtime.orchestration_status == "running"
    state.apply_event(Event(EventType.RUN_FINISHED, {"status": "complete"}))
    assert state.runtime.orchestration_status == "complete"

    state.apply_event(
        Event(EventType.MEMORY_UPDATED, {"indexed_documents": 7}, timestamp="now")
    )
    assert state.memory.indexed_documents == 7
    assert state.memory.last_update == "now"

    state.apply_event(Event(EventType.MODEL_CHANGED, {"model": "local-model"}))
    assert state.runtime.active_model == "local-model"
    state.apply_event(Event(EventType.REPOSITORY_CHANGED, {"repository": "owner/repo"}))
    assert state.operator.selected_repository == "owner/repo"
    assert state.repositories.active_repository == "owner/repo"
    assert len(state.recent_events) == 6


def test_empty_or_unknown_payload_values_keep_documented_fallbacks():
    state = build_default_state()
    previous_count = state.memory.indexed_documents
    state.apply_event(Event(EventType.MEMORY_UPDATED, {}))
    assert state.memory.indexed_documents == previous_count
    state.apply_event(Event(EventType.MODEL_CHANGED, {}))
    assert state.runtime.active_model == ""
    state.apply_event(Event(EventType.REPOSITORY_CHANGED, {"repository": ""}))
    assert state.operator.selected_repository == "DylanLRPollock/Monkey-Head-Project"
    assert state.repositories.active_repository == "DylanLRPollock/Monkey-Head-Project"
    state.apply_event(Event(EventType.TRANSCRIPTION_COMPLETE))
    assert len(state.recent_events) == 4
