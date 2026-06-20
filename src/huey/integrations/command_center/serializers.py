"""Serializers for Command Center payloads."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path


def _normalise(value: object) -> object:
    if is_dataclass(value):
        return {_key: _normalise(_value) for _key, _value in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _normalise(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_normalise(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def repo_to_json(repo: object) -> dict[str, object]:
    """Serialize a repository status object."""

    return dict(_normalise(repo))


def run_to_json(run_record: object) -> dict[str, object]:
    """Serialize a V1 run record."""

    return dict(_normalise(run_record))


def memory_to_json(memory_state: object) -> dict[str, object]:
    """Serialize a memory or indexing payload."""

    return dict(_normalise(memory_state))


def state_to_json(state: object) -> dict[str, object]:
    """Serialize a nested state payload."""

    return dict(_normalise(state))


__all__ = ["memory_to_json", "repo_to_json", "run_to_json", "state_to_json"]
