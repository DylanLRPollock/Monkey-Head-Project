"""Cover additional MainUI event, quick-access, and child-window branches."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from huey.memory.PY import main_ui
from huey.memory.PY.main_ui import MainUI


class _Value:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_quick_access_focus_selection_and_unhandled_action(monkeypatch):
    ui = MainUI.__new__(MainUI)
    calls = []
    ui.quick_access_entry = SimpleNamespace(focus_set=lambda: calls.append("focus"))
    assert MainUI._focus_quick_access(ui) == "break"
    assert calls == ["focus"]

    ui.quick_access_matches = []
    assert MainUI.launch_quick_access_selection(ui) == "break"

    ui.gui_action_map = {"action": SimpleNamespace(label="Action", description="desc")}
    ui.action_tab_ids = {}
    ui.surface_var = _Value()
    ui.workflow_hint_var = _Value()
    ui._action_handlers = lambda: {}
    MainUI._execute_gui_action(ui, "action")
    assert ui.surface_var.get() == "Action"
    assert ui.workflow_hint_var.get() == "desc"
    MainUI._execute_gui_action(ui, "missing")


def test_screen_prompt_noncustom_and_dark_theme_without_tk(monkeypatch):
    ui = MainUI.__new__(MainUI)
    monkeypatch.delenv("SCREEN_MODE", raising=False)
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(askstring=lambda *_args, **_kwargs: "1080p"),
    )
    assert MainUI.choose_screen_mode(ui) == "1080p"

    monkeypatch.setattr(main_ui, "tk", None)
    MainUI.apply_dark_theme(ui)


def test_tracking_methods_emit_events():
    ui = MainUI.__new__(MainUI)
    calls = []
    ui._emit_event = lambda *args, **kwargs: calls.append((args, kwargs))

    MainUI._track_started(ui, "Install", source="test", status="running")
    MainUI._track_finished(ui, source="test", status="complete")

    assert calls[0][0][0] == main_ui.EventType.RUN_STARTED
    assert calls[1][0][0] == main_ui.EventType.RUN_FINISHED


def test_data_summary_shows_counts_when_messagebox_exists(monkeypatch):
    ui = MainUI.__new__(MainUI)
    events = []
    ui.log_message = events.append
    ui._emit_event = lambda *_args, **_kwargs: None
    shown = []
    monkeypatch.setattr(
        main_ui, "preload_all", lambda: {"prompts": [1], "memory": {"x": [1, 2]}}
    )
    monkeypatch.setattr(
        main_ui,
        "messagebox",
        SimpleNamespace(showinfo=lambda *args: shown.append(args)),
    )

    MainUI.show_data_summary(ui)

    assert shown == [("Data Summary", "Prompts: 1\nMemory files: 2")]


def test_child_process_creation_flags_and_error_dialog(monkeypatch):
    ui = MainUI.__new__(MainUI)
    ui.project_root = Path("/tmp/project")
    ui.messages = []
    ui.finished = []
    ui.log_message = ui.messages.append
    ui._set_status = lambda _status: None
    ui._track_started = lambda *_args, **_kwargs: None
    ui._track_finished = lambda **kwargs: ui.finished.append(kwargs)
    monkeypatch.setattr(main_ui, "build_gui_process_command", lambda *_args: ["child"])
    monkeypatch.setattr(main_ui, "build_gui_process_env", lambda _root: {})
    monkeypatch.setattr(
        main_ui.subprocess, "CREATE_NEW_PROCESS_GROUP", 512, raising=False
    )
    calls = []
    monkeypatch.setattr(
        main_ui.subprocess,
        "Popen",
        lambda command, **kwargs: calls.append((command, kwargs)),
    )

    MainUI._launch_child_process(
        ui,
        label="Child",
        module_name="example.module",
        function_name="launch",
        source="test",
    )
    assert calls[0][1]["creationflags"] == 512

    errors = []
    monkeypatch.setattr(
        main_ui,
        "messagebox",
        SimpleNamespace(showerror=lambda *args: errors.append(args)),
    )
    monkeypatch.setattr(
        main_ui.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("denied")),
    )
    MainUI._launch_child_process(
        ui,
        label="Child",
        module_name="example.module",
        function_name="launch",
        source="test",
    )
    assert errors == [("Child", "denied")]
