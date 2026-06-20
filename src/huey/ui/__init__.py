"""User-interface helpers for terminal, CLI, and web surfaces."""

from __future__ import annotations

from .adaptive_ui import AdaptiveUIEngine, AdaptiveUIProfile
from .cli import build_cli_parser
from .dashboard import build_dashboard
from .interface import InterfaceController
from .terminal import render_status_table
from .web_ui import WebInterface

__all__ = [
    "AdaptiveUIEngine",
    "AdaptiveUIProfile",
    "InterfaceController",
    "WebInterface",
    "build_cli_parser",
    "build_dashboard",
    "render_status_table",
]
