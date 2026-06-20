"""Frontend/backend connection settings for Command Center."""

from __future__ import annotations

import os


def default_backend_url() -> str:
    """Return the default local backend URL."""

    return os.environ.get("HUEY_COMMAND_CENTER_BACKEND", "http://127.0.0.1:1996")


def command_center_frontend_url() -> str:
    """Return the configured frontend URL or repository landing page."""

    return os.environ.get(
        "HUEY_COMMAND_CENTER_FRONTEND",
        "https://github.com/DylanLRPollock/command-center",
    )


def export_frontend_config() -> dict[str, str]:
    """Return a JSON-safe frontend configuration payload."""

    return {
        "backend_url": default_backend_url(),
        "frontend_url": command_center_frontend_url(),
    }


__all__ = [
    "command_center_frontend_url",
    "default_backend_url",
    "export_frontend_config",
]
