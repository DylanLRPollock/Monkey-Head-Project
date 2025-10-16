# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Preload Data module (src/monkey_head/scripts)

"""Utility helpers for preloading reference data used by the tests."""

from __future__ import annotations

from typing import Dict, List

__all__ = ["preload_all"]


def _default_prompts() -> List[str]:
    """Return a small collection of canned prompts."""

    return [
        "Summarise the latest telemetry report.",
        "Draft a follow-up email to the operator.",
    ]


def _default_memory_snapshot() -> Dict[str, List[str]]:
    """Return a lightweight snapshot of the shared memory structure."""

    return {
        "PDF": ["systems-overview.pdf", "emergency-playbook.pdf"],
        "RAW": ["diagnostics.log"],
    }


def preload_all() -> Dict[str, object]:
    """Return prompt and memory metadata required by the UI layer."""

    return {
        "prompts": _default_prompts(),
        "memory": _default_memory_snapshot(),
    }
