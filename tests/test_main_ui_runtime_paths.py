"""Test side-effecting MainUI paths without opening a real desktop window."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from huey.memory.PY import main_ui
from huey.memory.PY.main_ui import MainUI


class _Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def _ui():
    ui = MainUI.__new__(MainUI)
    ui.messages = []
    ui.finished = []
    ui.started = []
    ui.statuses = []
    ui.progress_starts = 0
    ui.progress_stops = 0
    ui.log_message = ui.messages.append
    ui._track_started = lambda *args, **kwargs: ui.started.append((args, kwargs))
    ui._track_finished = lambda **kwargs: ui.finished.append(kwargs)
    ui._set_status = ui.statuses.append
    ui._start_progress = lambda: setattr(ui, "progress_starts", ui.progress_starts + 1)
    ui._stop_progress = lambda: setattr(ui, "progress_stops", ui.progress_stops + 1)
    ui.workflow_hint_var = _Var()
    ui.surface_var = _Var()
    return ui


def test_child_process_success_and_fallback_are_tracked(monkeypatch):
    ui = _ui()
    ui.project_root = Path("/tmp/project")
    monkeypatch.setattr(main_ui, "build_gui_process_command", lambda *_args: ["child"])
    monkeypatch.setattr(
        main_ui, "build_gui_process_env", lambda _root: {"MODE": "test"}
    )
    monkeypatch.setattr(main_ui.subprocess, "Popen", lambda *_args, **_kwargs: object())

    MainUI._launch_child_process(
        ui,
        label="Test Child",
        module_name="test.module",
        function_name="launch",
        source="test",
    )
    assert "Test Child opened" in ui.messages[-1]
    assert ui.finished[-1] == {"source": "test", "status": "test child ready"}

    fallback = object()
    monkeypatch.setattr(
        main_ui.subprocess,
        "Popen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("spawn denied")),
    )
    launched = []
    ui._launch_child_gui = lambda function, label: launched.append((function, label))
    monkeypatch.setattr(main_ui, "messagebox", None)
    MainUI._launch_child_process(
        ui,
        label="Fallback Child",
        module_name="test.module",
        function_name="launch",
        source="test",
        fallback=fallback,
    )
    assert launched == [(fallback, "Fallback Child")]
    assert ui.finished[-1]["status"] == "fallback child failed"
    assert any("spawn denied" in message for message in ui.messages)


def test_background_container_media_and_pod_operations_report_results(monkeypatch):
    ui = _ui()
    calls = []
    MainUI._run_container_func(
        ui,
        lambda *args, **kwargs: calls.append((args, kwargs)),
        "Build Image",
        "runtime",
        "image-name",
        confirmed=True,
        actor_role="operator",
    )
    assert calls == [(("image-name",), {"confirmed": True, "actor_role": "operator"})]
    assert ui.finished[-1]["status"] == "build image complete"
    assert ui.statuses[-1] == "Status: Ready"

    def fail(*_args, **_kwargs):
        raise RuntimeError("container failure")

    MainUI._run_container_func(ui, fail, "Stop", "runtime", confirmed=True)
    assert "Exception: container failure" in ui.messages[-1]
    assert ui.finished[-1]["status"] == "stop error"

    monkeypatch.setattr(main_ui, "get_pod_logs", lambda _pod: "pod output")
    MainUI._get_logs(ui, "pod-1", "Get Pod Logs", "kubernetes")
    assert "pod output" in ui.messages
    assert ui.finished[-1]["status"] == "get pod logs complete"

    monkeypatch.setattr(main_ui, "get_pod_logs", fail)
    MainUI._get_logs(ui, "pod-1", "Get Pod Logs", "kubernetes")
    assert "Exception: container failure" in ui.messages[-1]
    assert ui.finished[-1]["status"] == "get pod logs error"


def test_media_conversion_thread_reports_success_and_failure(monkeypatch):
    ui = _ui()
    calls = []
    monkeypatch.setattr(
        main_ui,
        "convert_media",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )
    MainUI._convert_media_thread(ui, "in.wav", "out.wav", "128k", "aac", "media")
    assert calls == [(("in.wav", "out.wav"), {"bitrate": "128k", "codec": "aac"})]
    assert ui.finished[-1]["status"] == "media conversion complete"
    assert ui.statuses[-1] == "Status: Ready"

    monkeypatch.setattr(
        main_ui,
        "convert_media",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad media")),
    )
    MainUI._convert_media_thread(ui, "in", "out", None, None, "media")
    assert "Exception: bad media" in ui.messages[-1]
    assert ui.finished[-1]["status"] == "media conversion error"


def test_event_overview_and_navigation_state_updates():
    ui = _ui()
    ui.state = main_ui.build_default_state()
    ui.event_bus = main_ui.EventBus()
    ui.memory_var = _Var()
    ui.platform_var = _Var()
    ui.activity_var = _Var()
    ui.gui_actions = main_ui.default_gui_actions()
    ui.gui_sections = main_ui.default_gui_sections()
    ui.action_tab_ids, ui.action_tab_titles = MainUI._build_action_tab_index(ui)
    ui.event_bus.subscribe(main_ui.EventType.RUN_STARTED, ui._handle_event)

    MainUI._refresh_overview(ui)
    assert ui.activity_var.get() == "Waiting for the first action."
    MainUI._emit_event(
        ui,
        main_ui.EventType.RUN_STARTED,
        {"action": "Run", "status": "running"},
        source="test",
    )
    assert "Run Started: Run" in ui.activity_var.get()
    assert ui.memory_var.get() == ui.state.memory.root_path

    frame = object()
    calls = []
    selection = {"frame": None}

    def select(frame=None):
        if frame is not None:
            calls.append(frame)
            selection["frame"] = frame
        return selection["frame"]

    ui.surface_notebook = SimpleNamespace(select=select)
    ui.surface_tab_frames = {"runtime-ops": frame}
    ui.surface_tab_titles = {"runtime-ops": "Runtime Ops"}
    MainUI.select_tab(ui, "runtime-ops")
    assert calls == [frame]
    assert ui.surface_var.get() == "Runtime Ops"
    assert ui.state.operator.active_view == "runtime-ops"
    ui.surface_notebook.tab = lambda _frame, _field: "Runtime Ops"
    MainUI._on_tab_changed(ui)
    assert ui.state.operator.active_view == "runtime-ops"


def test_log_helpers_and_thread_submission_paths(monkeypatch):
    ui = _ui()
    seen = []
    ui.root = SimpleNamespace(
        after=lambda delay, callback: seen.append((delay, callback))
    )
    ui.status_label = SimpleNamespace(config=lambda **kwargs: seen.append(kwargs))
    ui.progress = SimpleNamespace(
        start=lambda: seen.append("start"), stop=lambda: seen.append("stop")
    )
    ui.log_text = SimpleNamespace(
        insert=lambda *args: seen.append(("insert", args)),
        see=lambda *args: seen.append(("see", args)),
        delete=lambda *args: seen.append(("delete", args)),
    )
    MainUI._set_status(ui, "ready")
    MainUI._start_progress(ui)
    MainUI._stop_progress(ui)
    MainUI.log_message(ui, "done\n")
    for item in seen:
        if isinstance(item, tuple) and len(item) == 2 and item[0] == 0:
            item[1]()
    assert {"text": "ready"} in seen
    assert ("insert", ("end", "done\n")) in seen
    assert ("see", ("end",)) in seen
    MainUI.clear_log(ui)
    assert ("delete", ("1.0", "end")) in seen

    submitted = []
    ui.executor = SimpleNamespace(
        submit=lambda *args, **kwargs: submitted.append((args, kwargs))
    )
    MainUI._submit_task(ui, lambda: None, "arg", flag=True)
    assert submitted[0][0][1:] == ("arg",)
    assert submitted[0][1] == {"flag": True}

    ui = _ui()
    started = []

    class ImmediateThread:
        def __init__(self, *, target, args, kwargs):
            self.target, self.args, self.kwargs = target, args, kwargs

        def start(self):
            started.append((self.target, self.args, self.kwargs))
            self.target(*self.args, **self.kwargs)

    monkeypatch.setattr(main_ui.threading, "Thread", ImmediateThread)
    MainUI._submit_task(ui, lambda value: started.append(value), "fallback")
    assert "fallback" in started
