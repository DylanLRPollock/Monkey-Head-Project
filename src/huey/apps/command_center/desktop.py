"""Native Tkinter desktop UI for the local HueyOS Command Center.

The interface is a planning dashboard. It never executes displayed commands,
contacts repositories, changes runtime state, or controls physical systems.
"""

from __future__ import annotations

import json
import os
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from huey.gui.defaults import (
    default_migration_phases,
    default_operator_panel_state,
    default_repositories,
)
from huey.gui.models import MigrationPhase, dataclass_list_to_dicts, dataclass_to_dict
from huey.gui.prompts import generate_next_best_task_prompt, generate_phase_prompt
from huey.gui.safety import safety_banner
from huey.gui.v1_runs import sample_v1_runs
from huey.gui.validation import all_validation_commands

APP_SCHEMA = "huey.command_center.desktop.v1"
PHASE_STATUSES = ("not_started", "in_progress", "blocked", "ready_for_pr", "merged")
RISK_LEVELS = ("low", "medium", "high", "critical")
STATUS_LABELS = {
    "not_started": "Not started",
    "in_progress": "In progress",
    "blocked": "Blocked",
    "ready_for_pr": "Ready for PR",
    "merged": "Merged",
}


def state_file_path() -> Path:
    """Return the per-user local dashboard-state path."""
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return root / "huey" / "command-center" / "state.json"


def _initial_snapshot() -> dict[str, Any]:
    phases = dataclass_list_to_dicts(default_migration_phases())
    return {
        "schema": APP_SCHEMA,
        "migration": {
            "phases": phases,
            "checklist_completed": {
                phase["id"]: [False] * len(phase.get("checklist", []))
                for phase in phases
            },
            "global_notes": "",
        },
        "v1_runs": dataclass_list_to_dicts(sample_v1_runs()),
        "operator_panel": dataclass_to_dict(default_operator_panel_state()),
        "dependency_backlog": {},
    }


def _validated_snapshot(payload: object) -> dict[str, Any]:
    """Validate imported/local state before it is used by the UI."""
    if not isinstance(payload, dict) or payload.get("schema") != APP_SCHEMA:
        raise ValueError("Unsupported dashboard state schema.")
    migration = payload.get("migration")
    if not isinstance(migration, dict):
        raise ValueError("Dashboard state is missing its migration section.")
    phases = migration.get("phases")
    if not isinstance(phases, list):
        raise ValueError("Migration phases must be a list.")

    defaults = {phase.id: asdict(phase) for phase in default_migration_phases()}
    incoming: dict[str, dict[str, Any]] = {}
    for phase in phases:
        if not isinstance(phase, dict) or phase.get("id") not in defaults:
            raise ValueError("Migration state contains an unknown phase.")
        phase_id = str(phase["id"])
        if phase_id in incoming:
            raise ValueError("Migration state contains a duplicate phase.")
        base = defaults[phase_id]
        status = phase.get("status", base["status"])
        risk = phase.get("risk", base["risk"])
        if status not in PHASE_STATUSES or risk not in RISK_LEVELS:
            raise ValueError(f"Invalid status or risk for {phase_id}.")
        notes = phase.get("notes", base.get("notes", ""))
        if not isinstance(notes, str):
            raise ValueError(f"Notes for {phase_id} must be text.")
        incoming[phase_id] = {**base, "status": status, "risk": risk, "notes": notes}

    normalized = _initial_snapshot()
    normalized_phases = []
    completed = migration.get("checklist_completed", {})
    if not isinstance(completed, dict):
        raise ValueError("Checklist completion state must be an object.")
    normalized_completion: dict[str, list[bool]] = {}
    for phase_id, base in defaults.items():
        phase = incoming.get(phase_id, base)
        normalized_phases.append(phase)
        flags = completed.get(phase_id, [False] * len(phase["checklist"]))
        if (
            not isinstance(flags, list)
            or len(flags) != len(phase["checklist"])
            or any(type(flag) is not bool for flag in flags)
        ):
            raise ValueError(f"Invalid checklist completion values for {phase_id}.")
        normalized_completion[phase_id] = flags

    global_notes = migration.get("global_notes", "")
    if not isinstance(global_notes, str):
        raise ValueError("Global notes must be text.")
    normalized["migration"] = {
        "phases": normalized_phases,
        "checklist_completed": normalized_completion,
        "global_notes": global_notes,
    }

    runs = payload.get("v1_runs", normalized["v1_runs"])
    if not isinstance(runs, list) or any(not isinstance(run, dict) for run in runs):
        raise ValueError("V1 runs must be a list of JSON objects.")
    normalized["v1_runs"] = runs

    operator = payload.get("operator_panel", normalized["operator_panel"])
    if not isinstance(operator, dict):
        raise ValueError("Operator panel data must be a JSON object.")
    normalized["operator_panel"] = operator

    backlog = payload.get("dependency_backlog", {})
    if not isinstance(backlog, dict):
        raise ValueError("Dependency/security backlog must be a JSON object.")
    normalized["dependency_backlog"] = backlog
    return normalized


