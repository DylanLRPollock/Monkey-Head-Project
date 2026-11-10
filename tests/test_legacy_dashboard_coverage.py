"""Exercise dashboard helpers and interactions with lightweight Qt fakes."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from huey.core.task_scheduler import Agent, TaskPriority, TaskStatus


class _Signal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class _Widget:
    def __init__(self, *_args, **_kwargs):
        self.text = ""
        self.children = []
        self.items = {}
        self.rows = 0
        self.current_row = -1
        self.clicked = _Signal()
        self.timeout = _Signal()
        self._header = SimpleNamespace(
            setSectionResizeMode=lambda *_args: None,
        )

    def __getattr__(self, name):
        if name.startswith("set") or name in {"resize", "show", "exec", "start"}:
            return lambda *_args, **_kwargs: None
        raise AttributeError(name)

    def addWidget(self, item, *_args):
        self.children.append(item)

    def addLayout(self, item, *_args):
        self.children.append(item)

    def setText(self, value):
        self.text = value

    def setValue(self, value):
        self.value = value

    def setRowCount(self, count):
        self.rows = count
        self.items = {}

    def setItem(self, row, column, item):
        self.items[(row, column)] = item

    def item(self, row, column):
        return self.items.get((row, column))

    def currentRow(self):
        return self.current_row

    def resizeRowsToContents(self):
        return None

    def horizontalHeader(self):
        return self._header

    def header(self):
        return self._header

    def clear(self):
        self.children = []

    def addTopLevelItem(self, item):
        self.children.append(item)

    def addTab(self, widget, label):
        self.children.append((widget, label))


class _TableItem:
    def __init__(self, text):
        self._text = str(text)

    def text(self):
        return self._text


class _TreeItem:
    def __init__(self, values):
        self.values = values


class _Application:
    instance_value = None
    exec_count = 0

    def __init__(self, _args):
        type(self).instance_value = self

    @classmethod
    def instance(cls):
        return cls.instance_value

    def setStyleSheet(self, _style):
        self.style_set = True

    def exec(self):
        type(self).exec_count += 1


class _Dialogs:
    text_results: ClassVar[list] = []
    item_results: ClassVar[list] = []
    notices: ClassVar[list] = []

    @classmethod
    def getText(cls, *_args):
        return cls.text_results.pop(0)

    @classmethod
    def getItem(cls, *_args, **_kwargs):
        return cls.item_results.pop(0)

    @classmethod
    def information(cls, *_args):
        cls.notices.append(("info", _args[1], _args[2]))

    @classmethod
    def warning(cls, *_args):
        cls.notices.append(("warning", _args[1], _args[2]))


def _qt_modules():
    qt_core = types.ModuleType("PySide6.QtCore")
    qt_core.Qt = SimpleNamespace(AlignLeft=0)
    qt_core.QTimer = _Widget

    qt_widgets = types.ModuleType("PySide6.QtWidgets")
    for name in (
        "QGridLayout",
        "QHBoxLayout",
        "QLabel",
        "QMainWindow",
        "QProgressBar",
        "QPushButton",
        "QTableWidget",
        "QTabWidget",
        "QTreeWidget",
        "QVBoxLayout",
        "QWidget",
    ):
        setattr(qt_widgets, name, _Widget)
    qt_widgets.QApplication = _Application
    qt_widgets.QHeaderView = SimpleNamespace(Stretch=1, ResizeToContents=2)
    qt_widgets.QInputDialog = _Dialogs
    qt_widgets.QMessageBox = _Dialogs
    qt_widgets.QTableWidgetItem = _TableItem
    qt_widgets.QTreeWidgetItem = _TreeItem

    package = types.ModuleType("PySide6")
    package.__path__ = []
    package.QtCore = qt_core
    package.QtWidgets = qt_widgets
    return {
        "PySide6": package,
        "PySide6.QtCore": qt_core,
        "PySide6.QtWidgets": qt_widgets,
    }


@pytest.fixture
def dashboard(monkeypatch, tmp_path):
    for name, module in _qt_modules().items():
        monkeypatch.setitem(sys.modules, name, module)
    source = (
        Path(__file__).parents[1] / "src" / "huey" / "memory" / "PY" / "dashboard.py"
    )
    spec = importlib.util.spec_from_file_location("huey.memory.PY.dashboard", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    root = tmp_path / "memory"
    root.mkdir()
    monkeypatch.setattr(module, "get_memory_path", lambda **_kwargs: root)
    _Dialogs.text_results = []
    _Dialogs.item_results = []
    _Dialogs.notices = []
    _Application.instance_value = None
    _Application.exec_count = 0
    return module, root


def _record(
    task_id,
    status,
    requested=None,
    assigned=None,
    *,
    updated=1.0,
):
    return SimpleNamespace(
        task_id=task_id,
        command=f"command {task_id}",
        priority=TaskPriority.NORMAL,
        status=status,
        requested_agent=requested,
        assigned_agent=assigned,
        updated_at=updated,
    )


def test_format_size_directory_summary_and_error_paths(dashboard, tmp_path):
    module, _root = dashboard
    assert module._format_bytes(None) == "Unknown"
    assert module._format_bytes(1) == "1.00 B"
    assert module._format_bytes(1024**5) == "1.00 PB"

    folder = tmp_path / "folder"
    nested = folder / "nested"
    nested.mkdir(parents=True)
    (folder / ".hidden").write_text("ignore", encoding="utf-8")
    (folder / "top.txt").write_text("123", encoding="utf-8")
    (nested / "inside.txt").write_text("abcd", encoding="utf-8")
    assert module._directory_size(folder, depth=0) == (3.0, 1)
    assert module._directory_size(folder, depth=-1) == (0.0, 0)
    assert module._directory_size(folder / "top.txt") == (3.0, 1)
    assert [entry[0] for entry in module._memory_summary(folder)] == [
        ".hidden",
        "nested",
        "top.txt",
    ]
    assert module._memory_summary(tmp_path / "absent") == []


def test_directory_size_handles_filesystem_errors(dashboard, tmp_path, monkeypatch):
    module, _root = dashboard
    folder = tmp_path / "broken"
    folder.mkdir()

    def fail_iterdir(_path):
        raise OSError("unreadable")

    monkeypatch.setattr(Path, "iterdir", fail_iterdir)
    assert module._directory_size(folder) == (0.0, 0)


def test_system_metrics_success_fallback_and_unavailable(dashboard, monkeypatch):
    module, _root = dashboard
    module.psutil = SimpleNamespace(
        cpu_percent=lambda **_kwargs: 12.5,
        virtual_memory=lambda: SimpleNamespace(used=10, total=100),
        disk_usage=lambda _path: SimpleNamespace(used=20, total=200),
        boot_time=lambda: 100.0,
    )
    monkeypatch.setattr(module.time, "time", lambda: 3701.0)
    metrics = module._system_metrics()
    assert metrics["CPU Load"] == "12.5%"
    assert metrics["MemoryPercent"] == "10.0"
    assert metrics["Uptime"] == "1h 0m"

    module.psutil = SimpleNamespace(
        cpu_percent=lambda **_kwargs: (_ for _ in ()).throw(OSError()),
        virtual_memory=lambda: (_ for _ in ()).throw(OSError()),
        disk_usage=lambda _path: (_ for _ in ()).throw(OSError()),
        boot_time=lambda: (_ for _ in ()).throw(OSError()),
    )
    broken = module._system_metrics()
    assert broken["CPU Load"] == "Unavailable"
    assert broken["Memory"] == "Unavailable"
    assert broken["Disk"] == "Unavailable"
    assert "Uptime" not in broken

    module.psutil = None
    assert module._system_metrics()["Uptime"] == "Unknown"


def test_dashboard_window_builds_tabs_and_refreshes_views(dashboard, monkeypatch):
    module, root = dashboard
    (root / "notes.txt").write_text("note", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "guide.txt").write_text("guide", encoding="utf-8")
    records = [
        _record("r", TaskStatus.RUNNING, Agent.SPARK, Agent.SPARK, updated=1),
        _record("p", TaskStatus.PENDING, Agent.ZAP, None, updated=2),
        _record("c", TaskStatus.COMPLETED, Agent.SPARK, None, updated=3),
        _record("f", TaskStatus.FAILED, Agent.ZAP),
        _record("u", TaskStatus.FAILED),
    ]
    scheduler = SimpleNamespace(
        list_tasks=lambda: records,
        submit_task=lambda **_kwargs: SimpleNamespace(task_id="new"),
        reconcile=lambda: [1, 2],
        complete_task=lambda _task_id: None,
    )
    window = module.DashboardWindow(scheduler=scheduler)

    assert len(window.tabs.children) == 4
    assert window.task_table.rows == 5
    assert window.task_table.item(0, 0).text() == "r"
    assert window.task_table.item(1, 4).text() == "zap"
    assert window.agent_table.rows == len(Agent)
    assert window.memory_tree.children
    assert "Total" in window.memory_summary.text

    monkeypatch.setattr(
        module,
        "_system_metrics",
        lambda: {"CPU Load": "1%", "MemoryPercent": "not-number"},
    )
    window.refresh_system_metrics()
    assert window.system_labels["CPU Load"].text == "1%"
    assert window.system_labels["Disk"].text == "Unknown"
    assert window.memory_bar.value == 0


def test_dashboard_task_actions_handle_cancel_success_errors_and_reconcile(dashboard):
    module, _root = dashboard
    submitted = []
    completed = []
    scheduler = SimpleNamespace(
        list_tasks=lambda: [],
        submit_task=lambda **kwargs: submitted.append(kwargs)
        or SimpleNamespace(task_id="t-1"),
        reconcile=lambda: ["a", "b"],
        complete_task=lambda task_id: completed.append(task_id),
    )
    window = module.DashboardWindow(scheduler=scheduler)

    _Dialogs.text_results = [("", True)]
    window._submit_task_dialog()
    assert submitted == []
    _Dialogs.text_results = [("train", True)]
    _Dialogs.item_results = [("", True)]
    window._submit_task_dialog()
    assert submitted == []
    _Dialogs.text_results = [("  train  ", True)]
    _Dialogs.item_results = [("HIGH", True)]
    window._submit_task_dialog()
    assert submitted[0]["command"] == "train"
    assert submitted[0]["priority"] is TaskPriority.HIGH
    assert _Dialogs.notices[-1][1] == "Task Submitted"

    window._reconcile_tasks()
    assert _Dialogs.notices[-1][2] == "Re-dispatched 2 task(s)."
    window._complete_selected_task()
    assert _Dialogs.notices[-1][0] == "warning"

    window.task_table.current_row = 0
    window._complete_selected_task()
    assert completed == []
    window.task_table.setItem(0, 0, _TableItem("t-1"))
    window._complete_selected_task()
    assert completed == ["t-1"]
    assert _Dialogs.notices[-1][1] == "Task Completed"

    def missing(_task_id):
        raise KeyError("gone")

    scheduler.complete_task = missing
    window.task_table.current_row = 0
    window.task_table.setItem(0, 0, _TableItem("t-1"))
    window._complete_selected_task()
    assert _Dialogs.notices[-1] == ("warning", "Complete Task", "'gone'")


def test_dashboard_launch_owns_or_reuses_application(dashboard, monkeypatch):
    module, _root = dashboard
    monkeypatch.setattr(module, "as_qt_stylesheet", lambda: "style")
    module.launch_dashboard()
    assert _Application.exec_count == 1
    assert _Application.instance_value.style_set is True

    module.launch_dashboard()
    assert _Application.exec_count == 1

    monkeypatch.setattr(module, "QApplication", None)
    with pytest.raises(RuntimeError, match="PySide6 is not available"):
        module.DashboardWindow()
    with pytest.raises(RuntimeError, match="PySide6 is not available"):
        module.launch_dashboard()
