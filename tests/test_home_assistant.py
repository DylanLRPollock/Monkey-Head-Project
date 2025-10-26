# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Home Assistant module (tests)

from unittest.mock import patch

import pytest

pytest.importorskip("requests")

from monkey_head.services.home_assistant import call_service, get_state


class DummyResp:
    def __init__(self, payload=None):
        self.status_code = 200
        self._payload = payload or {}

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_call_service():
    with patch("requests.post", return_value=DummyResp({"ok": True})) as post:
        result = call_service(
            "light",
            "toggle",
            {"entity_id": "light.kitchen"},
            base_url="http://hass",
            token="abc",
        )
        post.assert_called_once()
        assert result == {"ok": True}


def test_get_state():
    with patch("requests.get", return_value=DummyResp({"state": "on"})) as get:
        result = get_state("light.kitchen", base_url="http://hass", token="abc")
        get.assert_called_once()
        assert result == {"state": "on"}