def load_local_state(path: Path | None = None) -> tuple[dict[str, Any], str | None]:
    """Read local state, falling back to safe defaults if it is invalid."""
    selected = path or state_file_path()
    if not selected.exists():
        return _initial_snapshot(), None
    try:
        payload = json.loads(selected.read_text(encoding="utf-8"))
        return _validated_snapshot(payload), None
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return _initial_snapshot(), f"Local dashboard state was not loaded: {exc}"


class CommandCenterDesktop(tk.Tk):
    """Local-first Tkinter dashboard port of the supplied web application."""

    def __init__(self) -> None:
        super().__init__()
        self.title("HueyOS Command Center")
        self.geometry("1180x820")
        self.minsize(850, 640)
        self.configure(background="#15131d")
        self.state_path = state_file_path()
        self.snapshot, self.load_warning = load_local_state(self.state_path)
        self.save_job: str | None = None
        self.phase_lookup = {
            phase["id"]: phase for phase in self.snapshot["migration"]["phases"]
        }
        self._configure_style()
        self._build_ui()
        self._refresh_phase_list()
        self._refresh_v1_runs()
        self.protocol("WM_DELETE_WINDOW", self._close)
        if self.load_warning:
            self.after(
                250,
                lambda: messagebox.showwarning("Command Center", self.load_warning),
            )

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("TkDefaultFont", 10))
        style.configure("TFrame", background="#15131d")
        style.configure("Panel.TFrame", background="#211d2c")
        style.configure("TLabel", background="#15131d", foreground="#f2eef8")
        style.configure("Panel.TLabel", background="#211d2c", foreground="#f2eef8")
        style.configure("Muted.TLabel", foreground="#c0b9cb")
        style.configure("Title.TLabel", font=("TkDefaultFont", 21, "bold"))
        style.configure("TNotebook", background="#15131d", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 9), background="#292438")
        style.map("TNotebook.Tab", background=[("selected", "#574276")])
        style.configure("Treeview", rowheight=28, background="#211d2c",
                        fieldbackground="#211d2c", foreground="#f2eef8")
        style.configure("Treeview.Heading", background="#342d43", foreground="#f2eef8")
        style.configure("TCombobox", fieldbackground="#211d2c", foreground="#f2eef8")
        style.configure("TButton", padding=(9, 6))
        style.configure("TCheckbutton", background="#211d2c", foreground="#f2eef8")
        style.configure("Horizontal.TProgressbar", background="#54c997",
                        troughcolor="#373141")

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=18)
        outer.pack(fill="both", expand=True)
        heading = ttk.Frame(outer)
        heading.pack(fill="x", pady=(0, 14))
        ttk.Label(heading, text="COMMAND CENTER", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            heading,
            text=(
                "Monkey-Head-Project ecosystem dashboard · local planning and mock data"
            ),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill="both", expand=True)
        self._build_migration_tab()
        self._build_repositories_tab()
        self._build_validation_tab()
        self._build_copilot_tab()
        self._build_v1_tab()
        self._build_operator_tab()
        self._build_umbrella_tab()
        self._build_data_tab()

        self.status_var = tk.StringVar(value=f"Local state: {self.state_path}")
        ttk.Label(outer, textvariable=self.status_var, style="Muted.TLabel").pack(
            anchor="w", pady=(10, 0)
        )

    def _tab(self, title: str) -> ttk.Frame:
        frame = ttk.Frame(self.notebook, padding=14)
        self.notebook.add(frame, text=title)
        return frame

    def _build_migration_tab(self) -> None:
        tab = self._tab("Migration")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

        ttk.Label(tab, text="Overall migration checklist progress").grid(
            row=0, column=0, sticky="w"
        )
        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(tab, variable=self.progress_var, maximum=100).grid(
            row=1, column=0, sticky="ew", pady=(6, 12)
        )
        self.progress_text = ttk.Label(tab, text="")
        self.progress_text.grid(row=1, column=0, sticky="e", pady=(6, 12))

        split = ttk.Panedwindow(tab, orient="horizontal")
        split.grid(row=2, column=0, sticky="nsew")
        left = ttk.Frame(split, padding=(0, 0, 12, 0))
        right = ttk.Frame(split, padding=(12, 0, 0, 0))
        split.add(left, weight=2)
        split.add(right, weight=3)

        self.phase_tree = ttk.Treeview(
            left, columns=("status", "risk", "progress"), show="headings",
            selectmode="browse"
        )
        for column, label, width in (
            ("status", "Status", 110), ("risk", "Risk", 75), ("progress", "Tasks", 70)
        ):
            self.phase_tree.heading(column, text=label)
            self.phase_tree.column(column, width=width, anchor="w")
        self.phase_tree.pack(fill="both", expand=True)
        self.phase_tree.bind("<<TreeviewSelect>>", self._select_phase)

        self.phase_title = ttk.Label(right, text="Select a migration phase",
                                     style="Title.TLabel", wraplength=620)
        self.phase_title.pack(anchor="w", pady=(0, 8))
        self.phase_repo = ttk.Label(right, text="", style="Muted.TLabel")
        self.phase_repo.pack(anchor="w", pady=(0, 10))

        controls = ttk.Frame(right)
        controls.pack(fill="x", pady=(0, 8))
        ttk.Label(controls, text="Status").pack(side="left")
        self.phase_status = tk.StringVar()
        self.status_box = ttk.Combobox(
            controls, textvariable=self.phase_status, state="readonly", width=18,
            values=PHASE_STATUSES
        )
        self.status_box.pack(side="left", padx=(6, 18))
        self.status_box.bind("<<ComboboxSelected>>", self._update_phase_field)
        ttk.Label(controls, text="Risk").pack(side="left")
        self.phase_risk = tk.StringVar()
        self.risk_box = ttk.Combobox(
            controls, textvariable=self.phase_risk, state="readonly", width=12,
            values=RISK_LEVELS
        )
        self.risk_box.pack(side="left", padx=6)
        self.risk_box.bind("<<ComboboxSelected>>", self._update_phase_field)

        ttk.Label(right, text="Checklist").pack(anchor="w", pady=(8, 3))
        self.checklist_frame = ttk.Frame(right, style="Panel.TFrame")
        self.checklist_frame.pack(fill="x", anchor="n")
        ttk.Label(right, text="Phase notes").pack(anchor="w", pady=(10, 3))
        self.phase_notes = tk.Text(right, height=5, wrap="word", undo=True,
                                   background="#211d2c", foreground="#f2eef8",
                                   insertbackground="#f2eef8", relief="flat")
        self.phase_notes.pack(fill="x")
        self.phase_notes.bind("<KeyRelease>", self._schedule_save_phase_notes)

        ttk.Label(tab, text="Global notes").grid(
            row=3, column=0, sticky="w", pady=(12, 4)
        )
        self.global_notes = tk.Text(tab, height=4, wrap="word",
                                    background="#211d2c", foreground="#f2eef8",
                                    insertbackground="#f2eef8", relief="flat")
        self.global_notes.grid(row=4, column=0, sticky="ew")
        self.global_notes.insert("1.0", self.snapshot["migration"]["global_notes"])
        self.global_notes.bind("<KeyRelease>", self._schedule_save_global_notes)

    def _build_repositories_tab(self) -> None:
        tab = self._tab("Repositories")
        ttk.Label(tab, text="Repository Health Dashboard", style="Title.TLabel").pack(
            anchor="w", pady=(0, 10)
        )
        ttk.Label(
            tab,
            text="Mock repository cards only. No GitHub API requests are made.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 12))
        for repo in default_repositories():
            card = ttk.LabelFrame(tab, text=f"{repo.name} · {repo.role}", padding=12)
            card.pack(fill="x", pady=5)
            ttk.Label(card, text=repo.description, style="Panel.TLabel",
                      wraplength=900).pack(anchor="w")
            ttk.Label(card, text=f"{repo.full_name}  |  Data: {repo.data_mode}",
                      style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

    def _build_validation_tab(self) -> None:
        tab = self._tab("Validation")
        ttk.Label(tab, text="Validation Command Center", style="Title.TLabel").pack(
            anchor="w", pady=(0, 8)
        )
        ttk.Label(
            tab,
            text=(
                "Commands are displayed and copied only; this app never executes them."
            ),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 10))
        self.validation_tree = ttk.Treeview(
            tab, columns=("repo", "risk", "purpose", "command"), show="headings"
        )
        for column, label, width in (
            ("repo", "Repository", 210), ("risk", "Risk", 80),
            ("purpose", "Purpose", 310), ("command", "Command", 480)
        ):
            self.validation_tree.heading(column, text=label)
            self.validation_tree.column(column, width=width, anchor="w")
        self.validation_tree.pack(fill="both", expand=True)
        self.validation_rows = {}
        for command in all_validation_commands():
            values = (command.repo, command.risk, command.purpose, command.command)
            row = self.validation_tree.insert("", "end", values=values)
            self.validation_rows[row] = command.command
        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Copy selected command",
                   command=self._copy_validation_command).pack(side="left")
        ttk.Button(buttons, text="Copy all commands",
                   command=self._copy_all_validation_commands).pack(side="left", padx=8)

    def _build_copilot_tab(self) -> None:
        tab = self._tab("Copilot")
        ttk.Label(tab, text="Copilot Task Generator", style="Title.TLabel").pack(
            anchor="w", pady=(0, 8)
        )
        ttk.Label(
            tab,
            text=(
                "Generate reviewable task prompts from the migration plan. Nothing is sent."
            ),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 12))
        controls = ttk.Frame(tab)
        controls.pack(fill="x", pady=(0, 10))
        self.prompt_phase = tk.StringVar()
        self.prompt_box = ttk.Combobox(controls, textvariable=self.prompt_phase,
                                       state="readonly", width=54)
        self.prompt_box.pack(side="left")
        self.prompt_box.bind("<<ComboboxSelected>>", self._generate_phase_prompt)
        ttk.Button(controls, text="Next best task",
                   command=self._generate_next_prompt).pack(side="left", padx=8)
        ttk.Button(controls, text="Copy prompt",
                   command=self._copy_prompt).pack(side="left")
        self.prompt_text = tk.Text(tab, wrap="word", background="#211d2c",
                                   foreground="#f2eef8", insertbackground="#f2eef8")
        self.prompt_text.pack(fill="both", expand=True)
        self.prompt_ids = {
            f'{phase["title"]} [{phase["id"]}]': phase["id"]
            for phase in self.snapshot["migration"]["phases"]
        }
        self.prompt_box.configure(values=tuple(self.prompt_ids))
        if self.prompt_ids:
            self.prompt_box.current(0)
            self._generate_phase_prompt()

    def _build_v1_tab(self) -> None:
        tab = self._tab("V1 Runs")
        ttk.Label(tab, text="Huey Brain V1 Proof Loop Runs",
                  style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Label(
            tab,
            text=(
                "Sample/mock run records. Import local JSONL or export the visible records."
            ),
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 10))
        split = ttk.Panedwindow(tab, orient="horizontal")
        split.pack(fill="both", expand=True)
        left = ttk.Frame(split)
        right = ttk.Frame(split, padding=(12, 0, 0, 0))
        split.add(left, weight=2)
        split.add(right, weight=3)
        self.run_tree = ttk.Treeview(
            left, columns=("fixture", "status"), show="headings", selectmode="browse"
        )
        self.run_tree.heading("fixture", text="Fixture")
        self.run_tree.heading("status", text="Result")
        self.run_tree.column("fixture", width=260)
        self.run_tree.column("status", width=90)
        self.run_tree.pack(fill="both", expand=True)
        self.run_tree.bind("<<TreeviewSelect>>", self._select_run)
        self.run_detail = tk.Text(right, wrap="word", background="#211d2c",
                                  foreground="#f2eef8", state="disabled")
        self.run_detail.pack(fill="both", expand=True)
        buttons = ttk.Frame(tab)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(
            buttons, text="Import JSONL", command=self._import_v1_jsonl
        ).pack(side="left")
        ttk.Button(buttons, text="Export runs", command=self._export_v1_runs).pack(
            side="left", padx=8
        )

    def _build_operator_tab(self) -> None:
        tab = self._tab("Operator")
        ttk.Label(tab, text="HueyOS Operator Panel", style="Title.TLabel").pack(
            anchor="w", pady=(0, 8)
        )
        warning = ttk.LabelFrame(tab, text="Safety boundary", padding=12)
        warning.pack(fill="x", pady=(0, 12))
        ttk.Label(
            warning,
            text="Mock-only status display. It cannot control Huey, execute commands, "
                 "change memory or governance, or perform power actions.",
            style="Panel.TLabel",
            wraplength=900,
        ).pack(anchor="w")
        self.operator_frame = ttk.Frame(tab)
        self.operator_frame.pack(fill="x", anchor="n")
        self._render_operator_panel()
        ttk.Button(
            tab, text="Refresh mock display",
            command=lambda: messagebox.showinfo(
                "Mock-only", "Sample display refreshed. No system action was performed."
            ),
        ).pack(anchor="w", pady=(12, 0))

    def _build_umbrella_tab(self) -> None:
        tab = self._tab("Umbrella")
        ttk.Label(tab, text="Project Umbrella", style="Title.TLabel").pack(
            anchor="w", pady=(0, 12)
        )
        policy = safety_banner()
        facts = (
            ("Runtime", "HueyOS / Monkey-Head-Project"),
            ("Cockpit", "PyHuey"),
            ("Dashboard", "Command Center"),
            ("Data mode", "Local planning state and mock repository/run records"),
            ("Network changes allowed", str(policy["allow_network_mutation"])),
            ("Command execution allowed", str(policy["allow_command_execution"])),
            ("Memory/governance mutation allowed",
             f'{policy["allow_memory_mutation"]} / '
             f'{policy["allow_governance_mutation"]}'),
        )
        for label, value in facts:
            row = ttk.Frame(tab)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label, width=36).pack(side="left")
            ttk.Label(row, text=value, style="Muted.TLabel").pack(side="left")
        ttk.Label(
            tab,
            text="Reference repositories and project links are listed as text only. "
                 "This desktop port does not contact external services.",
            style="Muted.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(18, 0))

    def _build_data_tab(self) -> None:
        tab = self._tab("Data")
        ttk.Label(tab, text="Local Data and Backups", style="Title.TLabel").pack(
            anchor="w", pady=(0, 8)
        )
        ttk.Label(
            tab,
            text=f"Dashboard state is stored on this computer at:\\n{self.state_path}",
            style="Muted.TLabel",
            justify="left",
        ).pack(anchor="w", pady=(0, 14))
        ttk.Button(tab, text="Export full state…", command=self._export_state).pack(
            anchor="w", pady=4
        )
        ttk.Button(tab, text="Import full state…", command=self._import_state).pack(
            anchor="w", pady=4
        )
        ttk.Button(tab, text="Reset migration progress to project defaults",
                   command=self._reset_state).pack(anchor="w", pady=(16, 4))
        ttk.Label(
            tab,
            text="Imports are validated before replacing the current state. "
                 "Exports may contain your private notes; review them before sharing.",
            style="Muted.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(14, 0))

    def _render_operator_panel(self) -> None:
        for child in self.operator_frame.winfo_children():
            child.destroy()
        data = self.snapshot["operator_panel"]
        fields = (
            ("API", data.get("api_url", "local")),
            ("Health", data.get("health_status", "unknown")),
            ("Memory", data.get("memory_status", "unknown")),
            ("Governance", data.get("governance_status", "unknown")),
            ("Connector", data.get("connector_status", "unknown")),
            ("Runtime", data.get("runtime_status", "unknown")),
            ("FFmpeg", data.get("ffmpeg_status", "unknown")),
            ("V1", data.get("v1_status", "unknown")),
            ("Mode", "mock-only" if data.get("mock_only", True) else "read-only"),
        )
        for index, (label, value) in enumerate(fields):
            card = ttk.LabelFrame(self.operator_frame, text=label, padding=10)
            card.grid(row=index // 3, column=index % 3, sticky="nsew", padx=5, pady=5)
            ttk.Label(card, text=str(value), style="Muted.TLabel").pack(anchor="w")
            self.operator_frame.columnconfigure(index % 3, weight=1)

    def _refresh_phase_list(self) -> None:
        for item in self.phase_tree.get_children():
            self.phase_tree.delete(item)
        phases = self.snapshot["migration"]["phases"]
        done = total = 0
        for phase in phases:
            flags = self.snapshot["migration"]["checklist_completed"][phase["id"]]
            completed = sum(flags)
            count = len(flags)
            done += completed
            total += count
            self.phase_tree.insert(
                "", "end", iid=phase["id"],
                values=(STATUS_LABELS.get(phase["status"], phase["status"]),
                        phase["risk"], f"{completed}/{count}"),
            )
        self.progress_var.set((done / total * 100) if total else 0)
        self.progress_text.configure(text=f"{done}/{total} tasks")
        selected = getattr(self, "selected_phase_id", None)
        if selected in self.phase_lookup:
            self.phase_tree.selection_set(selected)
            self._render_phase(selected)
        elif phases:
            current = next(
                (p for p in phases if p["status"] == "in_progress"), phases[0]
            )
            self.phase_tree.selection_set(current["id"])
            self._render_phase(current["id"])

    def _select_phase(self, _event: object = None) -> None:
        selection = self.phase_tree.selection()
        if selection:
            self._render_phase(selection[0])

    def _render_phase(self, phase_id: str) -> None:
        self.selected_phase_id = phase_id
        phase = self.phase_lookup[phase_id]
        self.phase_title.configure(text=phase["title"])
        self.phase_repo.configure(text=f'Target repository: {phase["target_repo"]}')
        self.phase_status.set(phase["status"])
        self.phase_risk.set(phase["risk"])
        for child in self.checklist_frame.winfo_children():
            child.destroy()
        flags = self.snapshot["migration"]["checklist_completed"][phase_id]
        if not phase.get("checklist"):
            ttk.Label(self.checklist_frame, text="No checklist items recorded.",
                      style="Muted.TLabel").pack(anchor="w", padx=8, pady=5)
        for index, text in enumerate(phase.get("checklist", [])):
            variable = tk.BooleanVar(value=flags[index])
            ttk.Checkbutton(
                self.checklist_frame, text=text, variable=variable,
                command=lambda i=index, v=variable: self._toggle_checklist(i, v.get()),
            ).pack(anchor="w", padx=8, pady=3)
        self.phase_notes.delete("1.0", "end")
        self.phase_notes.insert("1.0", phase.get("notes", ""))

    def _update_phase_field(self, _event: object = None) -> None:
        phase = self.phase_lookup.get(getattr(self, "selected_phase_id", ""))
        if phase is None:
            return
        phase["status"] = self.phase_status.get()
        phase["risk"] = self.phase_risk.get()
        self._save_state()
        self._refresh_phase_list()

    def _toggle_checklist(self, index: int, value: bool) -> None:
        phase_id = self.selected_phase_id
        self.snapshot["migration"]["checklist_completed"][phase_id][index] = value
        self._save_state()
        self._refresh_phase_list()

    def _schedule_save_phase_notes(self, _event: object = None) -> None:
        self._schedule_notes_save()

    def _schedule_save_global_notes(self, _event: object = None) -> None:
        self._schedule_notes_save()

    def _schedule_notes_save(self) -> None:
        if self.save_job:
            self.after_cancel(self.save_job)
        self.save_job = self.after(500, self._flush_notes)

    def _flush_notes(self) -> None:
        self.save_job = None
        phase = self.phase_lookup.get(getattr(self, "selected_phase_id", ""))
        if phase is not None:
            phase["notes"] = self.phase_notes.get("1.0", "end-1c")
        self.snapshot["migration"]["global_notes"] = self.global_notes.get(
            "1.0", "end-1c"
        )
        self._save_state()

    def _close(self) -> None:
        if self.save_job:
            self.after_cancel(self.save_job)
            self.save_job = None
        self._flush_notes()
        self.destroy()

    def _save_state(self) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.state_path.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(self.snapshot, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            temporary.replace(self.state_path)
            self.status_var.set(f"Saved locally · {self.state_path}")
        except OSError as exc:
            self.status_var.set(f"Could not save local state: {exc}")

    def _copy_text(self, value: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(value)
        self.status_var.set("Copied to clipboard.")

    def _copy_validation_command(self) -> None:
        selection = self.validation_tree.selection()
        if selection:
            self._copy_text(self.validation_rows[selection[0]])

    def _copy_all_validation_commands(self) -> None:
        commands = [item.command for item in all_validation_commands()]
        self._copy_text("\n".join(commands))

    def _generate_phase_prompt(self, _event: object = None) -> None:
        phase_id = self.prompt_ids.get(self.prompt_phase.get())
        if phase_id is None:
            return
        phase_data = self.phase_lookup.get(phase_id)
        if phase_data is not None:
            self._set_prompt(generate_phase_prompt(MigrationPhase(**phase_data)))

    def _generate_next_prompt(self) -> None:
        phases = [
            MigrationPhase(**phase)
            for phase in self.snapshot["migration"]["phases"]
        ]
        self._set_prompt(generate_next_best_task_prompt(phases))

    def _set_prompt(self, prompt: str) -> None:
        self.prompt_text.delete("1.0", "end")
        self.prompt_text.insert("1.0", prompt)

    def _copy_prompt(self) -> None:
        self._copy_text(self.prompt_text.get("1.0", "end-1c"))

    def _refresh_v1_runs(self) -> None:
        for item in self.run_tree.get_children():
            self.run_tree.delete(item)
        self.run_lookup: dict[str, dict[str, Any]] = {}
        for index, run in enumerate(self.snapshot["v1_runs"]):
            iid = f"run-{index}"
            self.run_lookup[iid] = run
            self.run_tree.insert(
                "", "end", iid=iid,
                values=(
                    run.get("fixture", "unknown fixture"),
                    run.get("status", "unknown"),
                ),
            )
        children = self.run_tree.get_children()
        if children:
            self.run_tree.selection_set(children[0])
            self._select_run()

    def _select_run(self, _event: object = None) -> None:
        selection = self.run_tree.selection()
        if not selection:
            return
        run = self.run_lookup[selection[0]]
        self.run_detail.configure(state="normal")
        self.run_detail.delete("1.0", "end")
        self.run_detail.insert("1.0", json.dumps(run, indent=2, ensure_ascii=False))
        self.run_detail.configure(state="disabled")

    def _import_v1_jsonl(self) -> None:
        path = filedialog.askopenfilename(
            title="Import V1 JSONL",
            filetypes=(("JSON Lines", "*.jsonl"), ("All files", "*")),
        )
        if not path:
            return
        try:
            from huey.gui.v1_runs import load_jsonl
            imported = [asdict(run) for run in load_jsonl(Path(path))]
        except (OSError, ValueError) as exc:
            messagebox.showerror("Import failed", str(exc))
            return
        self.snapshot["v1_runs"] = imported
        self._save_state()
        self._refresh_v1_runs()

    def _export_v1_runs(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export V1 runs", defaultextension=".json",
            filetypes=(("JSON", "*.json"),)
        )
        if not path:
            return
        try:
            Path(path).write_text(
                json.dumps(self.snapshot["v1_runs"], indent=2, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.status_var.set(f"Exported runs to {path}")

    def _export_state(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export Command Center state", defaultextension=".json",
            filetypes=(("JSON", "*.json"),)
        )
        if not path:
            return
        try:
            Path(path).write_text(
                json.dumps(self.snapshot, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.status_var.set(f"Exported dashboard state to {path}")

    def _import_state(self) -> None:
        path = filedialog.askopenfilename(
            title="Import Command Center state", filetypes=(("JSON", "*.json"),)
        )
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            imported = _validated_snapshot(payload)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror("Import failed", str(exc))
            return
        self.snapshot = imported
        self.phase_lookup = {
            phase["id"]: phase for phase in self.snapshot["migration"]["phases"]
        }
        self.global_notes.delete("1.0", "end")
        self.global_notes.insert("1.0", self.snapshot["migration"]["global_notes"])
        self._render_operator_panel()
        self.prompt_ids = {
            f'{phase["title"]} [{phase["id"]}]': phase["id"]
            for phase in self.snapshot["migration"]["phases"]
        }
        self.prompt_box.configure(values=tuple(self.prompt_ids))
        self._refresh_phase_list()
        self._refresh_v1_runs()
        self._save_state()
        messagebox.showinfo("Import complete", "Validated dashboard state imported.")

    def _reset_state(self) -> None:
        if not messagebox.askyesno(
            "Reset dashboard",
            "Replace migration progress and sample run data with project defaults?",
        ):
            return
        self.snapshot = _initial_snapshot()
        self.phase_lookup = {
            phase["id"]: phase for phase in self.snapshot["migration"]["phases"]
        }
        self.global_notes.delete("1.0", "end")
        self.global_notes.insert("1.0", "")
        self._render_operator_panel()
        self._refresh_phase_list()
        self._refresh_v1_runs()
        self._save_state()


def main() -> None:
    """Start the native Command Center desktop dashboard."""
    CommandCenterDesktop().mainloop()


if __name__ == "__main__":
    main()
