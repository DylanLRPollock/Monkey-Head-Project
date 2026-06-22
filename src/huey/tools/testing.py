"""Testing helpers for the scaffold subsystem tree."""

from __future__ import annotations


def build_fixture_payload(**overrides: object) -> dict[str, object]:
    payload = {
        "name": "fixture",
        "status": "ready",
        "priority": 1,
    }
    payload.update(overrides)
    return payload


def assert_mapping_subset(
    expected: dict[str, object], actual: dict[str, object]
) -> None:
    for key, value in expected.items():
        assert key in actual, f"Missing key: {key}"
        assert actual[key] == value, f"Unexpected value for {key}: {actual[key]!r}"


__all__ = ["assert_mapping_subset", "build_fixture_payload"]
