# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Main UI module (huey/memory/PY)

from __future__ import annotations

import logging
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

os.environ.setdefault("MONKEY_HEAD_LIGHT_IMPORTS", "1")

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:  # pragma: no cover - optional dependency
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
except ImportError:  # pragma: no cover - can't import GUI libs
    tk = None
    filedialog = None
    messagebox = None
    scrolledtext = None
    simpledialog = None
    ttk = None

from huey.apps.command_center.cli import open_command_center
from huey.config_toggle_gui import run_config_toggle_gui
from huey.gui import EventBus, EventType, build_default_state
from huey.gui.process import build_gui_process_command, build_gui_process_env
from huey.gui.surfaces import (
    GuiActionSection,
    action_lookup,
    default_gui_actions,
    default_gui_sections,
    default_gui_surfaces,
    search_gui_actions,
    section_actions,
)
from huey.gui.theme import as_tk_palette
from huey.gui_scaling import apply_scaling
from huey.install_gui import launch_install_gui as launch_graphical_install
from huey.license_gui import show_license_gui
from huey.media.media_conversion import convert_media
from huey.memory.PY.ai_tools_gui import run_ai_tools
from huey.memory.PY.dashboard import launch_dashboard
from huey.memory.PY.preload_data import preload_all
from huey.os.core.platform_support import (
    build_platform_script_command,
    detect_host_platform,
    find_project_root,
    resolve_platform_script_paths,
)
from huey.services.container_management import (
    build_docker_image,
    cleanup_images,
    cleanup_kubernetes,
    deploy_kubernetes,
    get_pod_logs,
    manage_containers,
    manage_networks,
    manage_volumes,
    scale_deployment,
    stop_containers,
)
from huey.simple_chat_gui import run_simple_chat

_PALETTE = as_tk_palette()
DARK_BG = _PALETTE["background"]
PANEL_BG = _PALETTE["panel"]
PANEL_ALT_BG = _PALETTE["panel_alt"]
LIGHT_FG = _PALETTE["text"]
MUTED_FG = _PALETTE["muted_text"]
ACCENT_PURPLE = _PALETTE["accent"]
SUCCESS_GREEN = _PALETTE["success"]
WARNING_GOLD = _PALETTE["warning"]
BORDER = _PALETTE["border"]

logger = logging.getLogger(__name__)

_WRAP_SIDEBAR = 250
_WRAP_CONTENT = 620


@dataclass(frozen=True)
class LauncherAction:
    label: str
    description: str
    command: Callable[[], None]


