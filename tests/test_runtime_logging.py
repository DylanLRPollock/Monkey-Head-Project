import json
from pathlib import Path

import pytest

from hueyos.runtime.logging import append_jsonl_record, validate_run_record


def _valid_record() -> dict:
    return {
        "run_id": "run-123",
        "timestamp_start": "2026-05-12T00:00:00Z",
        "timestamp_end": "2026-05-12T00:00:01Z",
        "source_file": "fixture.mp3",
        "transcript": "hello",
        "response": {"text": "ack"},
        "transcription_engine": "local",
        "transcription_model": "whisper-small",
        "cognition_provider": "mock-bridge",
        "cognition_model": "mock-v1",
        "runtime_seconds": 1.23,
        "exit_status": "success",
    }


def test_append_jsonl_record_writes_valid_record(tmp_path: Path):
    log_path = tmp_path / "logs" / "runs.jsonl"
    record = _valid_record()

    append_jsonl_record(log_path, record)

    lines = log_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    persisted = json.loads(lines[0])
    assert persisted == record


def test_validate_run_record_fails_when_required_field_missing():
    record = _valid_record()
    record.pop("response")

    with pytest.raises(ValueError, match="response"):
        validate_run_record(record)


def test_validate_run_record_fails_for_non_json_safe_value():
    record = _valid_record()
    record["response"] = {"bad": {"nested-set"}}

    with pytest.raises(TypeError, match="non-JSON-safe"):
        validate_run_record(record)
