"""Centralized environment validation for security-sensitive settings."""

from __future__ import annotations

import hmac
import json
import os
import re
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

PRODUCTION_REQUIRED_SECRET_VARIABLES = ("OPENAI_API_KEY",)
_API_PRINCIPALS_VARIABLE = "HUEY_API_PRINCIPALS_JSON"
_API_PRINCIPAL_ROLES = {"operator", "admin"}
_API_PRINCIPAL_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,63}")
_API_TOKEN_VARIABLES = (
    "HUEY_API_TOKEN",
    "HUEY_API_OPERATOR_TOKEN",
    "HUEY_API_ADMIN_TOKEN",
)


def parse_api_principals(raw: str) -> list[dict[str, str]]:
    """Parse individually named API credentials from their JSON environment value."""

    try:
        records = json.loads(raw)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("HUEY_API_PRINCIPALS_JSON must contain a JSON array") from exc

    if not isinstance(records, list):
        raise ValueError("HUEY_API_PRINCIPALS_JSON must contain a JSON array")

    principals: list[dict[str, str]] = []
    subjects: set[str] = set()
    tokens: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("Each API principal must be a JSON object")
        subject = record.get("subject")
        role = record.get("role")
        token = record.get("token")
        if (
            not isinstance(subject, str)
            or not _API_PRINCIPAL_ID.fullmatch(subject)
            or not isinstance(role, str)
            or role not in _API_PRINCIPAL_ROLES
            or not isinstance(token, str)
            or subject in _API_TOKEN_VARIABLES
            or not token.strip()
        ):
            raise ValueError(
                "Each API principal needs a valid subject, role, and token"
            )
        token = token.strip()
        if subject in subjects or token in tokens:
            raise ValueError("API principal subjects and tokens must be unique")
        subjects.add(subject)
        tokens.add(token)
        principals.append({"subject": subject, "role": role, "token": token})

    return principals


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

    checks: list[str] = [
        "HUEY_ENV",
        *PRODUCTION_REQUIRED_SECRET_VARIABLES,
        *DATABASE_PASSWORD_VARIABLES,
    ]
    if _vnc_enabled():
        checks.append("VNC_PASSWORD")

    issues: list[str] = []
    named_principals: list[dict[str, str]] = []
    raw_principals = os.getenv(_API_PRINCIPALS_VARIABLE, "").strip()
    if raw_principals:
        try:
            named_principals = parse_api_principals(raw_principals)
        except ValueError as exc:
            issues.append(str(exc))

    configured_tokens = {
        key: os.getenv(key, "").strip()
        for key in _API_TOKEN_VARIABLES
        if os.getenv(key, "").strip()
    }
    for principal in named_principals:
        configured_tokens[principal["subject"]] = principal["token"]

    if not configured_tokens:
        issues.append(
            "Configure an API credential with HUEY_API_TOKEN, "
            "HUEY_API_OPERATOR_TOKEN, HUEY_API_ADMIN_TOKEN, or "
            "HUEY_API_PRINCIPALS_JSON"
        )
    configured_token_values = list(configured_tokens.values())
    if any(
        hmac.compare_digest(token, previous)
        for index, token in enumerate(configured_token_values)
        for previous in configured_token_values[:index]
    ):
        issues.append("API credentials must be unique")
    for key, value in configured_tokens.items():
        if _looks_like_placeholder(value):
            issues.append(f"{key} uses a placeholder API credential")

    admin_tokens = [
        value
        for key, value in configured_tokens.items()
        if key == "HUEY_API_ADMIN_TOKEN"
        or any(
            p["subject"] == key and p["role"] == "admin"
            for p in named_principals
        )
    ]
    operator_tokens = [
        value
        for key, value in configured_tokens.items()
        if key in {"HUEY_API_TOKEN", "HUEY_API_OPERATOR_TOKEN"}
        or any(
            p["subject"] == key and p["role"] == "operator"
            for p in named_principals
        )
    ]
    if any(
        hmac.compare_digest(admin, operator)
        for admin in admin_tokens
        for operator in operator_tokens
    ):
        issues.append("Admin and operator-scoped API credentials must differ")

    for key in checks:
        value = os.getenv(key, "")
        if not value.strip() or _looks_like_placeholder(value):
            issues.append(f"{key} is missing, empty, or uses a placeholder value")

    if not issues:
        return

    if is_development:
        for issue in issues:
            warnings.warn(
                f"[huey-env-validation] {issue}", RuntimeWarning, stacklevel=2
            )
        return

    joined = "; ".join(issues)
    raise RuntimeError(
        f"Environment validation failed for HUEY_ENV='{env or 'unset'}': {joined}"
    )
