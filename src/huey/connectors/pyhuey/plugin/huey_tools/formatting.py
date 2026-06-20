"""Formatting helpers for Huey Tools plugin responses."""

from __future__ import annotations

import json

from .bridge import HueyBridgeResult
from .registry import HueyToolSpec
from .safety import HueyToolSafetyPolicy, policy_to_dict


def safe_json_dumps(value: object) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def format_bridge_result(result: HueyBridgeResult) -> str:
    payload = result.parsed_json if result.parsed_json is not None else result.to_dict()
    return safe_json_dumps(payload)


def format_status(status: dict) -> str:
    return safe_json_dumps(status)


def format_tool_specs(specs: list[HueyToolSpec]) -> str:
    return safe_json_dumps(
        [
            {
                "id": spec.id,
                "group": spec.group,
                "implemented": spec.implemented,
                "safe_by_default": spec.safe_by_default,
            }
            for spec in specs
        ]
    )


def format_safety_policy(policy: HueyToolSafetyPolicy) -> str:
    return safe_json_dumps(policy_to_dict(policy))


__all__ = [
    "format_bridge_result",
    "format_safety_policy",
    "format_status",
    "format_tool_specs",
    "safe_json_dumps",
]
