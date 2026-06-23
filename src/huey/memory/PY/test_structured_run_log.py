from __future__ import annotations

from pathlib import Path

from huey.v1.structured_run_log import StructuredRunLog


def test_append_and_read_jsonl(tmp_path: Path) -> None:
    log = StructuredRunLog(tmp_path / "run.jsonl")
    event = log.append("test.event", {"ok": True})
    records = log.read()
    assert records[0]["event_id"] == event["event_id"]
    assert records[0]["payload"]["ok"] is True
