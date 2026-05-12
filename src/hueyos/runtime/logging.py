"""Structured JSONL logging helpers for HueyOS V1 run records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REQUIRED_V1_FIELDS = {
    "run_id",
    "timestamp_start",
    "timestamp_end",
    "source_file",
    "transcript",
    "response",
    "transcription_engine",
    "transcription_model",
    "cognition_provider",
    "cognition_model",
    "runtime_seconds",
    "exit_status",
}


def _normalize_json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("record includes non-finite float value")
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("record contains non-string dictionary key")
            normalized[key] = _normalize_json_value(item)
        return normalized

    if isinstance(value, (list, tuple)):
        return [_normalize_json_value(item) for item in value]

    raise TypeError(f"record contains non-JSON-safe value of type {type(value).__name__}")


def validate_run_record(record: dict) -> dict:
    """Validate and normalize a V1 run record for structured JSON output."""
    if not isinstance(record, dict):
        raise TypeError("record must be a dictionary")

    missing = REQUIRED_V1_FIELDS - set(record.keys())
    if missing:
        missing_fields = ", ".join(sorted(missing))
        raise ValueError(f"record missing required V1 field(s): {missing_fields}")

    normalized = _normalize_json_value(record)
    json.dumps(normalized, ensure_ascii=False, allow_nan=False)
    return normalized


def append_jsonl_record(path: str | Path, record: dict) -> None:
    """Append one validated V1 run record to a JSONL file."""
    normalized_record = validate_run_record(record)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(normalized_record, ensure_ascii=False, allow_nan=False) + "\n")
