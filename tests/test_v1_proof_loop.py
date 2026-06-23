"""Tests for the higher-level V1 proof loop helpers."""

from __future__ import annotations

from pathlib import Path

from huey.v1.proof_loop import run_fixture, validate_result


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
