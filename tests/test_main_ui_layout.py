"""Build the launcher interface with fake Tk widgets and verify its wiring."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from huey.memory.PY import main_ui
from huey.memory.PY.main_ui import MainUI


class _Value:
    def __init__(self, value=""):
        self.value = value
        self.traces = []

    def get(self):
        return self.value

    def set(self, value):
        self.value = value

    def trace_add(self, mode, callback):
        self.traces.append((mode, callback))


class _Widget:
    def __init__(self, *, text="", command=None, textvariable=None, **options):
        self.text = text
        self.command = command
        self.textvariable = textvariable
        self.options = options
        if text:
            self.options.setdefault("text", text)
        self.children = []
        self.items = []
        self.selected = []

    def pack(self, **_kwargs):
        return self

    def grid(self, **_kwargs):
        return self

    def bind(self, *_args):
        return None

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def pack_propagate(self, _value):
        return None

    def delete(self, *_args):
        self.items.clear()

    def insert(self, _index, item):
        self.items.append(item)

    def selection_set(self, index):
        self.selected = [index]

    def focus_set(self):
        self.focused = True

    def selection_range(self, start, end):
        self.range = (start, end)

    def curselection(self):
        return tuple(self.selected)

    def invoke(self):
        if self.command:
            return self.command()


class _Notebook(_Widget):
    def add(self, frame, *, text):
        self.children.append((frame, text))

    def select(self, frame=None):
        if frame is not None:
            self.selected_frame = frame
        return getattr(self, "selected_frame", None)

    def tab(self, _frame, _option):
        for frame, title in self.children:
            if frame is self.selected_frame:
                return title
        return ""


class _Root:
    def __init__(self):
        self.calls = []

    def title(self, value):
        self.calls.append(("title", value))

    def minsize(self, width, height):
        self.calls.append(("minsize", width, height))

    def protocol(self, name, callback):
        self.calls.append(("protocol", name, callback))


class _Menu:
    def __init__(self, *_args, **_kwargs):
        self.commands = []

    def add_command(self, **kwargs):
        self.commands.append(kwargs)

    def add_separator(self):
        self.commands.append({"separator": True})

    def add_cascade(self, **kwargs):
        self.commands.append(kwargs)


def test_launcher_builds_navigation_action_tabs_log_and_footer(monkeypatch):
    widgets = []
    buttons = {}

    def make_widget(*_args, **kwargs):
        widget = _Widget(**kwargs)
        widgets.append(widget)
        if kwargs.get("text") and kwargs.get("command"):
            buttons.setdefault(kwargs["text"], []).append(widget)
        return widget

    notebook = _Notebook()
    ttk = SimpleNamespace(
        Notebook=lambda *_args, **_kwargs: notebook,
        Progressbar=lambda *_args, **kwargs: make_widget(**kwargs),
    )
    tk = SimpleNamespace(
        Frame=make_widget,
        Label=make_widget,
        Button=make_widget,
        Entry=make_widget,
        Listbox=make_widget,
        BOTH="both",
        X="x",
        Y="y",
        LEFT="left",
        RIGHT="right",
        W="w",
        E="e",
        END="end",
        WORD="word",
        FLAT="flat",
        HORIZONTAL="horizontal",
    )
    monkeypatch.setattr(main_ui, "tk", tk)
    monkeypatch.setattr(main_ui, "ttk", ttk)
    monkeypatch.setattr(
        main_ui, "scrolledtext", SimpleNamespace(ScrolledText=make_widget)
    )

    ui = MainUI.__new__(MainUI)
    ui.root = object()
    ui.gui_actions = main_ui.default_gui_actions()
    ui.gui_action_map = main_ui.action_lookup(ui.gui_actions)
    ui.gui_sections = main_ui.default_gui_sections()
    ui.gui_surfaces = main_ui.default_gui_surfaces(ui.gui_actions)
    ui.action_tab_ids, ui.action_tab_titles = MainUI._build_action_tab_index(ui)
    ui.quick_access_var = _Value("run")
    ui.quick_access_matches = list(ui.gui_actions)
    ui.surface_var = _Value("Launch Pad")
    ui.workflow_hint_var = _Value("ready")
    ui.repository_var = _Value("DylanLRPollock/Monkey-Head-Project")
    ui.platform_var = _Value("Test platform")
    ui.memory_var = _Value("/tmp/memory")
    ui.install_path_var = _Value("Unavailable")
    ui.update_path_var = _Value("Unavailable")
    ui.run_path_var = _Value("Unavailable")
    ui.activity_var = _Value("Waiting")
    ui.action_calls = []
    ui._action_handlers = lambda: {
        action.id: (lambda action_id=action.id: ui.action_calls.append(action_id))
        for action in ui.gui_actions
    }
    ui._refresh_overview = lambda: None

    MainUI.create_widgets(ui)

    assert "HueyOS Control Deck" in [widget.text for widget in widgets]
    assert len(notebook.children) == len(ui.surface_tab_frames)
    assert {title for _frame, title in notebook.children} >= {
        "Launch Pad",
        "Runtime Ops",
    }
    assert ui.quick_access_listbox.items
    assert ui.progress is not None
    assert ui.status_label.options["text"] == "Status: Ready"
    assert ui.log_text is not None
    assert ui.quick_access_var.traces[0][0] == "write"

    selected = []
    ui.select_tab = selected.append
    buttons["Windows"][0].invoke()
    assert selected == ["connectors-and-windows"]

    run_action = ui.gui_action_map["run"]
    action_button = next(
        button for button in buttons[run_action.label] if button.command is not None
    )
    action_button.invoke()
    assert ui.action_calls == ["run"]
    assert ui.surface_var.get() == run_action.label
    assert ui.workflow_hint_var.get() == run_action.description


def test_launcher_card_helpers_and_sizing(monkeypatch):
    made = []

    def factory(*_args, **kwargs):
        widget = _Widget(**kwargs)
        made.append(widget)
        return widget

    monkeypatch.setattr(
        main_ui,
        "tk",
        SimpleNamespace(
            Frame=factory, Label=factory, X="x", BOTH="both", LEFT="left", W="w", E="e"
        ),
    )
    card = MainUI._make_card(None, object(), width=300)
    MainUI._add_card_heading(card, "Title", "Description", wraplength=200)
    MainUI._add_flow_step(card, "Step", "Details")
    MainUI._add_key_value(card, "Path", _Value("/tmp"))
    assert card.options["width"] == 300
    assert len(made) >= 8


def test_launcher_initialization_wires_services_and_window(monkeypatch):
    calls = []

    class _StringVar(_Value):
        def __init__(self, *, value=""):
            super().__init__(value)

    monkeypatch.setattr(
        main_ui,
        "tk",
        SimpleNamespace(StringVar=_StringVar),
    )
    monkeypatch.setattr(main_ui, "find_project_root", lambda _path: Path("/project"))
    monkeypatch.setattr(
        main_ui,
        "detect_host_platform",
        lambda: SimpleNamespace(runtime_display_name="Test OS"),
    )
    monkeypatch.setattr(
        main_ui, "apply_scaling", lambda root, mode: calls.append(("scale", mode))
    )
    monkeypatch.setattr(MainUI, "choose_screen_mode", lambda _self: "1080p")
    for name in (
        "apply_dark_theme",
        "setup_paths",
        "_bootstrap_state",
        "create_menu",
        "create_widgets",
        "_bind_navigation_shortcuts",
        "apply_background_image",
        "check_license",
    ):
        monkeypatch.setattr(MainUI, name, lambda self, name=name: calls.append(name))
    monkeypatch.setattr(
        MainUI, "log_message", lambda self, msg: calls.append(("log", msg))
    )

    root = _Root()
    ui = MainUI(root)
    try:
        assert ui.project_root == Path("/project")
        assert ui.platform_var.get() == "Test OS"
        assert ui.repository_var.get() == "DylanLRPollock/Monkey-Head-Project"
        assert all(
            callbacks == [ui._handle_event]
            for callbacks in ui.event_bus._subscribers.values()
        )
        assert ("title", "HueyOS Control Deck") in root.calls
        assert ("minsize", 980, 720) in root.calls
        assert calls[:3] == [("scale", "1080p"), "apply_dark_theme", "setup_paths"]
        assert calls[-1] == ("log", "HueyOS control deck ready.")
    finally:
        ui.executor.shutdown(wait=True)


def test_launcher_menu_and_navigation_callbacks(monkeypatch):
    menus = []

    def menu_factory(*args, **kwargs):
        menu = _Menu(*args, **kwargs)
        menus.append(menu)
        return menu

    monkeypatch.setattr(main_ui, "tk", SimpleNamespace(Menu=menu_factory, END="end"))
    root = SimpleNamespace(quit=lambda: None)
    root.config = lambda **kwargs: setattr(root, "menu", kwargs["menu"])
    ui = MainUI.__new__(MainUI)
    ui.root = root
    MainUI.create_menu(ui)
    assert len(menus) == 4
    assert [entry.get("label") for entry in menus[1].commands if "label" in entry] == [
        "Install",
        "Graphical Installer",
        "Run",
        "Update",
        "Clear Log",
        "Exit",
    ]

    ui.quick_access_var = _Value("run")
    ui.gui_actions = main_ui.default_gui_actions()
    ui.action_tab_titles = {"run": "Launch Pad"}
    ui.quick_access_matches = []
    ui.quick_access_listbox = _Widget()
    ui.quick_access_entry = _Widget()
    ui.refresh_quick_access_results()
    assert ui.quick_access_matches
    assert ui.quick_access_listbox.items
    assert ui.quick_access_listbox.selected == [0]
    assert ui._focus_quick_access() == "break"

    executed = []
    ui._execute_gui_action = executed.append
    ui.quick_access_listbox.selection_set(0)
    assert ui.launch_quick_access_selection() == "break"
    assert executed == [ui.quick_access_matches[0].id]
    ui.quick_access_matches = []
    assert ui.launch_quick_access_selection() == "break"
