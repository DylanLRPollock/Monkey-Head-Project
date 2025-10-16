# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Dashboard module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.12.2025
# ==================================================
"""PySide6 dashboard providing a consolidated operational overview."""

from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

try:  # pragma: no cover - optional GUI dependencies
    from PySide6.QtCore import QTimer, Qt
    from PySide6.QtWidgets import (
        QApplication,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover - GUI not available
    QApplication = None  # type: ignore[assignment]

try:  # pragma: no cover - optional theming
    from qt_material import apply_stylesheet
except Exception:  # pragma: no cover - theme not installed
    apply_stylesheet = None  # type: ignore[assignment]

try:  # pragma: no cover - psutil optional
    import psutil  # type: ignore
except Exception:  # pragma: no cover - psutil missing at runtime
    psutil = None  # type: ignore[assignment]

from monkey_head.core.task_scheduler import (
    Agent,
    TaskPriority,
    TaskScheduler,
    TaskStatus,
)
from monkey_head.utils.paths import get_memory_path


def _format_bytes(value: float | int | None) -> str:
    """Return ``value`` formatted as a human readable string."""

    if value is None:
        return "Unknown"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024.0:
            return f"{size:0.2f} {unit}"
        size /= 1024.0
    return f"{size:0.2f} PB"


def _directory_size(path: Path, *, depth: int = 1) -> Tuple[float, int]:
    """Return ``(size, item_count)`` for ``path`` limited by ``depth``."""

    total = 0
    count = 0
    try:
        if path.is_file():
            return float(path.stat().st_size), 1
        if depth < 0:
            return 0.0, 0
        for entry in path.iterdir():
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                size, items = _directory_size(entry, depth=depth - 1)
                total += size
                count += items
            else:
                total += float(entry.stat().st_size)
                count += 1
    except Exception:
        return 0.0, 0
    return total, count


def _memory_summary(path: Path) -> List[Tuple[str, float, int]]:
    """Return aggregated stats for the top-level entries inside ``path``."""

    results: List[Tuple[str, float, int]] = []
    try:
        for entry in sorted(path.iterdir(), key=lambda e: e.name.lower()):
            size, items = _directory_size(entry, depth=1)
            results.append((entry.name, size, items))
    except Exception:
        return []
    return results


def _system_metrics() -> Dict[str, str]:
    """Gather host metrics for display."""

    metrics: Dict[str, str] = {}
    if psutil is not None:  # pragma: no branch
        try:
            metrics["CPU Load"] = f"{psutil.cpu_percent(interval=0.05):0.1f}%"
        except Exception:
            metrics["CPU Load"] = "Unavailable"
        try:
            vm = psutil.virtual_memory()
            metrics["Memory"] = f"{_format_bytes(vm.used)} / {_format_bytes(vm.total)}"
            metrics["MemoryPercent"] = f"{(vm.used / vm.total) * 100:0.1f}" if vm.total else "0.0"
        except Exception:
            metrics["Memory"] = "Unavailable"
            metrics["MemoryPercent"] = "0.0"
        try:
            disk = psutil.disk_usage(str(Path("/")))
            metrics["Disk"] = f"{_format_bytes(disk.used)} / {_format_bytes(disk.total)}"
        except Exception:
            metrics["Disk"] = "Unavailable"
        try:
            boot = getattr(psutil, "boot_time", lambda: None)()
        except Exception:
            boot = None
        if boot:
            uptime = max(0.0, time.time() - float(boot))
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            metrics["Uptime"] = f"{hours}h {minutes}m"
    else:
        metrics.update({
            "CPU Load": "psutil unavailable",
            "Memory": "psutil unavailable",
            "MemoryPercent": "0.0",
            "Disk": "psutil unavailable",
            "Uptime": "Unknown",
        })
    return metrics


class DashboardWindow(QMainWindow):
    """Main window hosting the dashboard tabs."""

    def __init__(self, scheduler: TaskScheduler | None = None) -> None:
        if QApplication is None:  # pragma: no cover - GUI environment missing
            raise RuntimeError("PySide6 is not available")

        super().__init__()
        self.scheduler = scheduler or TaskScheduler()
        self.setWindowTitle("Monkey Head Dashboard")
        self.resize(1100, 720)

        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._setup_system_tab()
        self._setup_memory_tab()
        self._setup_task_tab()
        self._setup_agent_tab()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_all)
        self._timer.start(5000)
        self.refresh_all()

    # ------------------------------------------------------------------
    # Tab setup helpers
    # ------------------------------------------------------------------
    def _setup_system_tab(self) -> None:
        self.system_tab = QWidget()
        grid = QGridLayout(self.system_tab)
        self.system_labels: Dict[str, QLabel] = {}

        labels = ["CPU Load", "Memory", "Disk", "Uptime"]
        for row, label in enumerate(labels):
            grid.addWidget(QLabel(label + ":"), row, 0, Qt.AlignLeft)
            value_label = QLabel("…")
            grid.addWidget(value_label, row, 1, Qt.AlignLeft)
            self.system_labels[label] = value_label

        self.memory_bar = QProgressBar()
        self.memory_bar.setRange(0, 100)
        grid.addWidget(QLabel("Memory Utilisation:"), len(labels), 0, Qt.AlignLeft)
        grid.addWidget(self.memory_bar, len(labels), 1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_system_metrics)
        grid.addWidget(refresh_btn, len(labels) + 1, 0)

        self.tabs.addTab(self.system_tab, "System Metrics")

    def _setup_memory_tab(self) -> None:
        self.memory_tab = QWidget()
        layout = QVBoxLayout(self.memory_tab)

        self.memory_summary = QLabel("Scanning memory path…")
        layout.addWidget(self.memory_summary)

        self.memory_tree = QTreeWidget()
        self.memory_tree.setColumnCount(3)
        self.memory_tree.setHeaderLabels(["Name", "Size", "Items"])
        self.memory_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.memory_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.memory_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        layout.addWidget(self.memory_tree)

        button_row = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_memory_view)
        button_row.addWidget(refresh_btn)
        layout.addLayout(button_row)

        self.tabs.addTab(self.memory_tab, "Memory")

    def _setup_task_tab(self) -> None:
        self.task_tab = QWidget()
        layout = QVBoxLayout(self.task_tab)

        self.task_table = QTableWidget(0, 7)
        self.task_table.setHorizontalHeaderLabels(
            [
                "Task ID",
                "Command",
                "Priority",
                "Status",
                "Requested Agent",
                "Assigned Agent",
                "Updated",
            ]
        )
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for idx in range(2, 6):
            self.task_table.horizontalHeader().setSectionResizeMode(idx, QHeaderView.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        layout.addWidget(self.task_table)

        buttons = QHBoxLayout()
        submit_btn = QPushButton("Submit Task")
        submit_btn.clicked.connect(self._submit_task_dialog)
        buttons.addWidget(submit_btn)

        reconcile_btn = QPushButton("Reconcile")
        reconcile_btn.clicked.connect(self._reconcile_tasks)
        buttons.addWidget(reconcile_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_task_table)
        buttons.addWidget(refresh_btn)

        complete_btn = QPushButton("Complete Selected")
        complete_btn.clicked.connect(self._complete_selected_task)
        buttons.addWidget(complete_btn)

        layout.addLayout(buttons)

        self.tabs.addTab(self.task_tab, "Task Management")

    def _setup_agent_tab(self) -> None:
        self.agent_tab = QWidget()
        layout = QVBoxLayout(self.agent_tab)

        self.agent_table = QTableWidget(0, 4)
        self.agent_table.setHorizontalHeaderLabels(
            ["Agent", "Running", "Pending", "Completed"]
        )
        self.agent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.agent_table)

        self.tabs.addTab(self.agent_tab, "Agent Status")

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------
    def refresh_all(self) -> None:
        self.refresh_system_metrics()
        self.refresh_memory_view()
        self.refresh_task_table()
        self.refresh_agent_table()

    def refresh_system_metrics(self) -> None:
        metrics = _system_metrics()
        for key, label in self.system_labels.items():
            label.setText(metrics.get(key, "Unknown"))
        try:
            percent = float(metrics.get("MemoryPercent", "0.0"))
        except ValueError:
            percent = 0.0
        self.memory_bar.setValue(int(percent))

    def refresh_memory_view(self) -> None:
        memory_path = get_memory_path(create=True)
        summary = _memory_summary(memory_path)
        self.memory_tree.clear()
        total_size = 0.0
        total_items = 0
        for name, size, items in summary:
            item = QTreeWidgetItem([name, _format_bytes(size), str(items)])
            self.memory_tree.addTopLevelItem(item)
            total_size += size
            total_items += items
        self.memory_summary.setText(
            f"Memory root: {memory_path} — Total {_format_bytes(total_size)} across {total_items} items"
        )

    def refresh_task_table(self) -> None:
        records = self.scheduler.list_tasks()
        self.task_table.setRowCount(len(records))
        for row, record in enumerate(records):
            values = [
                record.task_id,
                record.command,
                record.priority.name,
                record.status.value,
                record.requested_agent.value if record.requested_agent else "—",
                record.assigned_agent.value if record.assigned_agent else "—",
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(record.updated_at)),
            ]
            for col, value in enumerate(values):
                self.task_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.task_table.resizeRowsToContents()

    def refresh_agent_table(self) -> None:
        records = self.scheduler.list_tasks()
        stats: Dict[Agent, Dict[str, int]] = defaultdict(lambda: {"running": 0, "pending": 0, "completed": 0})
        for record in records:
            agent = record.assigned_agent or record.requested_agent
            if agent is None:
                continue
            if record.status is TaskStatus.RUNNING:
                stats[agent]["running"] += 1
            elif record.status is TaskStatus.PENDING:
                stats[agent]["pending"] += 1
            elif record.status is TaskStatus.COMPLETED:
                stats[agent]["completed"] += 1

        self.agent_table.setRowCount(len(Agent))
        for row, agent in enumerate(Agent):
            data = stats.get(agent, {"running": 0, "pending": 0, "completed": 0})
            self.agent_table.setItem(row, 0, QTableWidgetItem(agent.value))
            self.agent_table.setItem(row, 1, QTableWidgetItem(str(data["running"])))
            self.agent_table.setItem(row, 2, QTableWidgetItem(str(data["pending"])))
            self.agent_table.setItem(row, 3, QTableWidgetItem(str(data["completed"])))
        self.agent_table.resizeRowsToContents()

    # ------------------------------------------------------------------
    # Task management actions
    # ------------------------------------------------------------------
    def _submit_task_dialog(self) -> None:
        command, ok = QInputDialog.getText(self, "Submit Task", "Command")
        if not ok or not command.strip():
            return
        priorities = [priority.name for priority in TaskPriority]
        priority_name, ok = QInputDialog.getItem(
            self,
            "Task Priority",
            "Select priority",
            priorities,
            editable=False,
        )
        if not ok or not priority_name:
            return
        priority = TaskPriority[priority_name]
        record = self.scheduler.submit_task(command=command.strip(), priority=priority)
        QMessageBox.information(
            self,
            "Task Submitted",
            f"Task {record.task_id} queued with priority {priority.name}.",
        )
        self.refresh_all()

    def _reconcile_tasks(self) -> None:
        dispatched = self.scheduler.reconcile()
        QMessageBox.information(
            self,
            "Reconcile",
            f"Re-dispatched {len(dispatched)} task(s).",
        )
        self.refresh_all()

    def _complete_selected_task(self) -> None:
        row = self.task_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Complete Task", "Select a task to mark as complete.")
            return
        task_id_item = self.task_table.item(row, 0)
        if task_id_item is None:
            return
        task_id = task_id_item.text()
        try:
            self.scheduler.complete_task(task_id)
        except KeyError as exc:
            QMessageBox.warning(self, "Complete Task", str(exc))
        else:
            QMessageBox.information(self, "Task Completed", f"Task {task_id} marked completed.")
        self.refresh_all()


def launch_dashboard(scheduler: TaskScheduler | None = None) -> None:
    """Launch the dashboard application."""

    if QApplication is None:
        raise RuntimeError("PySide6 is not available")

    app = QApplication.instance()
    owns_app = False
    if app is None:
        app = QApplication(sys.argv)
        owns_app = True
    if apply_stylesheet is not None:
        apply_stylesheet(app, theme="dark_teal.xml")

    window = DashboardWindow(scheduler=scheduler)
    window.show()

    if owns_app:
        app.exec()


__all__ = ["launch_dashboard", "DashboardWindow"]
