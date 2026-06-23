"""Tests for shared Tkinter GUI chrome helpers."""

from __future__ import annotations

from huey.gui.tk import (
    apply_root_chrome,
    apply_ttk_chrome,
    listbox_kwargs,
    primary_button_kwargs,
    text_surface_kwargs,
    tk_palette,
)


class _DummyRoot:
    def __init__(self) -> None:
        self.title_value = ""
        self.minsize_value: tuple[int, int] | None = None
        self.config_calls: list[dict[str, object]] = []

    def title(self, value: str) -> None:
        self.title_value = value

    def minsize(self, width: int, height: int) -> None:
        self.minsize_value = (width, height)

    def configure(self, **kwargs) -> None:
        self.config_calls.append(kwargs)


class _DummyStyle:
    def __init__(self, root) -> None:
        self.root = root
        self.configured: list[tuple[str, dict[str, object]]] = []
        self.mapped: list[tuple[str, dict[str, object]]] = []
        self.theme = ""

    def theme_use(self, name: str) -> None:
        self.theme = name

    def configure(self, name: str, **kwargs) -> None:
        self.configured.append((name, kwargs))

    def map(self, name: str, **kwargs) -> None:
        self.mapped.append((name, kwargs))


class _DummyTtk:
    Style = _DummyStyle


def test_apply_root_chrome_sets_title_minsize_and_palette(monkeypatch) -> None:
    recorded: dict[str, object] = {}

    monkeypatch.setattr(
        "huey.gui.tk.apply_scaling",
        lambda root, mode: recorded.update({"root": root, "mode": mode}),
    )
    root = _DummyRoot()

    apply_root_chrome(root, title="HueyOS", minsize=(640, 480), screen_mode="4k")

    assert recorded["root"] is root
    assert recorded["mode"] == "4k"
    assert root.title_value == "HueyOS"
    assert root.minsize_value == (640, 480)
    assert root.config_calls[-1]["bg"] == tk_palette()["background"]


def test_apply_ttk_chrome_configures_shared_styles() -> None:
    style = apply_ttk_chrome(_DummyRoot(), _DummyTtk)

    assert isinstance(style, _DummyStyle)
    assert style.theme == "clam"
    configured_names = [name for name, _kwargs in style.configured]
    assert "TButton" in configured_names
    assert "TNotebook.Tab" in configured_names
    mapped_names = [name for name, _kwargs in style.mapped]
    assert "TButton" in mapped_names


def test_widget_style_helpers_use_shared_palette() -> None:
    palette = tk_palette()

    assert primary_button_kwargs()["bg"] == palette["accent"]
    assert text_surface_kwargs()["bg"] == palette["panel_alt"]
    assert listbox_kwargs()["selectbackground"] == palette["accent"]
