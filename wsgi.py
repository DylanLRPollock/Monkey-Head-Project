"""Compatibility WSGI entry point at the repository root."""

from __future__ import annotations

from huey.wsgi import app, application

__all__ = ["app", "application"]
