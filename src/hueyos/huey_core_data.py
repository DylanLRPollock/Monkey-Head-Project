"""Core data helpers for Huey."""

from __future__ import annotations


def generate_core_data(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("data must be a dictionary")
    return {
        "processed": True,
        "input_length": len(data),
        "details": data,
    }


__all__ = ["generate_core_data"]
