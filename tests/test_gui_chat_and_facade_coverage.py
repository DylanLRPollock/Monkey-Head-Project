"""Cover simple-chat UI callbacks and module compatibility facades."""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

from huey import simple_chat_gui


class _Widget:
    instances: ClassVar[list[object]] = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.options = kwargs
        self.packed = False
        self.instances.append(self)

    def pack(self, **kwargs):
        self.packed = True
        self.pack_options = kwargs

    def config(self, **kwargs):
        self.options.update(kwargs)


class _Root(_Widget):
    def title(self, value):
        self.window_title = value

    def minsize(self, *size):
        self.minimum_size = size

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def mainloop(self):
        self.loop_started = True


class _Entry(_Widget):
    def get(self):
        return getattr(self, "value", "  What is 2+2?  ")

    def bind(self, sequence, callback):
        self.binding = (sequence, callback)

    def delete(self, start, end):
        self.deleted = (start, end)
        self.value = ""


class _Button(_Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command = kwargs["command"]


class _Chat(_Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inserted = []

    def insert(self, position, text):
        self.inserted.append((position, text))

    def see(self, position):
        self.seen = position


def _fake_tk(*, widgets=True):
    values = {
        "Tk": _Root,
        "Entry": _Entry,
        "Button": _Button,
        "END": "end",
        "NORMAL": "normal",
        "DISABLED": "disabled",
        "WORD": "word",
    }
    if widgets:
        values.update(Frame=_Widget, Label=_Widget)
    return SimpleNamespace(**values)


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        (" What is the capital of France? ", "The capital of France is Paris."),
        ("WHAT IS 2+2?", "2 + 2 equals 4."),
        ("unknown", "Sorry, I don't know the answer to that."),
    ],
)
def test_simple_chat_answer_normalization(question, expected):
    assert simple_chat_gui.get_answer(question) == expected


@pytest.mark.parametrize("with_widgets", [True, False])
def test_simple_chat_window_and_callbacks(monkeypatch, with_widgets):
    _Widget.instances.clear()
    monkeypatch.setattr(simple_chat_gui, "tk", _fake_tk(widgets=with_widgets))
    monkeypatch.setattr(simple_chat_gui.scrolledtext, "ScrolledText", _Chat)
    scale_calls = []
    monkeypatch.setattr(
        simple_chat_gui,
        "apply_scaling",
        lambda root, mode: scale_calls.append((root, mode)),
    )

    simple_chat_gui.run_simple_chat()
    root = next(item for item in _Widget.instances if isinstance(item, _Root))
    entry = next(item for item in _Widget.instances if isinstance(item, _Entry))
    button = next(item for item in _Widget.instances if isinstance(item, _Button))
    chat = next(item for item in _Widget.instances if isinstance(item, _Chat))
    assert root.window_title == "HueyOS Chat Console"
    assert root.loop_started is True
    assert scale_calls == [(root, "1080p")]
    assert chat.options["state"] == "disabled"
    button.command()
    assert ("end", "You: What is 2+2?\n") in chat.inserted
    assert ("end", "HueyOS: 2 + 2 equals 4.\n\n") in chat.inserted
    assert chat.seen == "end"
    assert entry.deleted == (0, "end")
    before = list(chat.inserted)
    button.command()
    assert chat.inserted == before


def test_network_and_power_compatibility_facades_export_implementations():
    # Package directories with these names take precedence during normal import,
    # so load the adjacent legacy shim files directly to exercise their code.
    source_root = Path(__file__).parents[1] / "src" / "huey"

    def load_facade(name):
        spec = importlib.util.spec_from_file_location(
            f"huey.{name}_compat", source_root / f"{name}.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    network = load_facade("network")
    power = load_facade("power")
    network_manager = importlib.import_module("huey.network_compat.manager")
    power_management = importlib.import_module("huey.power_compat.management")

    assert network_manager.NetworkManager is network.NetworkManager
    assert network_manager.NetworkStatus is network.NetworkStatus
    assert power_management.BatteryMonitor is power.BatteryMonitor
    assert power_management.PowerEvent is power.PowerEvent
    with pytest.raises(AttributeError):
        _ = network.not_an_export
    with pytest.raises(AttributeError):
        _ = power.not_an_export
