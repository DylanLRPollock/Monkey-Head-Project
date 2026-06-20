"""Helpers for normalizing V1 proof-loop run records."""

from __future__ import annotations

import json
from pathlib import Path

from huey.gui.models import V1RunRecord, dataclass_list_to_dicts


def parse_jsonl(text: str) -> list[V1RunRecord]:
    """Parse pasted JSONL text into ``V1RunRecord`` objects."""

    records: list[V1RunRecord] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at line {line_number}") from exc
        if not isinstance(payload, dict):
            raise ValueError(f"JSONL line {line_number} is not a JSON object")
        records.append(record_from_dict(payload))
    return records


def load_jsonl(path: Path) -> list[V1RunRecord]:
    """Load ``V1RunRecord`` objects from a local JSONL file."""

    return parse_jsonl(path.read_text(encoding="utf-8"))


def record_from_dict(payload: dict[str, object]) -> V1RunRecord:
    """Normalize a raw V1 run-log dictionary."""

    source_file = str(payload.get("source_file", payload.get("fixture", "")))
    status = "passed" if payload.get("exit_status") == "success" else "failed"
    return V1RunRecord(
        id=str(payload.get("run_id", payload.get("id", source_file or "unknown-run"))),
        fixture=Path(source_file).name or "unknown-fixture",
        status=status,  # type: ignore[arg-type]
        transcription_status=("complete" if payload.get("transcript") else "missing"),
        cognition_status=("complete" if payload.get("response") else "missing"),
        response_text=str(payload.get("response") or ""),
        error=str(payload.get("error_message_if_any") or ""),
        raw=dict(payload),
    )


def filter_runs(
    runs: list[V1RunRecord],
    status: str | None = None,
    contains: str | None = None,
    fixture: str | None = None,
) -> list[V1RunRecord]:
    """Filter V1 run records for UI display."""

    filtered = list(runs)
    if status:
        filtered = [run for run in filtered if run.status == status]
    if fixture:
        filtered = [run for run in filtered if run.fixture == fixture]
    if contains:
        needle = contains.lower()
        filtered = [
            run
            for run in filtered
            if needle in run.response_text.lower() or needle in run.error.lower()
        ]
    return filtered


def export_runs_json(runs: list[V1RunRecord]) -> str:
    """Export selected runs as pretty JSON."""

    return json.dumps(dataclass_list_to_dicts(runs), indent=2, sort_keys=True)


def sample_v1_runs() -> list[V1RunRecord]:
    """Return mock/sample V1 proof-loop records."""

    return [
        record_from_dict(
            {
                "run_id": "sample-run-001",
                "source_file": "fixtures/hello-world.mp3",
                "transcript": "Hello Huey, run the fixture loop.",
                "response": "Fixture loop acknowledged.",
                "exit_status": "success",
            }
        ),
        record_from_dict(
            {
                "run_id": "sample-run-002",
                "source_file": "fixtures/noisy-input.mp3",
                "transcript": "",
                "response": "",
                "exit_status": "error",
                "error_message_if_any": "Transcription pipeline could not extract speech.",
            }
        ),
    ]


__all__ = [
    "export_runs_json",
    "filter_runs",
    "load_jsonl",
    "parse_jsonl",
    "record_from_dict",
    "sample_v1_runs",
]
