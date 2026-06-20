"""Tests for V1 run parsing helpers."""

from __future__ import annotations

import json

from huey.gui.v1_runs import export_runs_json, filter_runs, parse_jsonl


def test_parse_jsonl_handles_valid_records():
    text = "\n".join(
        [
            json.dumps(
                {
                    "run_id": "run-1",
                    "source_file": "fixtures/one.mp3",
                    "transcript": "hello",
                    "response": "hi",
                    "exit_status": "success",
                }
            ),
            json.dumps(
                {
                    "run_id": "run-2",
                    "source_file": "fixtures/two.mp3",
                    "transcript": "",
                    "response": "",
                    "exit_status": "error",
                    "error_message_if_any": "boom",
                }
            ),
        ]
    )

    records = parse_jsonl(text)

    assert len(records) == 2
    assert records[0].status == "passed"
    assert records[1].status == "failed"


def test_parse_jsonl_skips_blank_lines():
    records = parse_jsonl(
        json.dumps(
            {
                "run_id": "run-1",
                "source_file": "fixtures/one.mp3",
                "transcript": "hello",
                "response": "hi",
                "exit_status": "success",
            }
        )
        + "\n\n"
    )

    assert len(records) == 1


def test_filter_runs_by_status():
    records = parse_jsonl(
        "\n".join(
            [
                json.dumps(
                    {
                        "run_id": "run-1",
                        "source_file": "fixtures/one.mp3",
                        "transcript": "hello",
                        "response": "hi",
                        "exit_status": "success",
                    }
                ),
                json.dumps(
                    {
                        "run_id": "run-2",
                        "source_file": "fixtures/two.mp3",
                        "transcript": "",
                        "response": "",
                        "exit_status": "error",
                    }
                ),
            ]
        )
    )

    filtered = filter_runs(records, status="failed")

    assert len(filtered) == 1
    assert filtered[0].fixture == "two.mp3"


def test_export_runs_json_roundtrip():
    records = parse_jsonl(
        json.dumps(
            {
                "run_id": "run-1",
                "source_file": "fixtures/one.mp3",
                "transcript": "hello",
                "response": "hi",
                "exit_status": "success",
            }
        )
    )

    payload = json.loads(export_runs_json(records))

    assert payload[0]["fixture"] == "one.mp3"
    assert payload[0]["status"] == "passed"
