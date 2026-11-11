"""Exercise license dialog decisions with fake widgets and no desktop session."""

from __future__ import annotations

from types import SimpleNamespace

from huey.memory.PY import license_gui


class _Widget:
    def __init__(self, *, command=None, text=None, **kwargs):
        self.command = command
        self.text = text
        self.kwargs = kwargs
        self.inserted = []

    def pack(self, **_kwargs):
        return self

    def insert(self, *args):
        self.inserted.append(args)

    def config(self, **kwargs):
        self.kwargs.update(kwargs)


class _Root:
    def __init__(self, buttons, selected_button):
        self.buttons = buttons
        self.selected_button = selected_button
        self.destroyed = False

    def mainloop(self):
        self.buttons[self.selected_button].command()

    def destroy(self):
        self.destroyed = True


def _prepare_dialog(monkeypatch, selected_button):
    buttons = {}
    roots = []

    def make_widget(*_args, **kwargs):
        widget = _Widget(**kwargs)
        if widget.text in {"Accept", "Decline", "Close"}:
            buttons[widget.text] = widget
        return widget

    def create_root():
        root = _Root(buttons, selected_button)
        roots.append(root)
        return root

    monkeypatch.setattr(
        license_gui,
        "tk",
        SimpleNamespace(
            Tk=create_root,
            Frame=make_widget,
            Label=make_widget,
            Button=make_widget,
            BOTH="both",
            X="x",
            W="w",
            LEFT="left",
            WORD="word",
            END="end",
            DISABLED="disabled",
        ),
    )
    monkeypatch.setattr(
        license_gui,
        "scrolledtext",
        SimpleNamespace(ScrolledText=make_widget),
    )
    monkeypatch.setattr(
        license_gui, "apply_root_chrome", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(license_gui, "text_surface_kwargs", lambda **_kwargs: {})
    monkeypatch.setattr(license_gui, "primary_button_kwargs", lambda: {})
    monkeypatch.setattr(
        license_gui, "_read_license_text", lambda: ("license terms", "hash-1")
    )
    return buttons, roots


def test_license_gui_skips_dialog_when_current_and_not_forced(monkeypatch):
    monkeypatch.setattr(license_gui, "license_is_current", lambda *_args: True)
    assert license_gui.show_license_gui("config.json") is False


def test_license_gui_accepts_terms_and_warns_about_experimental_status(
    monkeypatch, tmp_path
):
    buttons, roots = _prepare_dialog(monkeypatch, "Accept")
    monkeypatch.setattr(license_gui, "license_is_current", lambda *_args: False)
    accepted = []
    monkeypatch.setattr(
        license_gui, "accept_license", lambda *args: accepted.append(args)
    )
    messages = []
    monkeypatch.setattr(
        license_gui,
        "messagebox",
        SimpleNamespace(
            showinfo=lambda *args: messages.append(("info", *args)),
            showwarning=lambda *args: messages.append(("warning", *args)),
        ),
    )

    assert license_gui.show_license_gui(tmp_path / "config.json") is True

    assert buttons["Accept"].command
    assert "Decline" in buttons
    assert accepted == [(tmp_path / "config.json", "hash-1")]
    assert messages == [
        ("info", "License", "License accepted"),
        (
            "warning",
            "Experimental",
            "This is experimental software. Proceed with caution.",
        ),
    ]
    assert roots[0].destroyed


def test_license_gui_declines_and_closes_without_acceptance(monkeypatch, tmp_path):
    buttons, roots = _prepare_dialog(monkeypatch, "Decline")
    monkeypatch.setattr(license_gui, "license_is_current", lambda *_args: False)
    accepted = []
    monkeypatch.setattr(
        license_gui, "accept_license", lambda *args: accepted.append(args)
    )
    warnings = []
    monkeypatch.setattr(
        license_gui,
        "messagebox",
        SimpleNamespace(showwarning=lambda *args: warnings.append(args)),
    )

    assert license_gui.show_license_gui(tmp_path / "config.json") is True

    assert accepted == []
    assert warnings == [("License", "You must accept the license to proceed")]
    assert roots[0].destroyed
    assert "Accept" in buttons


def test_license_gui_force_show_is_read_only_for_current_license(monkeypatch):
    buttons, roots = _prepare_dialog(monkeypatch, "Close")
    monkeypatch.setattr(license_gui, "license_is_current", lambda *_args: True)
    accepted = []
    monkeypatch.setattr(
        license_gui, "accept_license", lambda *args: accepted.append(args)
    )
    monkeypatch.setattr(license_gui, "messagebox", None)

    assert license_gui.show_license_gui("config.json", force_show=True) is True

    assert set(buttons) == {"Close"}
    assert accepted == []
    assert roots[0].destroyed
