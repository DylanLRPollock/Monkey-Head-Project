"""Simplified preset data model used for testing integrations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class PresetItem:
    """Minimal representation of a PyGPT preset definition."""

    name: str = ""
    filename: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
