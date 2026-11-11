"""Coverage for V1 report, response and append-only run-log edge cases."""

from __future__ import annotations

import json

import pytest

from huey.v1 import report_generator, structured_run_log
from huey.v1.response_bridge import ResponseBridge, main as response_main


def test_report_formats_empty_and_mixed_records_with_escaped_html() -> None:
    assert json.loads(report_generator.generate_json_report([]))["summary"]["total"] == 0
    assert "Success rate: 0.00%" in report_generator.generate_markdown_report([])

    records = [
        {"run_id": "<run&1>", "exit_status": "success", "transcript": "a\nb", "response": "ok"},
        {"run_id": "failed", "exit_status": "error", "transcript": "", "response": None},
    ]
    markdown = report_generator.generate_markdown_report(records)
    assert "a b" in markdown
    assert "| failed | failed |  |  |" in markdown
    html = report_generator.generate_html_report(records)
    assert "&lt;run&amp;1&gt;" in html
    assert "<td>failed</td>" in html


def test_structured_run_log_append_read_and_empty(tmp_path) -> None:
    path = tmp_path / "nested" / "runs.jsonl"
    log = structured_run_log.StructuredRunLog(path)
    assert log.read() == []
    first = log.append("proof", {"status": "ok"})
    second = log.append("audit", {})
    records = log.read()
    assert len(records) == 2
    assert records[0]["event_id"] == first["event_id"]
    assert records[1]["event_type"] == second["event_type"]
    assert records[0]["payload"] == {"status": "ok"}


@pytest.mark.parametrize("event_type", ["", "  ", None])
def test_structured_run_log_rejects_empty_event_type(tmp_path, event_type) -> None:
    with pytest.raises(ValueError, match="event_type is required"):
        structured_run_log.StructuredRunLog(tmp_path / "events.jsonl").append(event_type, {})


def test_structured_run_log_rejects_payload_and_malformed_jsonl(tmp_path) -> None:
    log = structured_run_log.StructuredRunLog(tmp_path / "events.jsonl")
    with pytest.raises(TypeError, match="payload must be a dictionary"):
        log.append("proof", [])

    log.log_path.write_text('{"ok": true}\nnot-json\n', encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        log.read()
    log.log_path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="record type at line 1"):
        log.read()


def test_structured_run_log_cli_append_read_and_invalid_payload(tmp_path, capsys) -> None:
    path = str(tmp_path / "cli.jsonl")
    assert structured_run_log.main([path, "append", "proof", '{"ok": true}']) == 0
    assert json.loads(capsys.readouterr().out)["payload"] == {"ok": True}
    assert structured_run_log.main([path, "read"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["event_type"] == "proof"
    with pytest.raises(json.JSONDecodeError):
        structured_run_log.main([path, "append", "bad", "{"])


def test_response_bridge_api_guards_and_cli_output(monkeypatch, capsys) -> None:
    with pytest.raises(ValueError, match="mode must"):
        ResponseBridge("remote")
    with pytest.raises(ValueError, match="prompt is required"):
        ResponseBridge().respond("  ")
    with pytest.raises(RuntimeError, match="API_KEY is required"):
        ResponseBridge("api").respond("hello")
    monkeypatch.setenv("HUEY_RESPONSE_API_KEY", "configured")
    with pytest.raises(RuntimeError, match="not implemented"):
        ResponseBridge("api").respond("hello")

    assert response_main(["hello", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["mode"] == "mock"
    assert response_main(["hello"]) == 0
    assert "[mock] Huey V1 received: hello" in capsys.readouterr().out
