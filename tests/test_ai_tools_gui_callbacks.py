"""Drive the AI console's Tk callbacks with in-memory widget doubles."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

from huey.memory.PY import ai_tools_gui


class _Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _Widget:
    def __init__(self, *, text="", command=None, textvariable=None, **kwargs):
        self.text = text
        self.command = command
        self.textvariable = textvariable
        self.kwargs = kwargs
        self.value = ""
        self.items = []
        self.states = []

    def pack(self, **_kwargs):
        return self

    def grid(self, **_kwargs):
        return self

    def bind(self, event, callback):
        self.binding = (event, callback)

    def grid_rowconfigure(self, *_args, **_kwargs):
        return None

    def grid_columnconfigure(self, *_args, **_kwargs):
        return None

    def configure(self, **kwargs):
        self.states.append(kwargs)
        self.kwargs.update(kwargs)

    def get(self):
        return self.textvariable.get() if self.textvariable else self.value

    def insert(self, _index, value):
        self.items.append(value)

    def delete(self, *_args):
        self.items.clear()

    def see(self, *_args):
        return None

    def invoke(self):
        if self.command:
            return self.command()


# McCabe counts the nested widget doubles as branches of this integration test.
def test_ai_tools_console_processing_memory_upload_and_chat(  # noqa: C901, RUF100
    monkeypatch, tmp_path
):
    events = []
    buttons = {}
    entries = []
    variables = []
    lists = []
    text_widgets = []
    copies = {"fail": True}

    def widget_factory(*_args, **kwargs):
        widget = _Widget(**kwargs)
        if "text" in kwargs and kwargs.get("command"):
            buttons.setdefault(kwargs["text"], []).append(widget)
        return widget

    def entry_factory(*_args, **kwargs):
        widget = widget_factory(*_args, **kwargs)
        entries.append(widget)
        return widget

    def list_factory(*_args, **kwargs):
        widget = widget_factory(*_args, **kwargs)
        lists.append(widget)
        return widget

    def text_factory(*_args, **kwargs):
        widget = widget_factory(*_args, **kwargs)
        text_widgets.append(widget)
        return widget

    class _Root:
        def __init__(self):
            self.tk = SimpleNamespace(call=lambda *_args: None)

        def after(self, _delay, callback):
            callback()

        def mainloop(self):
            entries[0].value = "sample input"
            buttons["Process"][0].invoke()
            entries[1].value = "bad, number"
            buttons["Compute Mean"][0].invoke()
            entries[1].value = "1, 2, 3"
            buttons["Compute Mean"][0].invoke()

            for button in buttons["Refresh"]:
                button.invoke()

            buttons["Upload Files"][0].invoke()
            copies["fail"] = False
            buttons["Upload Files"][0].invoke()
            buttons["Open Memory Path"][0].invoke()

            variables[-1].set("hello Huey")
            buttons["Send"][0].invoke()
            variables[-1].set("provider error")
            buttons["Send"][0].invoke()
            events.append(("chat-output", list(text_widgets[0].items)))
            buttons["Clear"][0].invoke()

    tk = SimpleNamespace(
        Tk=_Root,
        Frame=widget_factory,
        Label=widget_factory,
        Entry=entry_factory,
        Button=widget_factory,
        Listbox=list_factory,
        StringVar=lambda value="": variables.append(_Var(value)) or variables[-1],
        BOTH="both",
        X="x",
        W="w",
        E="e",
        LEFT="left",
        END="end",
        NORMAL="normal",
        DISABLED="disabled",
    )

    class _Notebook(_Widget):
        def add(self, *_args, **kwargs):
            self.items.append(kwargs)

        def select(self, frame):
            self.selected = frame

    class _Progressbar(_Widget):
        def configure(self, **kwargs):
            if kwargs.get("value") == -1:
                raise ValueError("invalid progress")
            super().configure(**kwargs)

    ttk = SimpleNamespace(
        Notebook=lambda *_args, **kwargs: _Notebook(**kwargs),
        Progressbar=lambda *_args, **kwargs: _Progressbar(**kwargs),
        Button=widget_factory,
        Combobox=widget_factory,
    )
    messages = []
    monkeypatch.setattr(ai_tools_gui, "tk", tk)
    monkeypatch.setattr(ai_tools_gui, "ttk", ttk)
    monkeypatch.setattr(
        ai_tools_gui, "scrolledtext", SimpleNamespace(ScrolledText=text_factory)
    )
    monkeypatch.setattr(
        ai_tools_gui,
        "messagebox",
        SimpleNamespace(
            showinfo=lambda *args: messages.append(("info", args)),
            showerror=lambda *args: messages.append(("error", args)),
        ),
    )
    monkeypatch.setattr(
        ai_tools_gui,
        "filedialog",
        SimpleNamespace(
            askopenfilenames=lambda **_kwargs: (
                str(tmp_path / "good.txt"),
                str(tmp_path / "missing.txt"),
            )
        ),
    )
    monkeypatch.setattr(
        ai_tools_gui, "apply_root_chrome", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(ai_tools_gui, "apply_ttk_chrome", lambda *_args: None)
    monkeypatch.setattr(ai_tools_gui, "primary_button_kwargs", lambda: {})
    monkeypatch.setattr(ai_tools_gui, "listbox_kwargs", lambda: {})
    monkeypatch.setattr(ai_tools_gui, "text_surface_kwargs", lambda **_kwargs: {})
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    monkeypatch.setattr(ai_tools_gui, "ensure_subdirectory", lambda *_args: uploads)
    monkeypatch.setattr(
        ai_tools_gui, "get_memory_path", lambda **_kwargs: tmp_path / "memory"
    )
    good = tmp_path / "good.txt"
    good.write_text("uploaded", encoding="utf-8")

    class _Processor:
        def process_data(self, text):
            return text.upper()

        def compute_mean(self, numbers):
            return sum(numbers) / len(numbers)

    processor_module = types.ModuleType("huey.memory.PY.ai_processor")
    processor_module.AIProcessor = _Processor
    monkeypatch.setitem(sys.modules, processor_module.__name__, processor_module)

    class _Config:
        def get_setting(self, key, default=None):
            if key == "agent.llama.provider":
                return "invalid-provider"
            if key == "agent.llama.model":
                return ""
            return ["wrong", "type"]

    monkeypatch.setattr(ai_tools_gui, "ConfigManager", lambda _path: _Config())

    class _Adapter:
        def __init__(self, provider, *, model, settings):
            events.append(("adapter", provider.value, model, settings))

        def generate(self, *, prompt, messages):
            if prompt == "provider error":
                raise RuntimeError("offline")
            return f"answer to {messages[-1]['content']}"

    monkeypatch.setattr(ai_tools_gui, "LLMAdapter", _Adapter)

    class _Thread:
        def __init__(self, *, target, daemon=False):
            self.target = target
            self.daemon = daemon

        def start(self):
            events.append(("thread", self.daemon))
            self.target()

    monkeypatch.setattr(ai_tools_gui.threading, "Thread", _Thread)
    monkeypatch.setattr(
        ai_tools_gui.shutil,
        "copy2",
        lambda source, destination: (
            (_ for _ in ()).throw(OSError("disk full"))
            if copies["fail"]
            else Path(destination).write_bytes(Path(source).read_bytes())
        ),
    )
    monkeypatch.setattr(
        ai_tools_gui,
        "_gather_system_status",
        lambda: {"hostname": "huey", "memory_percent": "bad"},
    )

    ai_tools_gui.run_ai_tools()

    assert (uploads / "good.txt").read_text(encoding="utf-8") == "uploaded"
    assert any("Upload failed" in item[1][0] for item in messages if item[0] == "error")
    assert any(item[1][0] == "Processed" for item in messages if item[0] == "info")
    assert any(item[0] == "adapter" and item[1] == "openai" for item in events)
    assert any(
        "offline" in item
        for event in events
        if len(event) == 2 and event[0] == "chat-output"
        for item in event[1]
    )
    assert any(
        "answer to hello Huey" in item
        for event in events
        if len(event) == 2 and event[0] == "chat-output"
        for item in event[1]
    )
    assert any("good.txt" in item for listing in lists for item in listing.items)
