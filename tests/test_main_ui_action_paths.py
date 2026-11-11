"""Cover launcher action dispatch and subprocess result handling."""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

from huey.memory.PY import main_ui
from huey.memory.PY.main_ui import MainUI


class _Var:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _Listbox:
    def __init__(self, selection=()):
        self.items = []
        self.selected = selection

    def delete(self, *_args):
        self.items.clear()

    def insert(self, _index, value):
        self.items.append(value)

    def selection_set(self, index):
        self.selected = (index,)

    def curselection(self):
        return self.selected


def test_quick_access_refresh_selection_and_focus(monkeypatch):
    action = SimpleNamespace(
        id="license",
        label="License",
        launch_mode="new-window",
        description="Read the license",
    )
    monkeypatch.setattr(
        main_ui, "search_gui_actions", lambda query, _actions: [action] if query else []
    )
    ui = MainUI.__new__(MainUI)
    ui.quick_access_var = _Var("license")
    ui.gui_actions = [action]
    ui.action_tab_titles = {"license": "Help"}
    ui.quick_access_listbox = _Listbox()
    ui.quick_access_entry = SimpleNamespace(
        focused=False,
        focus_set=lambda: setattr(ui.quick_access_entry, "focused", True),
        selection_range=lambda *_a: None,
    )
    ui.quick_access_matches = []
    MainUI.refresh_quick_access_results(ui)
    assert ui.quick_access_listbox.items == ["License | New Window | Help"]
    assert ui.quick_access_listbox.selected == (0,)

    calls = []
    ui._execute_gui_action = calls.append
    assert MainUI.launch_quick_access_selection(ui) == "break"
    assert calls == ["license"]
    ui.quick_access_listbox.selected = (0,)
    ui.quick_access_matches = [action]
    assert MainUI.launch_quick_access_selection(ui) == "break"
    assert calls == ["license", "license"]
    assert MainUI._focus_quick_access(ui) == "break"
    assert ui.quick_access_entry.focused is True
    MainUI.clear_quick_access(ui)
    assert ui.quick_access_var.get() == ""


def test_execute_gui_action_updates_surface_and_runs_handler():
    ui = MainUI.__new__(MainUI)
    action = SimpleNamespace(label="Project", description="Project details")
    ui.gui_action_map = {"project": action}
    ui.action_tab_ids = {"project": "runtime"}
    ui.surface_var = _Var()
    ui.workflow_hint_var = _Var()
    called = []
    ui.select_tab = called.append
    ui._action_handlers = lambda: {"project": lambda: called.append("handler")}
    MainUI._execute_gui_action(ui, "missing")
    assert called == []
    MainUI._execute_gui_action(ui, "project")
    assert ui.surface_var.get() == "Project"
    assert ui.workflow_hint_var.get() == "Project details"
    assert called == ["runtime", "handler"]


def test_navigation_shortcuts_tabs_and_empty_quick_access(monkeypatch):
    monkeypatch.setattr(main_ui, "tk", SimpleNamespace(END="end"))
    ui = MainUI.__new__(MainUI)
    ui.quick_access_var = _Var("none")
    ui.gui_actions = []
    ui.quick_access_matches = []
    ui.quick_access_entry = None
    ui.quick_access_listbox = _Listbox()
    MainUI.refresh_quick_access_results(ui)
    assert ui.quick_access_listbox.items == []
    assert MainUI.launch_quick_access_selection(ui) == "break"
    assert MainUI._focus_quick_access(ui) == "break"

    ui.surface_tab_frames = {}
    ui.surface_var = _Var()
    ui.surface_tab_titles = {}
    ui.state = SimpleNamespace(operator=SimpleNamespace(active_view="initial"))
    ui.surface_notebook = None
    MainUI.select_tab(ui, "missing")
    MainUI._on_tab_changed(ui)
    assert ui.state.operator.active_view == "initial"

    ui.root = object()
    MainUI._bind_navigation_shortcuts(ui)

    bindings = {}
    ui.root = SimpleNamespace(
        bind_all=lambda key, callback: bindings.__setitem__(key, callback)
    )
    ui.select_tab = lambda tab_id: bindings.setdefault("selected", []).append(tab_id)
    MainUI._bind_navigation_shortcuts(ui)
    assert set(bindings) >= {"<Control-k>", "<Control-K>", "<Control-Key-1>"}
    bindings["<Control-Key-1>"](None)
    bindings["<Control-Key-2>"](None)
    bindings["<Control-Key-3>"](None)
    assert bindings["selected"] == [
        "launch-pad",
        "connectors-and-windows",
        "runtime-ops",
    ]


