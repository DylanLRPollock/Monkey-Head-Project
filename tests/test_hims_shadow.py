from __future__ import annotations

from pathlib import Path

from huey.hims.shadow import ShadowHIMS


def _build_run_record(fixture: Path, *, exit_status: str, error_message: str | None):
    return {
        "run_id": "run-001" if exit_status == "success" else "run-002",
        "timestamp_start": "2026-06-23T00:00:00Z",
        "timestamp_end": "2026-06-23T00:00:01Z",
        "source_file": str(fixture),
        "transcription_engine": "mock-transcriber",
        "transcription_model": "mock-whisper-v1",
        "transcript": "fixture transcript",
        "cognition_provider": "mock-cognition",
        "cognition_model": "mock-cognition-v1",
        "response": {"status": "ok"} if exit_status == "success" else None,
        "runtime_seconds": 1.0,
        "exit_status": exit_status,
        "error_message_if_any": error_message,
    }


def test_shadow_hims_emits_success_trace(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.mp3"
    fixture.write_bytes(b"fixture")
    shadow = ShadowHIMS(tmp_path / "hims-shadow")

    result = shadow.emit_run_record(
        _build_run_record(fixture, exit_status="success", error_message=None)
    )

    ledger = shadow.read_ledger()
    request_snapshot = shadow.read_message(result["request_message_id"])
    archive_snapshot = shadow.read_message(result["archive_message_id"])

    assert result["root_lineage_id"] == "run-001"
    assert [entry["event_type"] for entry in ledger] == [
        "message.created",
        "message.transition",
        "message.created",
        "message.transition",
        "message.transition",
        "message.created",
        "message.created",
    ]
    assert request_snapshot is not None
    assert request_snapshot["status"] == "executed"
    assert request_snapshot["current_mailbox"] == "executed"
    assert request_snapshot["lineage_metadata"]["terminal_state"] == "executed"
    assert archive_snapshot is not None
    assert archive_snapshot["status"] == "archived"
    assert archive_snapshot["payload"]["terminal_request_status"] == "executed"
    assert (shadow.root / "archived" / f"{result['packet_message_id']}.json").exists()
    assert (shadow.root / "executed" / f"{result['request_message_id']}.json").exists()
    assert (shadow.root / "executed" / f"{result['outcome_message_id']}.json").exists()
    assert (shadow.root / "archived" / f"{result['archive_message_id']}.json").exists()


def test_shadow_hims_emits_failure_trace(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.mp3"
    fixture.write_bytes(b"fixture")
    shadow = ShadowHIMS(tmp_path / "hims-shadow")

    result = shadow.emit_run_record(
        _build_run_record(
            fixture,
            exit_status="error",
            error_message="mock fixture failure",
        )
    )

    request_snapshot = shadow.read_message(result["request_message_id"])
    outcome_snapshot = shadow.read_message(result["outcome_message_id"])

    assert request_snapshot is not None
    assert request_snapshot["status"] == "rejected"
    assert request_snapshot["current_mailbox"] == "rejected"
    assert outcome_snapshot is not None
    assert outcome_snapshot["intent_type"] == "alert"
    assert outcome_snapshot["payload"]["error_message"] == "mock fixture failure"
    assert (shadow.root / "rejected" / f"{result['request_message_id']}.json").exists()
