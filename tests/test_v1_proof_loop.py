"""Tests for the higher-level V1 proof loop helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

from huey.v1.proof_loop import (
    ProofLoop,
    generate_report,
    run_all_fixtures,
    run_fixture,
    validate_result,
)
from huey.v1.response_bridge import ResponseResult


def test_run_fixture_generates_successful_record(tmp_path):
    fixture = tmp_path / "fixture.mp3"
    fixture.write_bytes(b"not-real-audio")

    record = run_fixture(
        fixture,
        transcribe_func=lambda source: {
            "transcription_engine": "test",
            "transcription_model": "mock",
            "transcript": f"transcribed {Path(source).name}",
        },
        cognition_func=lambda transcript: {
            "cognition_provider": "test",
            "cognition_model": "mock",
            "response": transcript.upper(),
        },
        log_dir=tmp_path / "runs",
    )

    assert validate_result(record) is True
    assert (tmp_path / "runs" / "v1-runs.jsonl").exists()
    assert (tmp_path / "runs" / "hims-shadow" / "ledger.jsonl").exists()


def test_proof_loop_records_response_and_emits_shadow_record(tmp_path, monkeypatch):
    from huey.v1 import proof_loop as module

    source = tmp_path / "fixture.wav"
    source.write_bytes(b"test-audio")
    manifest = Mock()
    manifest.to_json_dict.return_value = {"sha256": "abc"}
    prepare = Mock(return_value=manifest)
    monkeypatch.setattr(module, "prepare_audio_for_transcription", prepare)
    bridge = Mock()
    bridge.respond.return_value = ResponseResult(
        mode="mock",
        prompt="fixture transcript",
        response="fixture response",
        created_at="2026-01-01T00:00:00+00:00",
    )
    run_log = Mock()
    run_log.log_path = tmp_path / "events" / "run.jsonl"
    run_log.append.return_value = {"event_id": "event-1"}
    shadow = Mock()

    result = ProofLoop(response_bridge=bridge, run_log=run_log, shadow_hims=shadow).run(
        source, tmp_path / "prepared", transcript_text="fixture transcript"
    )

    prepare.assert_called_once_with(
        source, tmp_path / "prepared" / "fixture_prepared.wav", overwrite=False
    )
    bridge.respond.assert_called_once_with("fixture transcript")
    run_log.append.assert_called_once()
    shadow.emit_proof_loop_record.assert_called_once()
    assert result.response == "fixture response"
    assert result.to_json_dict()["prepared_audio"].endswith("fixture_prepared.wav")


def test_proof_loop_uses_default_transcript_and_implicit_shadow(tmp_path, monkeypatch):
    from huey.v1 import proof_loop as module

    source = tmp_path / "sample.wav"
    source.write_bytes(b"audio")
    manifest = Mock()
    manifest.to_json_dict.return_value = {}
    monkeypatch.setattr(
        module, "prepare_audio_for_transcription", Mock(return_value=manifest)
    )
    bridge = Mock()
    bridge.respond.return_value = ResponseResult(
        mode="mock",
        prompt="Prepared audio fixture: sample.wav",
        response="ok",
        created_at="now",
    )
    log = Mock()
    log.log_path = tmp_path / "logs" / "run.jsonl"
    log.append.return_value = None
    result = ProofLoop(response_bridge=bridge, run_log=log).run(
        source, tmp_path / "out"
    )
    assert result.transcript == "Prepared audio fixture: sample.wav"
    bridge.respond.assert_called_once_with(result.transcript)


@pytest.mark.parametrize("failure_stage", ["preparation", "response"])
def test_proof_loop_failure_does_not_log_or_emit_shadow_record(
    tmp_path, monkeypatch, failure_stage
):
    from huey.v1 import proof_loop as module

    source = tmp_path / "failure.wav"
    source.write_bytes(b"fixture")
    manifest = Mock()
    manifest.to_json_dict.return_value = {}
    prepare = Mock(return_value=manifest)
    bridge = Mock()
    if failure_stage == "preparation":
        prepare.side_effect = RuntimeError("audio preparation failed")
    else:
        bridge.respond.side_effect = RuntimeError("response failed")
    monkeypatch.setattr(module, "prepare_audio_for_transcription", prepare)
    run_log = Mock()
    shadow = Mock()

    with pytest.raises(RuntimeError, match="failed"):
        ProofLoop(response_bridge=bridge, run_log=run_log, shadow_hims=shadow).run(
            source, tmp_path / "prepared"
        )

    run_log.append.assert_not_called()
    shadow.emit_proof_loop_record.assert_not_called()


def test_run_all_fixtures_uses_explicit_items_and_report_aggregates(tmp_path):
    first = tmp_path / "one.wav"
    second = tmp_path / "two.wav"
    first.write_bytes(b"one")
    second.write_bytes(b"two")
    records = run_all_fixtures(
        [first, second],
        log_dir=tmp_path / "logs",
        mock=True,
    )
    summary = generate_report([*records, {"run_id": "failed", "exit_status": "error"}])
    assert summary == {
        "total": 3,
        "successful": 2,
        "failed": 1,
        "success_rate": pytest.approx(2 / 3),
        "failed_runs": ["failed"],
    }


def test_run_fixture_uses_default_offline_cognition_and_empty_report(tmp_path):
    source = tmp_path / "fixture.wav"
    source.write_bytes(b"fixture")
    record = run_fixture(
        source,
        transcribe_func=lambda _path: " ",
        log_dir=tmp_path / "runs",
    )
    assert "no transcript available" in record["response"]
    assert generate_report([])["success_rate"] == 0.0