def test_focus_action_and_tab_changed_update_state():
    ui = MainUI.__new__(MainUI)
    ui.surface_var = _Var()
    ui.workflow_hint_var = _Var()
    called = []
    callback = MainUI._focus_action(
        ui, "Details", "Action help", lambda: called.append(True)
    )
    callback()
    assert (ui.surface_var.get(), ui.workflow_hint_var.get(), called) == (
        "Details",
        "Action help",
        [True],
    )

    ui.surface_notebook = SimpleNamespace(
        select=lambda: "frame", tab=lambda _frame, _key: "Runtime & Ops"
    )
    ui.state = SimpleNamespace(operator=SimpleNamespace(active_view=""))
    MainUI._on_tab_changed(ui)
    assert ui.surface_var.get() == "Runtime & Ops"
    assert ui.state.operator.active_view == "runtime-ops"


def test_fallback_gui_reporting_and_close(monkeypatch):
    events = []
    ui = MainUI.__new__(MainUI)
    ui._run_on_ui = lambda callback: callback()
    ui.log_message = events.append
    errors = []
    monkeypatch.setattr(
        main_ui,
        "messagebox",
        SimpleNamespace(showerror=lambda *args: errors.append(args)),
    )

    MainUI._launch_child_gui(ui, lambda: None, "Good GUI")
    MainUI._launch_child_gui(
        ui,
        lambda: (_ for _ in ()).throw(RuntimeError("missing display")),
        "Broken GUI",
    )
    assert events == ["Broken GUI failed: missing display"]
    assert errors == [("Broken GUI", "missing display")]

    shutdowns = []
    destroyed = []
    ui.executor = SimpleNamespace(shutdown=lambda **kwargs: shutdowns.append(kwargs))
    ui.root = SimpleNamespace(destroy=lambda: destroyed.append(True))
    MainUI.on_close(ui)
    assert shutdowns == [{"wait": False}]
    assert destroyed == [True]
    del ui.executor
    MainUI.on_close(ui)
    assert destroyed == [True, True]


def test_primary_launcher_actions_schedule_the_expected_script(monkeypatch):
    ui = MainUI.__new__(MainUI)
    events = []
    ui.install_path = "install"
    ui.update_path = "update"
    ui.run_path = "run"
    ui.log_message = events.append
    ui._set_status = events.append
    ui._start_progress = lambda: events.append("progress")
    ui._track_started = lambda label, **kwargs: events.append((label, kwargs["status"]))
    ui._submit_task = lambda *args: events.append(args[1:])
    MainUI.install(ui)
    MainUI.run(ui)
    MainUI.update(ui)
    assert ("install", "Install", "launch-pad") in events
    assert ("run", "Run", "launch-pad") in events
    assert ("update", "Update", "launch-pad") in events


@pytest.mark.parametrize(
    ("method", "label", "module_name", "function_name", "source"),
    [
        (
            "launch_simple_chat",
            "Simple Chat",
            "huey.simple_chat_gui",
            "run_simple_chat",
            "chat",
        ),
        (
            "launch_ai_tools",
            "AI Console",
            "huey.memory.PY.ai_tools_gui",
            "run_ai_tools",
            "ai-console",
        ),
        (
            "launch_dashboard",
            "Dashboard",
            "huey.memory.PY.dashboard",
            "launch_dashboard",
            "dashboard",
        ),
    ],
)
def test_child_gui_launch_methods_set_hints_and_targets(
    monkeypatch, method, label, module_name, function_name, source
):
    ui = MainUI.__new__(MainUI)
    ui.workflow_hint_var = _Var()
    calls = []
    ui._launch_child_process = lambda **kwargs: calls.append(kwargs)
    getattr(MainUI, method)(ui)
    assert ui.workflow_hint_var.get()
    assert calls[0]["label"] == label
    assert calls[0]["module_name"] == module_name
    assert calls[0]["function_name"] == function_name
    assert calls[0]["source"] == source


