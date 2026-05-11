from __future__ import annotations

import logging

from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state


def test_monkey_manager_imports_without_full_pyside_stack():
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    from huey.pygpt_net.tools.manager import MonkeyManager

    manager = MonkeyManager()
    actions = manager.setup_menu()

    assert "monkey.pyhuey.status" in actions
    assert "monkey.system.check" in actions
    assert manager.integration_status()["prepared"] is True


def test_destructive_action_requires_explicit_intent(monkeypatch, caplog):
    from huey.pygpt_net.tools.manager import MonkeyManager

    manager = MonkeyManager()
    called = {"value": False}

    def _callback() -> None:
        called["value"] = True

    monkeypatch.delenv("HUEY_TOOL_ALLOW_DESTRUCTIVE", raising=False)
    with caplog.at_level(logging.WARNING):
        manager._run_destructive_action("cleanup_images", _callback)

    assert called["value"] is False
    assert "Blocked destructive action 'cleanup_images'" in caplog.text


def test_destructive_action_runs_when_intent_is_explicit(monkeypatch):
    from huey.pygpt_net.tools.manager import MonkeyManager

    manager = MonkeyManager()
    called = {"value": False}

    def _callback() -> None:
        called["value"] = True

    monkeypatch.setenv("HUEY_TOOL_ALLOW_DESTRUCTIVE", "1")
    manager._run_destructive_action("cleanup_images", _callback)
    assert called["value"] is True
