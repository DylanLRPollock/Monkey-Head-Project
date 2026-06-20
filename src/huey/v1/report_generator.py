"""Report generation helpers for V1 fixture runs."""

from __future__ import annotations

import json

from huey.v1.proof_loop import generate_report


def generate_json_report(run_records: list[dict[str, object]]) -> str:
    """Return a JSON report for V1 runs."""

    payload = {
        "summary": generate_report(run_records),
        "runs": run_records,
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def generate_markdown_report(run_records: list[dict[str, object]]) -> str:
    """Return a Markdown report for V1 runs."""

    summary = generate_report(run_records)
    lines = [
        "# V1 Proof Loop Report",
        "",
        f"- Total runs: {summary['total']}",
        f"- Successful: {summary['successful']}",
        f"- Failed: {summary['failed']}",
        f"- Success rate: {summary['success_rate']:.2%}",
        "",
        "| Run ID | Status | Transcript | Response |",
        "| --- | --- | --- | --- |",
    ]
    for record in run_records:
        status = "success" if record.get("exit_status") == "success" else "failed"
        transcript = str(record.get("transcript") or "").replace("\n", " ")[:60]
        response = str(record.get("response") or "").replace("\n", " ")[:60]
        lines.append(
            f"| {record.get('run_id')} | {status} | {transcript} | {response} |"
        )
    return "\n".join(lines)


def generate_html_report(run_records: list[dict[str, object]]) -> str:
    """Return a lightweight HTML report for V1 runs."""

    summary = generate_report(run_records)
    rows = []
    for record in run_records:
        status = "success" if record.get("exit_status") == "success" else "failed"
        rows.append(
            "<tr>"
            f"<td>{record.get('run_id')}</td>"
            f"<td>{status}</td>"
            f"<td>{record.get('transcript', '')}</td>"
            f"<td>{record.get('response', '')}</td>"
            "</tr>"
        )
    return (
        "<html><body>"
        "<h1>V1 Proof Loop Report</h1>"
        f"<p>Total: {summary['total']} | Successful: {summary['successful']} | "
        f"Failed: {summary['failed']}</p>"
        "<table border='1'><thead><tr><th>Run ID</th><th>Status</th>"
        "<th>Transcript</th><th>Response</th></tr></thead><tbody>"
        f"{''.join(rows)}"
        "</tbody></table></body></html>"
    )


__all__ = [
    "generate_html_report",
    "generate_json_report",
    "generate_markdown_report",
]
