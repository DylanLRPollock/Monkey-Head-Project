from __future__ import annotations

import logging

from huey.pyhuey_integration import prepare_pygpt, reset_pygpt_state


def test_monkey_manager_imports_without_full_pyside_stack():
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    manager = MonkeyManager()
    actions = manager.setup_menu()

    assert "monkey.gui.snapshot" in actions
    assert "monkey.paths.status" in actions
    assert "monkey.pyhuey.status" in actions
    assert "monkey.functions.list" in actions
    assert "monkey.system.check" in actions
    assert manager.integration_status()["prepared"] is True


def test_manager_exposes_and_invokes_registered_functions():
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    manager = MonkeyManager()
    functions = {item["name"]: item for item in manager.registered_functions()}

    assert "format_text" in functions
    assert (
        manager.invoke_registered_function(
            "format_text", text="alpha beta", line_length=20
        )
        == "alpha beta"
    )
    assert functions["list_available_pdfs"]["callable_without_arguments"] is True
    assert functions["format_text"]["parameters"][0]["name"] == "text"


def test_manager_gui_payload_groups_actions_and_paths():
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    manager = MonkeyManager()
    payload = manager.gui_payload()
    groups = {item["group"] for item in payload["action_groups"]}

    assert payload["title"] == "Monkey Manager"
    assert payload["paths"]["project_root"].endswith("Monkey-Head-Project")
    assert payload["paths"]["install"]["exists"] is True
    assert payload["paths"]["update"]["exists"] is True
    assert payload["paths"]["run"]["exists"] is True
    assert payload["integration"]["custom_function_count"] >= 4
    assert {"custom_functions", "docker", "integration", "kubernetes"} <= groups


def test_app_run_captures_gui_launch_state():
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    from huey.connectors.pyhuey.app import reset_last_launch_state, run
    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    reset_last_launch_state()
    state = run(tools=[MonkeyManager()])

    assert state["tool_count"] == 1
    assert state["tools"][0]["id"] == "monkey_manager"
    assert "monkey.gui.snapshot" in state["tools"][0]["menu_actions"]
    assert state["tools"][0]["menu_labels"]["monkey.paths.status"] == "Project Paths"
    assert state["tools"][0]["gui_payload"]["title"] == "Monkey Manager"


def test_adapter_status_includes_gui_state():
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    from huey.connectors.pyhuey.adapter import launch_pyhuey, shutdown_pyhuey
    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    try:
        status = launch_pyhuey(tools=[MonkeyManager()])
        assert status["running"] is True
        assert status["gui_state"]["tool_count"] == 1
        assert status["gui_state"]["tools"][0]["gui_payload"]["title"] == "Monkey Manager"
    finally:
        shutdown_pyhuey()


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
