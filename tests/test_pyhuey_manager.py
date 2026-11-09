from __future__ import annotations

import logging

import pytest

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
    assert manager.integration_status()["prepared"] is False


def test_manager_exposes_and_invokes_registered_functions():
    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    manager = MonkeyManager(
        authorization_provider=lambda _operation, _capability: ("reader", False)
    )
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
    assert payload["paths"]["installer_target"] in {
        "windows",
        "macos",
        "debian",
        "linux",
    }
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
        assert (
            status["gui_state"]["tools"][0]["gui_payload"]["title"] == "Monkey Manager"
        )
    finally:
        shutdown_pyhuey()


def test_destructive_action_requires_explicit_intent(monkeypatch, caplog):
    from huey.pygpt_net.tools.manager import MonkeyManager

    manager = MonkeyManager()
    called = {"value": False}

    def _callback() -> None:
        called["value"] = True

    monkeypatch.setenv("HUEY_TOOL_ALLOW_DESTRUCTIVE", "1")
    with caplog.at_level(logging.WARNING):
        manager._run_destructive_action("cleanup_images", _callback)

    assert called["value"] is False
    assert "Blocked operation 'project.container.cleanup'" in caplog.text


def test_destructive_action_runs_with_admin_authorization_provider():
    from huey.pygpt_net.tools.manager import MonkeyManager

    manager = MonkeyManager(
        authorization_provider=lambda _operation, _capability: ("admin", True)
    )
    called = {"value": False}

    def _callback() -> None:
        called["value"] = True

    manager._run_destructive_action("cleanup_images", _callback)
    assert called["value"] is True


def test_manager_mutating_scripts_default_to_deny(monkeypatch):
    from unittest.mock import Mock

    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    monkeypatch.delenv("HUEY_TOOL_ALLOW_MUTATING", raising=False)
    manager = MonkeyManager()
    execute = Mock(side_effect=AssertionError("unexpected script execution"))
    monkeypatch.setattr(manager, "_execute_script", execute)

    manager.install()
    manager.update()
    manager.run_app()

    execute.assert_not_called()


def test_manager_mutating_container_action_requires_explicit_intent(monkeypatch):
    from unittest.mock import Mock

    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    manager = MonkeyManager()
    callback = Mock()
    monkeypatch.setenv("HUEY_TOOL_ALLOW_MUTATING", "1")
    assert manager._run_capability("project.container.start", callback) is False
    callback.assert_not_called()

    manager = MonkeyManager(
        authorization_provider=lambda _operation, _capability: ("operator", True)
    )
    assert manager._run_capability("project.container.start", callback) is True
    callback.assert_called_once_with()


def test_manager_dry_run_does_not_resolve_paths_or_request_authorization(monkeypatch):
    from unittest.mock import Mock

    import huey.connectors.pyhuey.tools.manager as manager_module
    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    setup_paths = Mock(side_effect=AssertionError("unexpected path access"))
    provider = Mock(side_effect=AssertionError("unexpected authorization prompt"))
    monkeypatch.setattr(manager_module, "resolve_platform_script_paths", setup_paths)
    manager = MonkeyManager(authorization_provider=provider)

    assert (
        manager._run_capability("project.container.start", Mock(), dry_run=True)
        is False
    )
    setup_paths.assert_not_called()
    provider.assert_not_called()


def test_mutating_registered_function_requires_authorized_role(monkeypatch):
    from unittest.mock import Mock

    import huey.connectors.pyhuey.tools.manager as manager_module
    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    invoke = Mock(return_value={"moved": ["file.txt"]})
    monkeypatch.setattr(manager_module, "invoke_function", invoke)
    denied = MonkeyManager()

    with pytest.raises(PermissionError, match="project.memory.auto_sort"):
        denied.invoke_registered_function("auto_sort_memory")
    invoke.assert_not_called()

    allowed = MonkeyManager(
        authorization_provider=lambda _operation, _capability: ("operator", True)
    )
    assert allowed.invoke_registered_function("auto_sort_memory") == {
        "moved": ["file.txt"]
    }
    invoke.assert_called_once_with("auto_sort_memory")


def test_manager_does_not_expose_unregistered_function_capabilities(monkeypatch):
    from unittest.mock import Mock

    import huey.connectors.pyhuey.tools.manager as manager_module
    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    invoke = Mock()
    monkeypatch.setattr(manager_module, "invoke_function", invoke)
    manager = MonkeyManager(
        authorization_provider=lambda _operation, _capability: ("admin", True)
    )

    with pytest.raises(PermissionError, match="not exposed"):
        manager.invoke_registered_function("unreviewed_function")
    invoke.assert_not_called()
