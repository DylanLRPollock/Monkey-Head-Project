"""Record transformation helpers for downstream indexing and storage."""

from __future__ import annotations

from typing import Callable

TransformRule = Callable[[object], object]


def transform_records(
    records: list[dict[str, object]],
    *,
    field_rules: dict[str, TransformRule] | None = None,
) -> list[dict[str, object]]:
    rules = dict(field_rules or {})
    transformed: list[dict[str, object]] = []
    for record in records:
        updated: dict[str, object] = {}
        for key, value in record.items():
            rule = rules.get(key)
            updated[key] = value if rule is None else rule(value)
        transformed.append(updated)
    return transformed


__all__ = ["TransformRule", "transform_records"]