class MainUI:
    """Tkinter launcher for the HueyOS desktop tooling."""

    def __init__(self, root):
        if tk is None:
            raise RuntimeError("tkinter is not available")

        self.root = root
        self.project_root = find_project_root(Path(__file__).resolve())
        self.gui_actions = default_gui_actions()
        self.gui_action_map = action_lookup(self.gui_actions)
        self.gui_sections = default_gui_sections()
        self.gui_surfaces = default_gui_surfaces(self.gui_actions)
        self.action_tab_ids, self.action_tab_titles = self._build_action_tab_index()
        self.state = build_default_state()
        self.event_bus = EventBus()
        self.background_image = None
        self.background_label = None
        self.surface_tab_frames: dict[str, tk.Frame] = {}
        self.surface_tab_titles: dict[str, str] = {}
        self.surface_var = tk.StringVar(value="Launch Pad")
        self.workflow_hint_var = tk.StringVar(
            value=(
                "Move from setup into the connected windows, dialogs, and browser "
                "surfaces without leaving the same control deck."
            )
        )
        self.quick_access_var = tk.StringVar(value="")
        self.quick_access_matches = list(self.gui_actions)
        self.activity_var = tk.StringVar(value="Waiting for the first action.")
        self.repository_var = tk.StringVar(value="DylanLRPollock/Monkey-Head-Project")
        self.platform_var = tk.StringVar(
            value=detect_host_platform().runtime_display_name
        )
        self.memory_var = tk.StringVar(value=self.state.memory.root_path)
        self.install_path_var = tk.StringVar(value="Detecting...")
        self.update_path_var = tk.StringVar(value="Detecting...")
        self.run_path_var = tk.StringVar(value="Detecting...")

        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._handle_event)

        mode = self.choose_screen_mode()
        apply_scaling(self.root, mode)
        self.apply_dark_theme()
        self.root.title("HueyOS Control Deck")
        self.root.minsize(980, 720)
        self.executor = ThreadPoolExecutor(max_workers=os.cpu_count() or 4)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_paths()
        self._bootstrap_state()
        self.create_menu()
        self.create_widgets()
        self._bind_navigation_shortcuts()
        self.apply_background_image()
        self.check_license()
        self.log_message("HueyOS control deck ready.")

    def apply_dark_theme(self) -> None:
        """Configure Tk widgets to use the canonical HueyOS theme."""

        if tk is None:
            return

        self.root.configure(
            bg=DARK_BG,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
        )

        if ttk is not None:
            style = ttk.Style(self.root)
            try:
                style.theme_use("clam")
            except (RuntimeError, AttributeError, tk.TclError) as exc:
                logger.debug("Unable to apply ttk theme: %s", exc)
            style.configure("TLabel", background=DARK_BG, foreground=LIGHT_FG)
            style.configure(
                "TButton",
                background=ACCENT_PURPLE,
                foreground=LIGHT_FG,
                relief=tk.RAISED,
                borderwidth=1,
                focusthickness=0,
            )
            style.map(
                "TButton",
                background=[("active", PANEL_ALT_BG), ("pressed", SUCCESS_GREEN)],
                foreground=[("active", LIGHT_FG), ("pressed", LIGHT_FG)],
            )
            style.configure(
                "TNotebook",
                background=DARK_BG,
                borderwidth=0,
                tabmargins=(0, 0, 0, 0),
            )
            style.configure(
                "TNotebook.Tab",
                background=PANEL_ALT_BG,
                foreground=LIGHT_FG,
                padding=(14, 10),
            )
            style.map(
                "TNotebook.Tab",
                background=[("selected", ACCENT_PURPLE)],
                foreground=[("selected", LIGHT_FG)],
            )
            style.configure(
                "TProgressbar",
                troughcolor=PANEL_BG,
                background=SUCCESS_GREEN,
                bordercolor=BORDER,
                lightcolor=SUCCESS_GREEN,
                darkcolor=SUCCESS_GREEN,
            )
            style.configure(
                "TCombobox",
                fieldbackground=PANEL_ALT_BG,
                background=PANEL_ALT_BG,
                foreground=LIGHT_FG,
            )

    def _bootstrap_state(self) -> None:
        self.state.operator.selected_repository = self.repository_var.get()
        self.state.operator.active_view = "launch-pad"
        self._refresh_path_vars()
        self._emit_event(
            EventType.REPOSITORY_CHANGED,
            {"repository": self.repository_var.get()},
            source="launcher",
        )
        self._emit_event(
            EventType.MEMORY_UPDATED, {"indexed_documents": 0}, source="memory"
        )

    def _find_background_image(self) -> Path | None:
        """Locate the HueyOS background image from the repository root."""

        for parent in Path(__file__).resolve().parents:
            candidate = parent / "HueyOS-background.png"
            if candidate.exists():
                return candidate
        return None

    def apply_background_image(self) -> None:
        """Place the HueyOS background image behind the main window widgets."""

        if tk is None:
            return

        image_path = self._find_background_image()
        if image_path is None:
            return
        try:
            self.background_image = tk.PhotoImage(file=str(image_path))
        except (RuntimeError, AttributeError, OSError) as exc:
            logger.debug("Failed to load background image: %s", exc)
            return
        self.background_label = tk.Label(
            self.root, image=self.background_image, bg=DARK_BG
        )
        self.background_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.background_label.lower()

    def choose_screen_mode(self) -> str:
        """Ask the user which display mode to use or read from ``SCREEN_MODE``."""

        env_mode = os.environ.get("SCREEN_MODE")
        if env_mode in {"1080p", "4k", "custom"}:
            return env_mode

        if simpledialog is not None:
            mode = simpledialog.askstring(
                "Display Mode",
                "Choose display mode: 1080p, 4k, or custom",
                initialvalue="1080p",
            )
            if mode and mode.lower() in {"1080p", "4k", "custom"}:
                mode = mode.lower()
                if mode == "custom":
                    factor = simpledialog.askfloat(
                        "Scaling Factor",
                        "Enter scaling factor",
                        minvalue=0.5,
                        maxvalue=5.0,
                    )
                    if factor is not None:
                        os.environ["SCREEN_FACTOR"] = str(factor)
                    font = simpledialog.askinteger(
                        "Font Size",
                        "Enter base font size",
                        minvalue=6,
                        maxvalue=24,
                    )
                    if font is not None:
                        os.environ["SCREEN_FONT_SIZE"] = str(font)
                return mode
        return "1080p"

    def setup_paths(self):
        """Determine installer paths based on the current platform."""

        paths = resolve_platform_script_paths(self.project_root)
        self.install_path = paths.install
        self.update_path = paths.update
        self.run_path = paths.run
        self._refresh_path_vars()

    def _refresh_path_vars(self) -> None:
        self.install_path_var.set(self._display_path(self.install_path))
        self.update_path_var.set(self._display_path(self.update_path))
        self.run_path_var.set(self._display_path(self.run_path))

    @staticmethod
    def _display_path(path: Path | None) -> str:
        if path is None:
            return "Unavailable on this platform"
        return str(path)

    def _build_action_tab_index(self) -> tuple[dict[str, str], dict[str, str]]:
        tab_ids: dict[str, str] = {}
        tab_titles: dict[str, str] = {}
        for section in self.gui_sections:
            for action_id in section.action_ids:
                tab_ids.setdefault(action_id, section.tab_id)
                tab_titles.setdefault(action_id, section.tab_title)
        return tab_ids, tab_titles

    def create_menu(self):
        menu_bar = tk.Menu(self.root, bg=DARK_BG, fg=LIGHT_FG, tearoff=0)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
        file_menu.add_command(label="Install", command=self.install)
        file_menu.add_command(
            label="Graphical Installer", command=self.launch_install_gui
        )
        file_menu.add_command(label="Run", command=self.run)
        file_menu.add_command(label="Update", command=self.update)
        file_menu.add_command(label="Clear Log", command=self.clear_log)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menu_bar.add_cascade(label="Launcher", menu=file_menu)

        surfaces_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
        surfaces_menu.add_command(
            label="Command Center", command=self.launch_command_center
        )
        surfaces_menu.add_command(label="Simple Chat", command=self.launch_simple_chat)
        surfaces_menu.add_command(label="AI Console", command=self.launch_ai_tools)
        surfaces_menu.add_command(label="Dashboard", command=self.launch_dashboard)
        surfaces_menu.add_command(
            label="Config Toggles", command=self.show_config_toggles
        )
        surfaces_menu.add_command(label="License", command=self.show_license)
        menu_bar.add_cascade(label="Surfaces", menu=surfaces_menu)

        ops_menu = tk.Menu(menu_bar, tearoff=0, bg=DARK_BG, fg=LIGHT_FG)
        ops_menu.add_command(label="Data Summary", command=self.show_data_summary)
        ops_menu.add_command(label="Convert Media", command=self.convert_media_prompt)
        ops_menu.add_separator()
        ops_menu.add_command(label="Build Image", command=self.build_image)
        ops_menu.add_command(label="Start Containers", command=self.start_containers)
        ops_menu.add_command(label="Stop Containers", command=self.stop_containers)
        ops_menu.add_command(label="Manage Volumes", command=self.manage_volumes)
        ops_menu.add_command(label="Manage Networks", command=self.manage_networks)
        ops_menu.add_separator()
        ops_menu.add_command(label="Deploy Kubernetes", command=self.deploy_kubernetes)
        ops_menu.add_command(
            label="Scale Deployment", command=self.scale_deployment_prompt
        )
        ops_menu.add_command(label="Get Pod Logs", command=self.get_pod_logs_prompt)
        ops_menu.add_command(
            label="Cleanup Kubernetes", command=self.cleanup_kubernetes
        )
        menu_bar.add_cascade(label="Operations", menu=ops_menu)

    def create_widgets(self):
        shell = tk.Frame(self.root, bg=DARK_BG)
        shell.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        self._build_header(shell)

        body = tk.Frame(shell, bg=DARK_BG)
        body.pack(fill=tk.BOTH, expand=True)

        sidebar = tk.Frame(body, bg=DARK_BG)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))

        main_panel = tk.Frame(body, bg=DARK_BG)
        main_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_sidebar(sidebar)
        self._build_main_panel(main_panel)
        self._build_footer(shell)
        self._refresh_overview()

    def _build_header(self, parent) -> None:
        card = self._make_card(parent)
        title = tk.Label(
            card,
            text="HueyOS Control Deck",
            bg=PANEL_BG,
            fg=LIGHT_FG,
            font=("Segoe UI", 22, "bold"),
        )
        title.pack(anchor=tk.W, padx=18, pady=(16, 4))
        subtitle = tk.Label(
            card,
            text=(
                "Guide setup, connected windows, browser surfaces, and runtime "
                "operations without freezing the main window."
            ),
            bg=PANEL_BG,
            fg=MUTED_FG,
            justify=tk.LEFT,
            wraplength=_WRAP_CONTENT,
        )
        subtitle.pack(anchor=tk.W, padx=18)
        badge = tk.Label(
            card,
            text="Install -> Connect -> Explore -> Operate",
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            padx=12,
            pady=6,
        )
        badge.pack(anchor=tk.W, padx=18, pady=(12, 16))

    def _build_sidebar(self, parent) -> None:
        flow_card = self._make_card(parent, width=300)
        self._add_card_heading(
            flow_card,
            "Guided flow",
            "Move through the launcher in one clear order instead of bouncing between disconnected tools.",
            wraplength=_WRAP_SIDEBAR,
        )
        for title, detail in (
            ("1. Setup", "Install or update the local scripts and launch helpers."),
            (
                "2. Launch",
                "Run the core entrypoint once the local environment is ready.",
            ),
            (
                "3. Explore",
                "Open the Command Center, chat, AI console, dashboard, and popups from one unified shell.",
            ),
            (
                "4. Operate",
                "Handle media conversion plus Docker or Kubernetes operations.",
            ),
        ):
            self._add_flow_step(flow_card, title, detail)

        focus_card = self._make_card(parent)
        self._add_card_heading(
            focus_card,
            "Current focus",
            "The launcher updates this guidance as you move between views and tasks.",
            wraplength=_WRAP_SIDEBAR,
        )
        tk.Label(
            focus_card,
            textvariable=self.surface_var,
            bg=PANEL_BG,
            fg=LIGHT_FG,
            font=("Segoe UI", 14, "bold"),
            anchor=tk.W,
            justify=tk.LEFT,
        ).pack(fill=tk.X, padx=18)
        tk.Label(
            focus_card,
            textvariable=self.workflow_hint_var,
            bg=PANEL_BG,
            fg=MUTED_FG,
            justify=tk.LEFT,
            wraplength=_WRAP_SIDEBAR,
        ).pack(fill=tk.X, padx=18, pady=(6, 16))

        quick_access_card = self._make_card(parent)
        self._add_card_heading(
            quick_access_card,
            "Quick access",
            "Search actions, jump between tabs, and open functions without scanning every section manually.",
            wraplength=_WRAP_SIDEBAR,
        )
        nav_row = tk.Frame(quick_access_card, bg=PANEL_BG)
        nav_row.pack(fill=tk.X, padx=18, pady=(0, 10))
        for tab_id, label in (
            ("launch-pad", "Launch"),
            ("connectors-and-windows", "Windows"),
            ("runtime-ops", "Runtime"),
        ):
            tk.Button(
                nav_row,
                text=label,
                command=lambda target=tab_id: self.select_tab(target),
                bg=ACCENT_PURPLE,
                fg=LIGHT_FG,
                activebackground=PANEL_ALT_BG,
                activeforeground=LIGHT_FG,
                padx=8,
                pady=4,
            ).pack(side=tk.LEFT, padx=(0, 6))
        self.quick_access_entry = tk.Entry(
            quick_access_card,
            textvariable=self.quick_access_var,
            bg=PANEL_ALT_BG,
            fg=LIGHT_FG,
            insertbackground=LIGHT_FG,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
        )
        self.quick_access_entry.pack(fill=tk.X, padx=18, pady=(0, 8))
        self.quick_access_entry.bind("<Return>", self.launch_quick_access_selection)
        tk.Label(
            quick_access_card,
            text="Ctrl+K focuses search. Enter or double-click opens the selected function.",
            bg=PANEL_BG,
            fg=MUTED_FG,
            justify=tk.LEFT,
            wraplength=_WRAP_SIDEBAR,
        ).pack(fill=tk.X, padx=18, pady=(0, 8))
        self.quick_access_listbox = tk.Listbox(
            quick_access_card,
            height=7,
            bg=PANEL_ALT_BG,
            fg=LIGHT_FG,
            selectbackground=ACCENT_PURPLE,
            selectforeground=LIGHT_FG,
            activestyle="none",
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
        )
        self.quick_access_listbox.pack(fill=tk.X, padx=18, pady=(0, 8))
        self.quick_access_listbox.bind(
            "<Double-Button-1>", self.launch_quick_access_selection
        )
        self.quick_access_listbox.bind("<Return>", self.launch_quick_access_selection)
        button_row = tk.Frame(quick_access_card, bg=PANEL_BG)
        button_row.pack(fill=tk.X, padx=18, pady=(0, 16))
        tk.Button(
            button_row,
            text="Open Selected",
            command=self.launch_quick_access_selection,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=PANEL_ALT_BG,
            activeforeground=LIGHT_FG,
            padx=8,
            pady=4,
        ).pack(side=tk.LEFT)
        tk.Button(
            button_row,
            text="Clear Search",
            command=self.clear_quick_access,
            bg=ACCENT_PURPLE,
            fg=LIGHT_FG,
            activebackground=PANEL_ALT_BG,
            activeforeground=LIGHT_FG,
            padx=8,
            pady=4,
        ).pack(side=tk.LEFT, padx=(6, 0))
        self.quick_access_var.trace_add(
            "write", lambda *_args: self.refresh_quick_access_results()
        )
        self.refresh_quick_access_results()

        surfaces_card = self._make_card(parent)
        self._add_card_heading(
            surfaces_card,
            "Connected surfaces",
            "Every maintained GUI window, popup, and browser surface is listed here so the unified shell can stay the single front door.",
            wraplength=_WRAP_SIDEBAR,
        )
        mode_labels = {
            "browser": "Browser",
            "dialog": "Popup",
            "window": "Window",
        }
        for action in self.gui_surfaces:
            row = tk.Frame(
                surfaces_card,
                bg=PANEL_ALT_BG,
                highlightbackground=BORDER,
                highlightcolor=BORDER,
                highlightthickness=1,
                bd=0,
            )
            row.pack(fill=tk.X, padx=18, pady=(0, 8))
            copy = tk.Frame(row, bg=PANEL_ALT_BG)
            copy.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0), pady=10)
            tk.Label(
                copy,
                text=action.label,
                bg=PANEL_ALT_BG,
                fg=LIGHT_FG,
                font=("Segoe UI", 10, "bold"),
                anchor=tk.W,
            ).pack(fill=tk.X)
            tk.Label(
                copy,
                text=action.description,
                bg=PANEL_ALT_BG,
                fg=MUTED_FG,
                justify=tk.LEFT,
                anchor=tk.W,
                wraplength=_WRAP_SIDEBAR - 60,
            ).pack(fill=tk.X, pady=(4, 0))
            tk.Label(
                row,
                text=mode_labels.get(action.launch_mode, action.launch_mode.title()),
                bg=ACCENT_PURPLE,
                fg=LIGHT_FG,
                padx=8,
                pady=4,
            ).pack(side=tk.RIGHT, padx=12)

        system_card = self._make_card(parent)
        self._add_card_heading(
            system_card,
            "System map",
            "Keep the important local paths visible while you work.",
            wraplength=_WRAP_SIDEBAR,
        )
        self._add_key_value(system_card, "Repository", self.repository_var)
        self._add_key_value(system_card, "Platform", self.platform_var)
        self._add_key_value(system_card, "Memory root", self.memory_var)
        self._add_key_value(system_card, "Install script", self.install_path_var)
        self._add_key_value(system_card, "Update script", self.update_path_var)
        self._add_key_value(system_card, "Run script", self.run_path_var)

        activity_card = self._make_card(parent)
        self._add_card_heading(
            activity_card,
            "Recent activity",
            "The most recent launcher events stay visible here even while child windows stay open.",
            wraplength=_WRAP_SIDEBAR,
        )
        tk.Label(
            activity_card,
            textvariable=self.activity_var,
            bg=PANEL_BG,
            fg=MUTED_FG,
            justify=tk.LEFT,
            wraplength=_WRAP_SIDEBAR,
        ).pack(fill=tk.X, padx=18, pady=(0, 16))

    def _build_main_panel(self, parent) -> None:
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)
        if hasattr(notebook, "bind"):
            notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self.surface_notebook = notebook

        tab_frames: dict[str, tk.Frame] = {}
        tab_titles: dict[str, str] = {}
        for section in self.gui_sections:
            frame = tab_frames.get(section.tab_id)
            if frame is None:
                frame = tk.Frame(notebook, bg=DARK_BG)
                notebook.add(frame, text=section.tab_title)
                tab_frames[section.tab_id] = frame
                tab_titles[section.tab_id] = section.tab_title
            self._build_action_card(
                frame,
                section.title,
                section.description,
                self._launcher_actions_for(section),
            )
        self.surface_tab_frames = tab_frames
        self.surface_tab_titles = tab_titles

        log_card = self._make_card(parent)
        self._add_card_heading(
            log_card,
            "Activity log",
            "Command output and launch history stay anchored here while the rest of the interface remains available.",
            wraplength=_WRAP_CONTENT,
        )
        self.log_text = scrolledtext.ScrolledText(
            log_card,
            wrap=getattr(tk, "WORD", "word"),
            bg=PANEL_ALT_BG,
            fg=LIGHT_FG,
            insertbackground=LIGHT_FG,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
            height=16,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 18))

    def _build_footer(self, parent) -> None:
        footer = self._make_card(parent, pady=(14, 0))
        self.progress = ttk.Progressbar(
            footer, orient=tk.HORIZONTAL, mode="indeterminate"
        )
        self.progress.pack(fill=tk.X, padx=18, pady=(18, 10))
        self.status_label = tk.Label(
            footer,
            text="Status: Ready",
            bd=0,
            relief=tk.FLAT,
            anchor=tk.W,
            bg=PANEL_BG,
            fg=LIGHT_FG,
        )
        self.status_label.pack(fill=tk.X, padx=18, pady=(0, 18))

    def _make_card(self, parent, *, width: int | None = None, pady=(0, 14)):
        frame = tk.Frame(
            parent,
            bg=PANEL_BG,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
            bd=0,
        )
        if width is not None:
            frame.configure(width=width)
            frame.pack_propagate(False)
        frame.pack(fill=tk.X, pady=pady)
        return frame

    @staticmethod
    def _add_card_heading(
        card, title: str, description: str, *, wraplength: int
    ) -> None:
        tk.Label(
            card,
            text=title,
            bg=PANEL_BG,
            fg=LIGHT_FG,
            font=("Segoe UI", 15, "bold"),
            anchor=tk.W,
            justify=tk.LEFT,
        ).pack(fill=tk.X, padx=18, pady=(16, 4))
        tk.Label(
            card,
            text=description,
            bg=PANEL_BG,
            fg=MUTED_FG,
            justify=tk.LEFT,
            wraplength=wraplength,
        ).pack(fill=tk.X, padx=18, pady=(0, 14))

    @staticmethod
    def _add_flow_step(card, title: str, detail: str) -> None:
        step = tk.Frame(
            card,
            bg=PANEL_ALT_BG,
            highlightbackground=BORDER,
            highlightcolor=BORDER,
            highlightthickness=1,
            bd=0,
        )
        step.pack(fill=tk.X, padx=18, pady=(0, 10))
        tk.Label(
            step,
            text=title,
            bg=PANEL_ALT_BG,
            fg=LIGHT_FG,
            font=("Segoe UI", 11, "bold"),
            anchor=tk.W,
            justify=tk.LEFT,
        ).pack(fill=tk.X, padx=12, pady=(10, 4))
        tk.Label(
            step,
            text=detail,
            bg=PANEL_ALT_BG,
            fg=MUTED_FG,
            justify=tk.LEFT,
            wraplength=_WRAP_SIDEBAR - 24,
        ).pack(fill=tk.X, padx=12, pady=(0, 10))

    @staticmethod
    def _add_key_value(card, label: str, variable) -> None:
        row = tk.Frame(card, bg=PANEL_BG)
        row.pack(fill=tk.X, padx=18, pady=(0, 10))
        tk.Label(
            row,
            text=f"{label}:",
            bg=PANEL_BG,
            fg=WARNING_GOLD,
            justify=tk.LEFT,
            anchor=tk.W,
        ).pack(fill=tk.X)
        tk.Label(
            row,
            textvariable=variable,
            bg=PANEL_BG,
            fg=LIGHT_FG,
            justify=tk.LEFT,
            anchor=tk.W,
            wraplength=_WRAP_SIDEBAR,
        ).pack(fill=tk.X)

    def _build_action_card(
        self,
        parent,
        title: str,
        description: str,
        actions: Sequence[LauncherAction],
    ) -> None:
        card = self._make_card(parent)
        self._add_card_heading(card, title, description, wraplength=_WRAP_CONTENT)
        for action in actions:
            row = tk.Frame(
                card,
                bg=PANEL_ALT_BG,
                highlightbackground=BORDER,
                highlightcolor=BORDER,
                highlightthickness=1,
                bd=0,
            )
            row.pack(fill=tk.X, padx=18, pady=(0, 10))
            copy = tk.Frame(row, bg=PANEL_ALT_BG)
            copy.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 0), pady=12)
            tk.Label(
                copy,
                text=action.label,
                bg=PANEL_ALT_BG,
                fg=LIGHT_FG,
                font=("Segoe UI", 11, "bold"),
                anchor=tk.W,
            ).pack(fill=tk.X)
            tk.Label(
                copy,
                text=action.description,
                bg=PANEL_ALT_BG,
                fg=MUTED_FG,
                justify=tk.LEFT,
                anchor=tk.W,
                wraplength=420,
            ).pack(fill=tk.X, pady=(4, 0))
            tk.Button(
                row,
                text=action.label,
                command=self._focus_action(
                    action.label, action.description, action.command
                ),
                bg=ACCENT_PURPLE,
                fg=LIGHT_FG,
                activebackground=PANEL_ALT_BG,
                activeforeground=LIGHT_FG,
                padx=14,
                pady=6,
            ).pack(side=tk.RIGHT, padx=12, pady=12)

    def _launcher_actions_for(self, section: GuiActionSection) -> list[LauncherAction]:
        handlers = self._action_handlers()
        actions: list[LauncherAction] = []
        for action in section_actions(section, self.gui_actions):
            handler = handlers.get(action.id)
            if handler is None:
                logger.warning("No handler registered for GUI action %s", action.id)
                continue
            actions.append(
                LauncherAction(
                    label=action.label,
                    description=action.description,
                    command=handler,
                )
            )
        return actions

    def refresh_quick_access_results(self) -> None:
        query = self.quick_access_var.get()
        self.quick_access_matches = list(search_gui_actions(query, self.gui_actions))
        listbox = getattr(self, "quick_access_listbox", None)
        if listbox is None:
            return
        listbox.delete(0, getattr(tk, "END", "end"))
        for action in self.quick_access_matches:
            tab_title = self.action_tab_titles.get(action.id, "Launch Pad")
            launch_mode = action.launch_mode.replace("-", " ").title()
            listbox.insert(
                getattr(tk, "END", "end"),
                f"{action.label} | {launch_mode} | {tab_title}",
            )
        if self.quick_access_matches:
            listbox.selection_set(0)

    def clear_quick_access(self) -> None:
        self.quick_access_var.set("")
        self._focus_quick_access()

    def _focus_quick_access(self, _event=None) -> str:
        entry = getattr(self, "quick_access_entry", None)
        if entry is not None:
            entry.focus_set()
            if hasattr(entry, "selection_range"):
                entry.selection_range(0, getattr(tk, "END", "end"))
        return "break"

    def launch_quick_access_selection(self, _event=None) -> str:
        if not self.quick_access_matches:
            return "break"
        listbox = getattr(self, "quick_access_listbox", None)
        selected_index = 0
        if listbox is not None and hasattr(listbox, "curselection"):
            selection = listbox.curselection()
            if selection:
                selected_index = int(selection[0])
        action = self.quick_access_matches[selected_index]
        self._execute_gui_action(action.id)
        return "break"

    def _execute_gui_action(self, action_id: str) -> None:
        action = self.gui_action_map.get(action_id)
        if action is None:
            return
        tab_id = self.action_tab_ids.get(action_id)
        if tab_id:
            self.select_tab(tab_id)
        self.surface_var.set(action.label)
        self.workflow_hint_var.set(action.description)
        handler = self._action_handlers().get(action_id)
        if handler is not None:
            handler()

    def _action_handlers(self) -> dict[str, Callable[[], None]]:
        return {
            "install": self.install,
            "graphical-installer": self.launch_install_gui,
            "run": self.run,
            "update": self.update,
            "clear-log": self.clear_log,
            "command-center": self.launch_command_center,
            "data-summary": self.show_data_summary,
            "license": self.show_license,
            "config-toggles": self.show_config_toggles,
            "simple-chat": self.launch_simple_chat,
            "ai-console": self.launch_ai_tools,
            "dashboard": self.launch_dashboard,
            "convert-media": self.convert_media_prompt,
            "build-image": self.build_image,
            "start-containers": self.start_containers,
            "stop-containers": self.stop_containers,
            "manage-volumes": self.manage_volumes,
            "manage-networks": self.manage_networks,
            "deploy-kubernetes": self.deploy_kubernetes,
            "scale-deployment": self.scale_deployment_prompt,
            "get-pod-logs": self.get_pod_logs_prompt,
            "cleanup-kubernetes": self.cleanup_kubernetes,
        }

    def select_tab(self, tab_id: str) -> None:
        notebook = getattr(self, "surface_notebook", None)
        frame = self.surface_tab_frames.get(tab_id)
        if notebook is None or frame is None:
            return
        notebook.select(frame)
        self.surface_var.set(self.surface_tab_titles.get(tab_id, tab_id))
        self.state.operator.active_view = tab_id

    def _bind_navigation_shortcuts(self) -> None:
        if not hasattr(self.root, "bind_all"):
            return
        self.root.bind_all("<Control-k>", self._focus_quick_access)
        self.root.bind_all("<Control-K>", self._focus_quick_access)
        self.root.bind_all(
            "<Control-Key-1>", lambda _event: self.select_tab("launch-pad")
        )
        self.root.bind_all(
            "<Control-Key-2>",
            lambda _event: self.select_tab("connectors-and-windows"),
        )
        self.root.bind_all(
            "<Control-Key-3>", lambda _event: self.select_tab("runtime-ops")
        )

    def _focus_action(
        self, label: str, detail: str, callback: Callable[[], None]
    ) -> Callable[[], None]:
        def wrapped() -> None:
            self.surface_var.set(label)
            self.workflow_hint_var.set(detail)
            callback()

        return wrapped

    def _on_tab_changed(self, _event=None) -> None:
        notebook = getattr(self, "surface_notebook", None)
        if notebook is None:
            return
        current = notebook.tab(notebook.select(), "text")
        self.surface_var.set(current)
        normalized = current.lower().replace(" & ", "-").replace(" ", "-")
        self.state.operator.active_view = normalized

    def _emit_event(
        self,
        event_type: EventType | str,
        payload: dict[str, object] | None = None,
        *,
        source: str,
    ) -> None:
        self.event_bus.emit(event_type, payload, source=source)

    def _handle_event(self, event) -> None:
        self.state.apply_event(event)
        self._refresh_overview()

    def _refresh_overview(self) -> None:
        runtime_status = self.state.runtime.orchestration_status or "standby"
        self.memory_var.set(self.state.memory.root_path)
        self.platform_var.set(detect_host_platform().runtime_display_name)
        history = self.event_bus.history()
        if not history:
            self.activity_var.set("Waiting for the first action.")
            return

        entries: list[str] = []
        for event in reversed(history[-5:]):
            detail = (
                event.payload.get("action")
                or event.payload.get("status")
                or event.payload.get("repository")
                or "updated"
            )
            label = event.event_type.value.replace("_", " ").title()
            entries.append(f"{label}: {detail}")
        self.activity_var.set("\n".join(entries))
        self.surface_var.set(
            self.surface_var.get() or runtime_status.replace("-", " ").title()
        )

    def _run_on_ui(self, callback: Callable[[], None]) -> None:
        """Schedule ``callback`` on Tk's UI thread when possible."""

        root = getattr(self, "root", None)
        if root is not None and hasattr(root, "after"):
            root.after(0, callback)
        else:
            callback()

    def _set_status(self, text: str) -> None:
        self._run_on_ui(lambda: self.status_label.config(text=text))

    def _start_progress(self) -> None:
        self._run_on_ui(lambda: self.progress.start())

    def _stop_progress(self) -> None:
        self._run_on_ui(lambda: self.progress.stop())

    def log_message(self, message):
        end_token = getattr(tk, "END", "end")

        def append() -> None:
            self.log_text.insert(end_token, str(message).rstrip() + "\n")
            self.log_text.see(end_token)

        self._run_on_ui(append)

    def clear_log(self) -> None:
        """Remove all text from the log window."""

        self.log_text.delete("1.0", getattr(tk, "END", "end"))

    def _track_started(self, action_label: str, *, source: str, status: str) -> None:
        self._emit_event(
            EventType.RUN_STARTED,
            {"action": action_label, "status": status},
            source=source,
        )

    def _track_finished(self, *, source: str, status: str) -> None:
        self._emit_event(EventType.RUN_FINISHED, {"status": status}, source=source)

    def run_script(self, script_path, action_label: str, source: str):
        if script_path is None or not Path(script_path).exists():
            self.log_message(f"Script not found: {script_path}")
            if messagebox is not None:
                self._run_on_ui(
                    lambda: messagebox.showerror(
                        "Error", "Installer script not found for this platform."
                    )
                )
            self._track_finished(
                source=source, status=f"{action_label.lower()} unavailable"
            )
            self._stop_progress()
            self._set_status("Status: Ready")
            return
        try:
            cmd = build_platform_script_command(Path(script_path))
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if process.stdout is not None:
                for line in process.stdout:
                    self.log_message(line)
                process.stdout.close()
            process.wait()
            if process.returncode != 0:
                self.log_message(f"Error: command exited with {process.returncode}")
                self._track_finished(
                    source=source, status=f"{action_label.lower()} failed"
                )
            else:
                self.log_message("Operation completed successfully.")
                self._track_finished(
                    source=source, status=f"{action_label.lower()} complete"
                )
        except Exception as exc:
            self.log_message(f"Exception: {str(exc)}")
            self._track_finished(source=source, status=f"{action_label.lower()} error")
        finally:
            self._stop_progress()
            self._set_status("Status: Ready")

    def install(self):
        self.log_message("Starting installation...")
        self._set_status("Status: Installing")
        self._start_progress()
        self._track_started("Install", source="launch-pad", status="installing")
        self._submit_task(self.run_script, self.install_path, "Install", "launch-pad")

    def run(self):
        self.log_message("Launching application...")
        self._set_status("Status: Running")
        self._start_progress()
        self._track_started("Run", source="launch-pad", status="running")
        self._submit_task(self.run_script, self.run_path, "Run", "launch-pad")

    def update(self):
        self.log_message("Starting update...")
        self._set_status("Status: Updating")
        self._start_progress()
        self._track_started("Update", source="launch-pad", status="updating")
        self._submit_task(self.run_script, self.update_path, "Update", "launch-pad")

    def check_license(self):
        """Display the license agreement if not yet accepted."""

        show_license_gui()

    def show_license(self):
        """Manually open the license dialog."""

        self.log_message("Opening license window...")
        self.surface_var.set("License")
        self.workflow_hint_var.set("Review the current license terms.")
        show_license_gui(force_show=True)
        self._track_finished(source="license", status="license reviewed")

    def show_data_summary(self):
        """Display counts of bundled prompts and memory files."""

        data = preload_all()
        prompts = len(data.get("prompts", []))
        memory_files = sum(len(value) for value in data.get("memory", {}).values())
        self.log_message("Refreshing data summary...")
        self._emit_event(
            EventType.MEMORY_UPDATED,
            {"indexed_documents": memory_files},
            source="memory",
        )
        if messagebox is not None:
            messagebox.showinfo(
                "Data Summary", f"Prompts: {prompts}\nMemory files: {memory_files}"
            )

    def _launch_child_process(
        self,
        *,
        label: str,
        module_name: str,
        function_name: str,
        source: str,
        fallback: Callable[[], None] | None = None,
    ) -> None:
        self.log_message(f"Opening {label}...")
        self._set_status(f"Status: {label} ready")
        self._track_started(label, source=source, status=f"opening {label.lower()}")
        command = build_gui_process_command(module_name, function_name)
        env = build_gui_process_env(self.project_root)
        kwargs: dict[str, object] = {
            "cwd": str(self.project_root),
            "env": env,
        }
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if creationflags:
            kwargs["creationflags"] = creationflags
        try:
            subprocess.Popen(command, **kwargs)
        except Exception as exc:
            self.log_message(f"{label} failed: {exc}")
            if messagebox is not None:
                messagebox.showerror(label, str(exc))
            if fallback is not None:
                self._launch_child_gui(fallback, label)
            self._track_finished(source=source, status=f"{label.lower()} failed")
            return
        self.log_message(f"{label} opened in a separate window.")
        self._track_finished(source=source, status=f"{label.lower()} ready")

    def show_config_toggles(self):
        """Open the configuration toggles window without blocking the launcher."""

        self.workflow_hint_var.set(
            "Adjust the runtime toggles in a separate window and return here when done."
        )
        self._launch_child_process(
            label="Config Toggles",
            module_name="huey.config_toggle_gui",
            function_name="run_config_toggle_gui",
            source="config",
            fallback=run_config_toggle_gui,
        )

    def launch_command_center(self):
        """Open the browser-based Command Center without leaving the desktop shell."""

        self.workflow_hint_var.set(
            "The Command Center opens in your browser while the control deck stays available for every other connected window."
        )
        self._launch_child_process(
            label="Command Center",
            module_name="huey.apps.command_center.cli",
            function_name="open_command_center",
            source="command-center",
            fallback=open_command_center,
        )

    def launch_install_gui(self):
        """Open the graphical installer in a separate process."""

        self.workflow_hint_var.set(
            "The installer opens separately so you can review the license and target profile without leaving the control deck."
        )
        self._launch_child_process(
            label="Graphical Installer",
            module_name="huey.install_gui",
            function_name="launch_install_gui",
            source="installer",
            fallback=launch_graphical_install,
        )

    def _run_container_func(self, func, action_label: str, source: str, *args):
        try:
            func(*args)
            self.log_message("Operation completed successfully.")
            self._track_finished(
                source=source, status=f"{action_label.lower()} complete"
            )
        except Exception as exc:  # pragma: no cover - subprocess failures
            self.log_message(f"Exception: {exc}")
            self._track_finished(source=source, status=f"{action_label.lower()} error")
        finally:
            self._stop_progress()
            self._set_status("Status: Ready")

    def _submit_task(self, func, *args):
        executor = getattr(self, "executor", None)
        if executor is not None:
            executor.submit(func, *args)
        else:  # fallback for tests
            threading.Thread(target=func, args=args).start()

    def build_image(self):
        self.log_message("Building Docker image...")
        self._set_status("Status: Building")
        self._start_progress()
        self._track_started("Build Image", source="runtime", status="building image")
        self._submit_task(
            self._run_container_func, build_docker_image, "Build Image", "runtime"
        )

    def start_containers(self):
        self.log_message("Starting containers...")
        self._set_status("Status: Starting")
        self._start_progress()
        self._track_started(
            "Start Containers", source="runtime", status="starting containers"
        )
        self._submit_task(
            self._run_container_func, manage_containers, "Start Containers", "runtime"
        )

    def stop_containers(self):
        self.log_message("Stopping containers...")
        self._set_status("Status: Stopping")
        self._start_progress()
        self._track_started(
            "Stop Containers", source="runtime", status="stopping containers"
        )
        self._submit_task(
            self._run_container_func, stop_containers, "Stop Containers", "runtime"
        )

    def cleanup_images(self):
        self.log_message("Pruning images...")
        self._set_status("Status: Cleaning")
        self._start_progress()
        self._track_started(
            "Cleanup Images", source="runtime", status="cleaning images"
        )
        self._submit_task(
            self._run_container_func, cleanup_images, "Cleanup Images", "runtime"
        )

    def manage_volumes(self):
        self.log_message("Managing volumes...")
        self._set_status("Status: Volumes")
        self._start_progress()
        self._track_started(
            "Manage Volumes", source="runtime", status="managing volumes"
        )
        self._submit_task(
            self._run_container_func, manage_volumes, "Manage Volumes", "runtime"
        )

    def manage_networks(self):
        self.log_message("Managing networks...")
        self._set_status("Status: Networks")
        self._start_progress()
        self._track_started(
            "Manage Networks", source="runtime", status="managing networks"
        )
        self._submit_task(
            self._run_container_func, manage_networks, "Manage Networks", "runtime"
        )

    def deploy_kubernetes(self):
        self.log_message("Deploying Kubernetes resources...")
        self._set_status("Status: Deploying")
        self._start_progress()
        self._track_started("Deploy", source="kubernetes", status="deploying")
        self._submit_task(
            self._run_container_func,
            deploy_kubernetes,
            "Deploy",
            "kubernetes",
        )

    def cleanup_kubernetes(self):
        self.log_message("Cleaning Kubernetes resources...")
        self._set_status("Status: Cleaning")
        self._start_progress()
        self._track_started("Cleanup", source="kubernetes", status="cleaning")
        self._submit_task(
            self._run_container_func,
            cleanup_kubernetes,
            "Cleanup",
            "kubernetes",
        )

    def scale_deployment_prompt(self):
        name = simpledialog.askstring("Deployment", "Deployment name:")
        if not name:
            return
        replicas = simpledialog.askinteger("Replicas", "Number of replicas:")
        if replicas is None:
            return
        self.log_message(f"Scaling {name} to {replicas}...")
        self._set_status("Status: Scaling")
        self._start_progress()
        self._track_started(
            "Scale Deployment",
            source="kubernetes",
            status=f"scaling {name}",
        )
        self._submit_task(
            self._run_container_func,
            scale_deployment,
            "Scale Deployment",
            "kubernetes",
            name,
            replicas,
        )

    def get_pod_logs_prompt(self):
        pod = simpledialog.askstring("Pod", "Pod name:")
        if not pod:
            return
        self.log_message(f"Fetching logs for {pod}...")
        self._set_status("Status: Logs")
        self._start_progress()
        self._track_started(
            "Get Pod Logs", source="kubernetes", status=f"logs for {pod}"
        )
        self._submit_task(self._get_logs, pod, "Get Pod Logs", "kubernetes")

    def convert_media_prompt(self):
        if filedialog is None:
            messagebox.showerror("Error", "Tkinter is not available")
            return
        src = filedialog.askopenfilename(title="Select source file")
        if not src:
            return
        dst = filedialog.asksaveasfilename(title="Select output file")
        if not dst:
            return
        bitrate = simpledialog.askstring(
            "Audio Bitrate", "Bitrate", initialvalue="192k"
        )
        codec = simpledialog.askstring("Video Codec", "Codec", initialvalue="libx264")
        self.log_message(f"Converting {src} -> {dst}...")
        self._set_status("Status: Converting")
        self._start_progress()
        self._track_started("Convert Media", source="media", status="converting media")
        self._submit_task(self._convert_media_thread, src, dst, bitrate, codec, "media")

    def _convert_media_thread(self, src, dst, bitrate, codec, source: str):
        try:
            convert_media(src, dst, bitrate=bitrate, codec=codec)
            self.log_message("Operation completed successfully.")
            self._track_finished(source=source, status="media conversion complete")
        except Exception as exc:  # pragma: no cover - ffmpeg errors
            self.log_message(f"Exception: {exc}")
            self._track_finished(source=source, status="media conversion error")
        finally:
            self._stop_progress()
            self._set_status("Status: Ready")

    def _get_logs(self, pod, action_label: str, source: str):
        try:
            logs = get_pod_logs(pod)
            self.log_message(logs)
            self.log_message("Operation completed successfully.")
            self._track_finished(
                source=source, status=f"{action_label.lower()} complete"
            )
        except Exception as exc:  # pragma: no cover - subprocess failures
            self.log_message(f"Exception: {exc}")
            self._track_finished(source=source, status=f"{action_label.lower()} error")
        finally:
            self._stop_progress()
            self._set_status("Status: Ready")

    def _launch_child_gui(self, func, label: str) -> None:
        """Fallback in-process GUI launcher when subprocess startup fails."""

        def launch() -> None:
            try:
                func()
            except Exception as exc:  # pragma: no cover - GUI dependency failures
                self.log_message(f"{label} failed: {exc}")
                if messagebox is not None:
                    messagebox.showerror(label, str(exc))

        self._run_on_ui(launch)

    def launch_simple_chat(self):
        """Open the simple chat demo in a separate process."""

        self.workflow_hint_var.set(
            "The chat demo opens separately so the main control deck stays available."
        )
        self._launch_child_process(
            label="Simple Chat",
            module_name="huey.simple_chat_gui",
            function_name="run_simple_chat",
            source="chat",
            fallback=run_simple_chat,
        )

    def launch_ai_tools(self):
        """Open the AI tools console in a separate process."""

        self.workflow_hint_var.set(
            "The AI console launches separately so you can keep the launcher and the tool open together."
        )
        self._launch_child_process(
            label="AI Console",
            module_name="huey.memory.PY.ai_tools_gui",
            function_name="run_ai_tools",
            source="ai-console",
            fallback=run_ai_tools,
        )

    def launch_dashboard(self):
        """Open the dashboard in a separate process so Tk stays responsive."""

        self.workflow_hint_var.set(
            "The dashboard opens in its own process to keep the control deck responsive."
        )
        self._launch_child_process(
            label="Dashboard",
            module_name="huey.memory.PY.dashboard",
            function_name="launch_dashboard",
            source="dashboard",
            fallback=launch_dashboard,
        )

    def on_close(self):
        """Shutdown the executor and close the UI."""

        if hasattr(self, "executor"):
            self.executor.shutdown(wait=False)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainUI(root)
    root.mainloop()
