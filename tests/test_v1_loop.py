import json
from pathlib import Path

from hueyos.runtime.v1_loop import run_v1_loop


REQUIRED_FIELDS = {
    "run_id",
    "timestamp_start",
    "timestamp_end",
    "source_file",
    "transcription_engine",
    "transcription_model",
    "transcript",
    "cognition_provider",
    "cognition_model",
    "response",
    "runtime_seconds",
    "exit_status",
    "error_message_if_any",
}


def test_v1_loop_writes_json_record(tmp_path: Path):
    fixture = tmp_path / "fixture.mp3"
    fixture.write_bytes(b"fake-mp3-content")

    json_log = tmp_path / "run.json"

    def fake_transcribe(source_file: str):
        assert source_file.endswith("fixture.mp3")
        return {
            "transcription_engine": "local-mock",
            "transcription_model": "mock-whisper-small",
            "transcript": "hello from fixture",
        }

    def fake_cognition(transcript: str):
        assert transcript == "hello from fixture"
        return {
            "cognition_provider": "bridge-mock",
            "cognition_model": "mock-cognition-v1",
            "response": {"intent": "ack", "text": "received"},
        }

    def write_json(record: dict):
        json_log.write_text(json.dumps(record), encoding="utf-8")

    record = run_v1_loop(fixture, fake_transcribe, fake_cognition, write_json)

    assert set(record.keys()) == REQUIRED_FIELDS
    assert record["source_file"] == str(fixture)
    assert record["exit_status"] == "success"

    persisted = json.loads(json_log.read_text(encoding="utf-8"))
    assert persisted == record


def test_v1_loop_writes_jsonl_record(tmp_path: Path):
    fixture = tmp_path / "fixture.mp3"
    fixture.write_bytes(b"fake-mp3-content")

    jsonl_log = tmp_path / "runs.jsonl"

    def fake_transcribe(_source_file: str):
        return {
            "transcription_engine": "local-mock",
            "transcription_model": "mock-whisper-small",
            "transcript": "sample transcript",
        }

    def fake_cognition(_transcript: str):
        return {
            "cognition_provider": "bridge-mock",
            "cognition_model": "mock-cognition-v1",
            "response": "mock response",
        }

    def append_jsonl(record: dict):
        with jsonl_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    run_v1_loop(fixture, fake_transcribe, fake_cognition, append_jsonl)

    lines = jsonl_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    persisted = json.loads(lines[0])
    assert set(persisted.keys()) == REQUIRED_FIELDS
    assert persisted["transcript"] == "sample transcript"
    assert persisted["response"] == "mock response"
