"""Validation helpers for extracted and transformed records."""

from __future__ import annotations

from typing import Any


def validate_required_fields(record: dict[str, object], fields: list[str]) -> list[str]:
    return [
        field for field in fields if field not in record or record[field] in {"", None}
    ]


def validate_schema(
    record: dict[str, object], schema: dict[str, type[Any]]
) -> dict[str, str]:
    errors: dict[str, str] = {}
    for field, expected_type in schema.items():
        value = record.get(field)
        if value is None:
            errors[field] = "missing"
            continue
        if not isinstance(value, expected_type):
            errors[field] = (
                f"expected {expected_type.__name__}, got {type(value).__name__}"
            )
    return errors


__all__ = ["validate_required_fields", "validate_schema"]
