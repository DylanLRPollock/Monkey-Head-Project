"""Focused flow tests for the maintained Tk launcher."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from huey.memory.PY import main_ui
from huey.memory.PY.main_ui import MainUI


def _make_var() -> tuple[SimpleNamespace, dict[str, str]]:
    state: dict[str, str] = {}
    return (
        SimpleNamespace(set=lambda value: state.setdefault("value", value)),
        state,
    )


def test_check_license_uses_acceptance_gate() -> None:
    ui = MainUI.__new__(MainUI)

    with patch.object(main_ui, "show_license_gui") as gui_call:
        MainUI.check_license(ui)

    gui_call.assert_called_once_with()


def test_show_license_forces_manual_review() -> None:
    ui = MainUI.__new__(MainUI)
    surface_var, surface_state = _make_var()
    workflow_var, workflow_state = _make_var()
    ui.surface_var = surface_var
    ui.workflow_hint_var = workflow_var
    ui.log_message = lambda *_args, **_kwargs: None
    ui._track_finished = lambda **_kwargs: None

    with patch.object(main_ui, "show_license_gui") as gui_call:
        MainUI.show_license(ui)

    gui_call.assert_called_once_with(force_show=True)
    assert surface_state["value"] == "License"
    assert "license terms" in workflow_state["value"].lower()


def test_launch_install_gui_uses_child_process() -> None:
    ui = MainUI.__new__(MainUI)
    workflow_var, workflow_state = _make_var()
    ui.workflow_hint_var = workflow_var

    with patch.object(MainUI, "_launch_child_process") as launcher:
        MainUI.launch_install_gui(ui)

    launcher.assert_called_once_with(
        label="Graphical Installer",
        module_name="huey.install_gui",
        function_name="launch_install_gui",
        source="installer",
        fallback=main_ui.launch_graphical_install,
    )
    assert "installer opens separately" in workflow_state["value"].lower()


def test_launch_command_center_uses_browser_child_process() -> None:
    ui = MainUI.__new__(MainUI)
    workflow_var, workflow_state = _make_var()
    ui.workflow_hint_var = workflow_var

    with patch.object(MainUI, "_launch_child_process") as launcher:
        MainUI.launch_command_center(ui)

    launcher.assert_called_once_with(
        label="Command Center",
        module_name="huey.apps.command_center.cli",
        function_name="open_command_center",
        source="command-center",
        fallback=main_ui.open_command_center,
    )
    assert "browser" in workflow_state["value"].lower()


def test_launch_quick_access_selection_runs_selected_action() -> None:
    ui = MainUI.__new__(MainUI)
    surface_var, surface_state = _make_var()
    workflow_var, workflow_state = _make_var()
    action = main_ui.action_lookup(main_ui.default_gui_actions())["command-center"]
    called: dict[str, object] = {}

    ui.gui_action_map = {action.id: action}
    ui.action_tab_ids = {action.id: "connectors-and-windows"}
    ui.quick_access_matches = [action]
    ui.quick_access_listbox = SimpleNamespace(curselection=lambda: (0,))
    ui.surface_var = surface_var
    ui.workflow_hint_var = workflow_var
    ui.select_tab = lambda tab_id: called.setdefault("tab", tab_id)

    with patch.object(
        MainUI,
        "_action_handlers",
        return_value={action.id: lambda: called.setdefault("ran", True)},
    ):
        MainUI.launch_quick_access_selection(ui)

    assert called["tab"] == "connectors-and-windows"
    assert called["ran"] is True
    assert surface_state["value"] == "Command Center"
    assert "browser" in workflow_state["value"].lower()
