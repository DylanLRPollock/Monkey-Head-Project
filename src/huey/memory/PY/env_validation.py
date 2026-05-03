"""Centralized environment validation for security-sensitive settings."""

from __future__ import annotations

import os
import warnings

DEVELOPMENT_ENVS = {"", "dev", "development", "local", "test", "testing"}
_PLACEHOLDER_VALUES = {
    "changeme",
    "change-me",
    "replace-me",
    "replace_this",
    "replace-this",
    "placeholder",
    "token",
    "password",
    "secret",
    "set-me",
    "setme",
    "example",
    "dummy",
    "your-token-here",
    "your_token_here",
}

DATABASE_PASSWORD_VARIABLES = (
    "DB_PASSWORD",
    "DATABASE_PASSWORD",
    "POSTGRES_PASSWORD",
    "MYSQL_PASSWORD",
)

PRODUCTION_REQUIRED_SECRET_VARIABLES = (
    "HUEY_API_TOKEN",
    "OPENAI_API_KEY",
)


def configured_environment() -> str:
    return os.getenv("HUEY_ENV", "").strip().lower()


def _looks_like_placeholder(value: str) -> bool:
    compact = value.strip().lower().replace(" ", "")
    return compact in _PLACEHOLDER_VALUES or compact.startswith("your-")


def _vnc_enabled() -> bool:
    value = os.getenv("HUEY_VNC_ENABLED", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def validate_security_sensitive_environment() -> None:
    """Validate required env vars; fail fast outside development."""

    env = configured_environment()
    is_development = env in DEVELOPMENT_ENVS

    checks: list[str] = ["HUEY_ENV", *PRODUCTION_REQUIRED_SECRET_VARIABLES, *DATABASE_PASSWORD_VARIABLES]
    if _vnc_enabled():
        checks.append("VNC_PASSWORD")

    issues: list[str] = []
    for key in checks:
        value = os.getenv(key, "")
        if not value.strip() or _looks_like_placeholder(value):
            issues.append(f"{key} is missing, empty, or uses a placeholder value")

    if not issues:
        return

    if is_development:
        for issue in issues:
            warnings.warn(f"[huey-env-validation] {issue}", RuntimeWarning, stacklevel=2)
        return

    joined = "; ".join(issues)
    raise RuntimeError(f"Environment validation failed for HUEY_ENV='{env or 'unset'}': {joined}")
