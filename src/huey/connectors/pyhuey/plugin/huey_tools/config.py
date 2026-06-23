"""Configuration helpers for the Huey Tools plugin."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

from .bridge import HueyBridgeConfig


def _env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class HueyToolsSettings:
    monkey_head_project_path: str | None = None
    python_executable: str | None = None
    timeout_seconds: float = 120.0
    allow_external_paths: bool = False
    allowed_workspace_roots: list[str] = field(default_factory=list)


def default_settings() -> HueyToolsSettings:
    return HueyToolsSettings(
        monkey_head_project_path=None,
        python_executable=sys.executable,
        timeout_seconds=120.0,
        allow_external_paths=False,
        allowed_workspace_roots=[],
    )


def settings_to_bridge_config(settings: HueyToolsSettings) -> HueyBridgeConfig:
    return HueyBridgeConfig(
        monkey_head_project_path=(
            None
            if settings.monkey_head_project_path is None
            else Path(settings.monkey_head_project_path)
        ),
        python_executable=settings.python_executable or sys.executable,
        timeout_seconds=settings.timeout_seconds,
        allow_external_paths=settings.allow_external_paths,
        allowed_workspace_roots=[Path(path) for path in settings.allowed_workspace_roots],
    )


def load_settings_from_env() -> HueyToolsSettings:
    roots = os.getenv("HUEY_TOOLS_ALLOWED_WORKSPACE_ROOTS", "").strip()
    root_values = [value for value in roots.split(os.pathsep) if value]
    settings = default_settings()
    settings.monkey_head_project_path = os.getenv("HUEY_MONKEY_HEAD_PROJECT_PATH")
    settings.python_executable = os.getenv("HUEY_PYTHON_EXECUTABLE") or sys.executable
    settings.timeout_seconds = float(
        os.getenv("HUEY_TOOLS_TIMEOUT_SECONDS", str(settings.timeout_seconds))
    )
    settings.allow_external_paths = _env_flag(
        "HUEY_TOOLS_ALLOW_EXTERNAL_PATHS",
        default=settings.allow_external_paths,
    )
    settings.allowed_workspace_roots = root_values
    return settings


__all__ = [
    "HueyToolsSettings",
    "default_settings",
    "load_settings_from_env",
    "settings_to_bridge_config",
]
