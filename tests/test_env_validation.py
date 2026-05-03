from __future__ import annotations

import pytest

from huey.memory.PY.env_validation import validate_security_sensitive_environment


@pytest.fixture(autouse=True)
def _clear_env(monkeypatch):
    for key in (
        "HUEY_ENV",
        "HUEY_API_TOKEN",
        "DB_PASSWORD",
        "DATABASE_PASSWORD",
        "POSTGRES_PASSWORD",
        "MYSQL_PASSWORD",
        "HUEY_VNC_ENABLED",
        "VNC_PASSWORD",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


def test_production_fails_when_required_secrets_missing(monkeypatch):
    monkeypatch.setenv("HUEY_ENV", "production")
    monkeypatch.setenv("HUEY_API_TOKEN", "real-token")
    monkeypatch.setenv("DB_PASSWORD", "db-pass")
    monkeypatch.setenv("OPENAI_API_KEY", "change-me")

    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        validate_security_sensitive_environment()


def test_production_requires_vnc_password_when_vnc_enabled(monkeypatch):
    monkeypatch.setenv("HUEY_ENV", "staging")
    monkeypatch.setenv("HUEY_API_TOKEN", "real-token")
    monkeypatch.setenv("DB_PASSWORD", "db-pass")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("HUEY_VNC_ENABLED", "true")

    with pytest.raises(RuntimeError, match="VNC_PASSWORD"):
        validate_security_sensitive_environment()


def test_development_warns_instead_of_failing(monkeypatch):
    monkeypatch.setenv("HUEY_ENV", "development")

    with pytest.warns(RuntimeWarning, match="HUEY_API_TOKEN"):
        validate_security_sensitive_environment()


def test_production_passes_with_required_values(monkeypatch):
    monkeypatch.setenv("HUEY_ENV", "production")
    monkeypatch.setenv("HUEY_API_TOKEN", "real-token")
    monkeypatch.setenv("DB_PASSWORD", "db-pass")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    validate_security_sensitive_environment()
