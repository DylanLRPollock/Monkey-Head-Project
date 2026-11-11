"""Exercise the graphical installer flow without opening a desktop window."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest

from huey.memory.PY import install_gui


class _Value:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _Widget:
    def __init__(self, *, command=None, variable=None, **kwargs):
        self.command = command
        self.variable = variable
        self.kwargs = kwargs
        self.items = []
        self.selection = []
        self.states = []
        self.progress_calls = []

    def pack(self, **_kwargs):
        return self

    def grid(self, **_kwargs):
        return self

    def insert(self, _index, value):
        self.items.append(value)

    def configure(self, **kwargs):
        self.kwargs.update(kwargs)
        if "state" in kwargs:
            self.states.append(kwargs["state"])

    config = configure

    def curselection(self):
        return tuple(self.selection)

    def start(self, interval=None):
        self.progress_calls.append(("start", interval))

    def stop(self):
        self.progress_calls.append(("stop", None))


class _Root:
    def __init__(self, buttons):
        self.buttons = buttons
        self.destroyed = False

    def after(self, _delay, callback):
        callback()

    def mainloop(self):
        self.buttons["Install"].command()

    def destroy(self):
        self.destroyed = True


def _prepare_gui(monkeypatch, *, accepted, selection=(0,)):
    widgets = []
    buttons = {}
    progress = []
    variables = []

    def make_widget(*_args, **kwargs):
        widget = _Widget(**kwargs)
        if kwargs.get("text") == "Install":
            buttons["Install"] = widget
        if kwargs.get("text") == "Cancel":
            buttons["Cancel"] = widget
        if kwargs.get("text") == "Open standalone license review":
            buttons["License"] = widget
        if kwargs.get("text") == "I have read and agree to the license terms.":
            widget.variable.value = accepted
        if "selectmode" in kwargs:
            widget.selection = list(selection)
        widgets.append(widget)
        return widget

    def progress_factory(*_args, **kwargs):
        widget = _Widget(**kwargs)
        progress.append(widget)
        return widget

    root = _Root(buttons)

    class _BooleanVar(_Value):
        pass

    class _StringVar(_Value):
        pass

    tk = SimpleNamespace(
        Tk=lambda: root,
        Frame=make_widget,
        Label=make_widget,
        Button=make_widget,
        Listbox=make_widget,
        Text=make_widget,
        Checkbutton=make_widget,
        BooleanVar=lambda value=False: _BooleanVar(value),
        StringVar=lambda value="": _StringVar(value),
        MULTIPLE="multiple",
        END="end",
        WORD="word",
        DISABLED="disabled",
        NORMAL="normal",
    )
    ttk = SimpleNamespace(
        Combobox=make_widget,
        Progressbar=progress_factory,
    )
    monkeypatch.setattr(install_gui, "tk", tk)
    monkeypatch.setattr(install_gui, "ttk", ttk)
    monkeypatch.setattr(
        install_gui, "apply_root_chrome", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(install_gui, "apply_ttk_chrome", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(install_gui, "listbox_kwargs", lambda: {})
    monkeypatch.setattr(install_gui, "text_surface_kwargs", lambda **_kwargs: {})
    monkeypatch.setattr(install_gui, "primary_button_kwargs", lambda: {})
    monkeypatch.setattr(install_gui, "_read_license_text", lambda: "terms")

    def start_thread(*, target, args, daemon):
        assert daemon is True
        target(*args)
        return SimpleNamespace(start=lambda: None)

    monkeypatch.setattr(install_gui.threading, "Thread", start_thread)
    monkeypatch.setattr(install_gui, "accept_license", lambda _path: None)
    return root, buttons, progress, variables


def test_install_gui_requires_license_and_does_not_run_installer(monkeypatch, tmp_path):
    _root, _buttons, _progress, _variables = _prepare_gui(monkeypatch, accepted=False)
    messages = []
    monkeypatch.setattr(
        install_gui,
        "messagebox",
        SimpleNamespace(showwarning=lambda *args: messages.append(args)),
    )
    installer_calls = []
    monkeypatch.setattr(
        install_gui, "run_installer", lambda **kwargs: installer_calls.append(kwargs)
    )

    install_gui.launch_install_gui(tmp_path / "config.json")

    assert installer_calls == []
    assert messages == [
        (
            "License required",
            "You must agree to the license before installation.",
        )
    ]


@pytest.mark.parametrize(
    ("return_code", "expected_status", "expected_message"),
    [
        (0, "Installation completed successfully.", "info"),
        (3, "Installation failed (code 3).", "error"),
    ],
)
def test_install_gui_runs_selected_packages_and_reports_result(
    monkeypatch, tmp_path, return_code, expected_status, expected_message
):
    _root, buttons, progress, _variables = _prepare_gui(
        monkeypatch, accepted=True, selection=(1,)
    )
    messages = []
    monkeypatch.setattr(
        install_gui,
        "messagebox",
        SimpleNamespace(
            showinfo=lambda *args: messages.append(("info", *args)),
            showerror=lambda *args: messages.append(("error", *args)),
            showwarning=lambda *args: messages.append(("warning", *args)),
        ),
    )
    installer_calls = []

    def run_installer(**kwargs):
        installer_calls.append(kwargs)
        return return_code

    monkeypatch.setattr(install_gui, "run_installer", run_installer)

    install_gui.launch_install_gui(tmp_path / "nested" / "config.json")

    assert installer_calls == [
        {
            "hardware": "general",
            "software": [install_gui.SOFTWARE_OPTIONS[1]],
            "confirmed": True,
            "actor_role": "operator",
        }
    ]
    assert buttons["Install"].states == ["disabled", "normal"]
    assert progress[0].progress_calls == [("start", 10), ("stop", None)]
    if expected_message == "info":
        assert messages[0][0:2] == ("info", "Install")
        assert messages[0][2] == expected_status
    else:
        assert messages == [("error", "Install", expected_status)]


def test_install_gui_handles_command_error(monkeypatch, tmp_path):
    _prepare_gui(monkeypatch, accepted=True)
    messages = []
    monkeypatch.setattr(
        install_gui,
        "messagebox",
        SimpleNamespace(showerror=lambda *args: messages.append(args)),
    )

    def fail_install(**_kwargs):
        raise subprocess.CalledProcessError(12, ["installer"])

    monkeypatch.setattr(install_gui, "run_installer", fail_install)
    install_gui.launch_install_gui(tmp_path / "config.json")
    assert messages == [("Install", "Installation failed (code 12).")]
