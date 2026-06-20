"""Minimal context item used by lightweight plugin command handlers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CtxItem:
    extra: dict[str, object] = field(default_factory=dict)
    agent_call: bool = False
    input_text: str = ""
    output_text: str = ""


__all__ = ["CtxItem"]
