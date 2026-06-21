from __future__ import annotations

import pytest

from huey.v1.response_bridge import ResponseBridge


def test_mock_response_is_offline() -> None:
    result = ResponseBridge().respond("hello")
    assert result.mode == "mock"
    assert "hello" in result.response


def test_api_mode_requires_environment(monkeypatch) -> None:
    monkeypatch.delenv("HUEY_RESPONSE_API_KEY", raising=False)
    with pytest.raises(RuntimeError):
        ResponseBridge("api").respond("hello")