@pytest.mark.parametrize(
    ("return_code", "expected_status"), [(0, "install complete"), (4, "install failed")]
)
def test_run_script_captures_output_and_finalizes_status(
    monkeypatch, tmp_path, return_code, expected_status
):
    script = tmp_path / "install.py"
    script.touch()
    events = []
    ui = MainUI.__new__(MainUI)
    ui.log_message = events.append
    ui._track_finished = lambda **kwargs: events.append(kwargs["status"])
    ui._stop_progress = lambda: events.append("stopped")
    ui._set_status = events.append
    monkeypatch.setattr(
        main_ui, "build_platform_script_command", lambda path: [str(path)]
    )

    class Process:
        stdout = io.StringIO("line one\nline two\n")
        returncode = return_code

        def wait(self):
            return return_code

    monkeypatch.setattr(main_ui.subprocess, "Popen", lambda *_a, **_kwargs: Process())
    MainUI.run_script(ui, script, "Install", "launch-pad")
    assert "line one\n" in events
    assert expected_status in events
    assert events[-2:] == ["stopped", "Status: Ready"]


def test_run_script_missing_path_and_process_exception(monkeypatch, tmp_path):
    events = []
    ui = MainUI.__new__(MainUI)
    ui.log_message = events.append
    ui._track_finished = lambda **kwargs: events.append(kwargs["status"])
    ui._stop_progress = lambda: events.append("stopped")
    ui._set_status = events.append
    ui._run_on_ui = lambda callback: callback()
    monkeypatch.setattr(
        main_ui, "messagebox", SimpleNamespace(showerror=lambda *_a: None)
    )
    MainUI.run_script(ui, tmp_path / "missing", "Run", "launch-pad")
    assert any("Script not found" in item for item in events)
    assert "run unavailable" in events

    events.clear()
    script = tmp_path / "run.py"
    script.touch()
    monkeypatch.setattr(main_ui, "build_platform_script_command", lambda _path: ["cmd"])
    monkeypatch.setattr(
        main_ui.subprocess,
        "Popen",
        lambda *_a, **_kwargs: (_ for _ in ()).throw(OSError("spawn failed")),
    )
    MainUI.run_script(ui, script, "Run", "launch-pad")
    assert "Exception: spawn failed" in events
    assert "run error" in events


def test_launch_child_process_success_and_fallback(monkeypatch, tmp_path):
    events = []
    ui = MainUI.__new__(MainUI)
    ui.project_root = tmp_path
    ui.log_message = events.append
    ui._set_status = events.append
    ui._track_started = lambda *a, **kwargs: events.append(kwargs["status"])
    ui._track_finished = lambda **kwargs: events.append(kwargs["status"])
    ui._launch_child_gui = lambda fallback, label: events.append(
        ("fallback", label, fallback())
    )
    monkeypatch.setattr(
        main_ui, "messagebox", SimpleNamespace(showerror=lambda *_a: None)
    )
    monkeypatch.setattr(main_ui, "build_gui_process_command", lambda *args: list(args))
    monkeypatch.setattr(
        main_ui, "build_gui_process_env", lambda _root: {"PATH": "/bin"}
    )
    launched = []
    monkeypatch.setattr(
        main_ui.subprocess,
        "Popen",
        lambda command, **kwargs: launched.append((command, kwargs)),
    )
    MainUI._launch_child_process(
        ui,
        label="Dashboard",
        module_name="huey.dashboard",
        function_name="main",
        source="dashboard",
    )
    assert launched[0][0] == ["huey.dashboard", "main"]
    assert launched[0][1]["cwd"] == str(tmp_path)
    assert "dashboard ready" in events

    launched.clear()
    fallback_calls = []

    def fallback():
        fallback_calls.append("fallback")

    monkeypatch.setattr(
        main_ui.subprocess,
        "Popen",
        lambda *_a, **_kwargs: (_ for _ in ()).throw(OSError("spawn failed")),
    )
    MainUI._launch_child_process(
        ui,
        label="Chat",
        module_name="huey.chat",
        function_name="main",
        source="chat",
        fallback=fallback,
    )
    assert fallback_calls == ["fallback"]
    assert "chat failed" in events
