"""Focused flow tests for the maintained Tk launcher."""

from __future__ import annotations

import io
from types import SimpleNamespace
from unittest.mock import patch

import pytest

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


def _ui_var(value=""):
    var = SimpleNamespace(value=value)
    var.set = lambda new_value: setattr(var, "value", new_value)
    var.get = lambda: var.value
    return var


def _script_ui():
    ui = MainUI.__new__(MainUI)
    ui.messages = []
    ui.finished = []
    ui.statuses = []
    ui.progress_stops = 0
    ui.log_message = ui.messages.append
    ui._track_finished = lambda **kwargs: ui.finished.append(kwargs)
    ui._stop_progress = lambda: setattr(ui, "progress_stops", ui.progress_stops + 1)
    ui._set_status = ui.statuses.append
    return ui


@pytest.mark.parametrize(
    ("returncode", "expected_status"),
    [(0, "install complete"), (3, "install failed")],
)
def test_run_script_records_process_output_and_exit_status(
    tmp_path, monkeypatch, returncode, expected_status
):
    script = tmp_path / "installer.sh"
    script.write_text("#!/bin/sh\n")
    process = SimpleNamespace(
        stdout=io.StringIO("first line\nsecond line\n"),
        returncode=returncode,
        wait=lambda: None,
    )
    monkeypatch.setattr(
        main_ui, "build_platform_script_command", lambda _path: ["fake"]
    )
    monkeypatch.setattr(main_ui.subprocess, "Popen", lambda *_args, **_kwargs: process)
    ui = _script_ui()

    MainUI.run_script(ui, script, "Install", "launch-pad")

    assert ui.messages[:2] == ["first line\n", "second line\n"]
    assert ui.finished == [{"source": "launch-pad", "status": expected_status}]
    assert ui.progress_stops == 1
    assert ui.statuses == ["Status: Ready"]
    assert process.stdout.closed


def test_run_script_handles_missing_path_and_process_start_error(tmp_path, monkeypatch):
    monkeypatch.setattr(main_ui, "messagebox", None)
    ui = _script_ui()
    MainUI.run_script(ui, None, "Run", "launch-pad")
    assert "Script not found" in ui.messages[0]
    assert ui.finished[-1]["status"] == "run unavailable"
    assert ui.statuses[-1] == "Status: Ready"

    script = tmp_path / "run.sh"
    script.write_text("#!/bin/sh\n")
    monkeypatch.setattr(
        main_ui.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("launch failed")),
    )
    MainUI.run_script(ui, script, "Run", "launch-pad")
    assert "Exception: launch failed" in ui.messages[-1]
    assert ui.finished[-1]["status"] == "run error"
    assert ui.progress_stops == 2


def test_main_ui_confirmation_blocks_without_dialog_and_passes_consequence():
    ui = _script_ui()
    monkeypatch_context = patch.object(main_ui, "messagebox", None)
    with monkeypatch_context:
        assert not MainUI._confirm_container_operation(
            ui, "delete data", destructive=True
        )
    assert "Blocked delete data" in ui.messages[-1]

    with patch.object(main_ui, "messagebox") as dialog:
        dialog.askyesno.return_value = True
        assert MainUI._confirm_container_operation(ui, "start service")
        assert MainUI._confirm_container_operation(
            ui, "delete service", destructive=True
        )
    assert "local project or cluster state" in dialog.askyesno.call_args_list[0].args[1]
    assert "remove resources" in dialog.askyesno.call_args_list[1].args[1]


def test_main_ui_paths_and_ui_thread_helpers():
    ui = MainUI.__new__(MainUI)
    assert MainUI._display_path(None) == "Unavailable on this platform"
    assert MainUI._display_path(main_ui.Path("/opt/huey/run.sh")) == "/opt/huey/run.sh"

    called = []
    ui.root = SimpleNamespace(
        after=lambda delay, callback: called.append((delay, callback))
    )
    MainUI._run_on_ui(ui, lambda: called.append("ran"))
    assert called[0][0] == 0
    called[0][1]()
    assert called[-1] == "ran"

    ui.root = object()
    MainUI._run_on_ui(ui, lambda: called.append("direct"))
    assert called[-1] == "direct"


def test_main_ui_refresh_quick_access_and_empty_selection(monkeypatch):
    ui = MainUI.__new__(MainUI)
    ui.quick_access_var = _ui_var("missing action")
    ui.gui_actions = main_ui.default_gui_actions()
    ui.quick_access_matches = list(ui.gui_actions)
    ui.quick_access_listbox = None
    MainUI.refresh_quick_access_results(ui)
    assert ui.quick_access_matches == []
    assert MainUI.launch_quick_access_selection(ui) == "break"

    ui.quick_access_var = _ui_var("license")
    calls = []
    ui.action_tab_titles = {}
    ui.quick_access_listbox = SimpleNamespace(
        delete=lambda *args: calls.append(("delete", args)),
        insert=lambda *args: calls.append(("insert", args)),
        selection_set=lambda *args: calls.append(("select", args)),
    )
    MainUI.refresh_quick_access_results(ui)
    assert calls[0][0] == "delete"
    assert any(call[0] == "insert" for call in calls)
    assert calls[-1] == ("select", (0,))


def test_main_ui_execute_unknown_and_known_actions():
    ui = MainUI.__new__(MainUI)
    ui.gui_action_map = {}
    ui.action_tab_ids = {}
    MainUI._execute_gui_action(ui, "missing")

    action = main_ui.action_lookup(main_ui.default_gui_actions())["license"]
    ui.gui_action_map = {action.id: action}
    ui.action_tab_ids = {action.id: "runtime-ops"}
    ui.surface_var = _ui_var()
    ui.workflow_hint_var = _ui_var()
    selected = []
    ui.select_tab = selected.append
    ran = []
    ui._action_handlers = lambda: {action.id: lambda: ran.append(True)}
    MainUI._execute_gui_action(ui, action.id)
    assert selected == ["runtime-ops"]
    assert ui.surface_var.get() == action.label
    assert ui.workflow_hint_var.get() == action.description
    assert ran == [True]
