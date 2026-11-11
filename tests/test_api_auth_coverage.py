"""Exercise API credential parsing and least-privilege enforcement."""

from __future__ import annotations

import importlib
import json
import sys
import warnings

import pytest
from fastapi import HTTPException
from starlette.requests import Request

sys.modules.setdefault(
    "huey.os.core.resilience", importlib.import_module("huey.core.resilience")
)
sys.modules.setdefault(
    "huey.os.core.task_scheduler",
    importlib.import_module("huey.core.task_scheduler"),
)
with warnings.catch_warnings():
    warnings.filterwarnings(
        "ignore", message=r"\[huey-env-validation\]", category=RuntimeWarning
    )
    api = importlib.import_module("huey.memory.PY.api")


def _request(authorization: str = "", client: tuple[str, int] = ("127.0.0.1", 1234)):
    headers = [] if not authorization else [(b"authorization", authorization.encode())]
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/admin",
            "raw_path": b"/admin",
            "query_string": b"",
            "headers": headers,
            "client": client,
            "server": ("test", 80),
        }
    )


def _clear_api_credentials(monkeypatch):
    for name in (
        "HUEY_API_TOKEN",
        "HUEY_API_OPERATOR_TOKEN",
        "HUEY_API_ADMIN_TOKEN",
        "HUEY_API_PRINCIPALS_JSON",
    ):
        monkeypatch.delenv(name, raising=False)


def test_configured_tokens_merge_legacy_scoped_and_named_credentials(monkeypatch):
    _clear_api_credentials(monkeypatch)
    monkeypatch.setenv("HUEY_API_OPERATOR_TOKEN", "operator")
    monkeypatch.setenv("HUEY_API_ADMIN_TOKEN", "admin")
    monkeypatch.setenv("HUEY_API_TOKEN", "legacy")
    monkeypatch.setenv(
        "HUEY_API_PRINCIPALS_JSON",
        json.dumps([{"subject": "sensor-1", "role": "operator", "token": "sensor"}]),
    )
    assert api._configured_api_tokens() == {
        "admin": ["admin"],
        "operator": ["operator", "legacy", "sensor"],
    }


@pytest.mark.parametrize(
    ("environment", "credentials", "message"),
    [
        (
            {"HUEY_API_TOKEN": "same", "HUEY_API_ADMIN_TOKEN": "same"},
            None,
            "must be distinct",
        ),
        (
            {"HUEY_API_OPERATOR_TOKEN": "shared"},
            [{"subject": "agent", "role": "operator", "token": "shared"}],
            "must be unique",
        ),
    ],
)
def test_duplicate_credentials_are_rejected(
    monkeypatch, environment, credentials, message
):
    _clear_api_credentials(monkeypatch)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    if credentials is not None:
        monkeypatch.setenv("HUEY_API_PRINCIPALS_JSON", json.dumps(credentials))
    with pytest.raises(RuntimeError, match=message):
        api._configured_api_tokens()


def test_request_authentication_handles_scheme_named_and_shared_tokens(monkeypatch):
    _clear_api_credentials(monkeypatch)
    monkeypatch.setenv("HUEY_API_OPERATOR_TOKEN", "operator-secret")
    monkeypatch.setenv(
        "HUEY_API_PRINCIPALS_JSON",
        json.dumps(
            [{"subject": "sensor-1", "role": "operator", "token": "sensor-secret"}]
        ),
    )
    assert api._authenticate_api_request(_request("Basic operator-secret")) is None
    named = api._authenticate_api_request(_request("Bearer sensor-secret"))
    assert (named.subject, named.role, named.identity_type) == (
        "sensor-1",
        "operator",
        "named-credential",
    )
    shared = api._authenticate_api_request(_request("Bearer operator-secret"))
    assert (shared.subject, shared.role, shared.identity_type) == (
        "shared:operator",
        "operator",
        "shared-credential",
    )
    assert api._authenticate_api_request(_request("Bearer wrong")) is None


def test_strong_and_admin_auth_enforce_role_and_dev_loopback(monkeypatch):
    _clear_api_credentials(monkeypatch)
    with pytest.raises(HTTPException) as missing:
        api.require_strong_api_auth(_request())
    assert missing.value.status_code == 401

    monkeypatch.setenv("HUEY_API_OPERATOR_TOKEN", "operator")
    with pytest.raises(HTTPException) as invalid:
        api.require_strong_api_auth(_request("Bearer wrong"))
    assert invalid.value.status_code == 401
    request = _request("Bearer operator")
    assert api.require_strong_api_auth(request) == "operator"
    assert request.state.api_principal.subject == "shared:operator"
    with pytest.raises(HTTPException) as forbidden:
        api.require_admin_api_auth(_request("Bearer operator"))
    assert forbidden.value.status_code == 403

    _clear_api_credentials(monkeypatch)
    assert api.require_admin_api_auth(_request()) == "admin"
    with pytest.raises(HTTPException) as remote:
        api.require_admin_api_auth(_request(client=("203.0.113.4", 1234)))
    assert remote.value.status_code == 401


def test_unsafe_task_policy_distinguishes_explicit_and_development_access(monkeypatch):
    _clear_api_credentials(monkeypatch)
    for value in ("1", "true", "yes", "on", " TRUE "):
        monkeypatch.setenv("HUEY_ENABLE_UNSAFE_TASKS", value)
        assert api._unsafe_task_submission_enabled()
    monkeypatch.setenv("HUEY_ENABLE_UNSAFE_TASKS", "no")
    assert not api._unsafe_task_submission_enabled()

    _clear_api_credentials(monkeypatch)
    monkeypatch.delenv("HUEY_ENABLE_UNSAFE_TASKS", raising=False)
    with pytest.raises(HTTPException) as local_disabled:
        api._require_unsafe_task_submission_access(_request())
    assert local_disabled.value.status_code == 403
    with pytest.raises(HTTPException) as remote:
        api._require_unsafe_task_submission_access(_request(client=("203.0.113.9", 80)))
    assert remote.value.status_code == 403

    monkeypatch.setenv("HUEY_API_OPERATOR_TOKEN", "operator")
    monkeypatch.setattr(api, "_configured_environment", lambda: "development")
    api._require_unsafe_task_submission_access(_request(client=("203.0.113.9", 80)))
