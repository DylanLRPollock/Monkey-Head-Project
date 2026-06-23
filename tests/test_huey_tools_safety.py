from __future__ import annotations

import json

import pytest

from huey.connectors.pyhuey.plugin.huey_tools.safety import (
    assert_action_allowed,
    blocked_actions,
    default_safety_policy,
    is_action_allowed,
    policy_to_dict,
)


def test_default_policy_blocks_dangerous_actions() -> None:
    policy = default_safety_policy()
    blocked = blocked_actions(policy)

    assert "hardware_control" in blocked
    assert "governance_mutation" in blocked
    assert "overwrite" in blocked


def test_allowed_actions_pass() -> None:
    policy = default_safety_policy()

    assert is_action_allowed("status", policy) is True
    assert is_action_allowed("ffmpeg_validate", policy) is True
    assert is_action_allowed("audio_prepare", policy) is True


def test_assert_action_allowed_raises_for_blocked_action() -> None:
    with pytest.raises(PermissionError):
        assert_action_allowed("hardware_control")


def test_policy_to_dict_is_json_safe() -> None:
    payload = policy_to_dict()

    assert payload["allow_shell"] is False
    json.dumps(payload, sort_keys=True)
