"""Test isolated legacy utilities with temporary paths and mocked commands."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

from huey.memory.PY import backup_restore, config_toggle_gui, file_manager, resources


def _load_auto_sort():
    path = Path(__file__).resolve().parents[1] / "src/huey/memory/PY/auto-sort.py"
    spec = importlib.util.spec_from_file_location("huey_auto_sort", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _Value:
    def __init__(self, value=False):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _Widget:
    def __init__(self, *, command=None, text=None, variable=None, **kwargs):
        self.command = command
        self.text = text
        self.variable = variable
        self.kwargs = kwargs

    def pack(self, **_kwargs):
        return self


class _Root:
    def __init__(self, buttons, selection):
        self.buttons = buttons
        self.selection = selection
        self.destroyed = False

    def mainloop(self):
        self.buttons[self.selection].command()

    def destroy(self):
        self.destroyed = True


def _prepare_toggle_gui(monkeypatch, selection):
    buttons = {}
    roots = []
    variables = []

    class _Manager:
        def __init__(self, _path):
            self.saved = None

        def get_setting(self, key, default):
            return key.endswith("voice_control") or default

        def update_settings(self, values):
            self.saved = values

    manager = _Manager("config")

    def make_widget(*_args, **kwargs):
        widget = _Widget(**kwargs)
        if widget.text in {"Save", "Cancel"}:
            buttons[widget.text] = widget
        return widget

    def create_root():
        root = _Root(buttons, selection)
        roots.append(root)
        return root

    def make_var(value=False):
        var = _Value(value)
        variables.append(var)
        return var

    monkeypatch.setattr(
        config_toggle_gui,
        "tk",
        SimpleNamespace(
            Tk=create_root,
            Frame=make_widget,
            Label=make_widget,
            Checkbutton=make_widget,
            Button=make_widget,
            BooleanVar=make_var,
            StringVar=lambda value="": _Value(value),
            BOTH="both",
            X="x",
            LEFT="left",
        ),
    )
    monkeypatch.setattr(config_toggle_gui, "ConfigManager", lambda _path: manager)
    monkeypatch.setattr(
        config_toggle_gui, "apply_root_chrome", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(config_toggle_gui, "primary_button_kwargs", lambda: {})
    return manager, buttons, roots, variables


def test_config_toggle_gui_saves_current_values_and_reports_success(monkeypatch):
    manager, buttons, roots, variables = _prepare_toggle_gui(monkeypatch, "Save")
    messages = []
    monkeypatch.setattr(
        config_toggle_gui,
        "messagebox",
        SimpleNamespace(showinfo=lambda *args: messages.append(args)),
    )

    config_toggle_gui.run_config_toggle_gui("config.json")

    assert manager.saved is not None
    assert manager.saved["access.voice_control"] is True
    assert set(manager.saved) == set(config_toggle_gui.TOGGLE_FIELDS)
    assert len(variables) == len(config_toggle_gui.TOGGLE_FIELDS)
    assert messages == [("Config", "Settings saved.")]
    assert roots[0].destroyed
    assert buttons["Save"].command


def test_config_toggle_gui_cancel_does_not_write_settings(monkeypatch):
    manager, _buttons, roots, _variables = _prepare_toggle_gui(monkeypatch, "Cancel")
    monkeypatch.setattr(config_toggle_gui, "messagebox", None)

    config_toggle_gui.run_config_toggle_gui()

    assert manager.saved is None
    assert roots[0].destroyed


def test_config_toggle_gui_reports_missing_tkinter(monkeypatch):
    monkeypatch.setattr(config_toggle_gui, "tk", None)
    with pytest.raises(RuntimeError, match="tkinter is not available"):
        config_toggle_gui.run_config_toggle_gui()


def test_backup_restore_use_expected_paths_and_check_status(monkeypatch, tmp_path):
    home = tmp_path / "home"
    monkeypatch.setattr(
        backup_restore.os.path,
        "expanduser",
        lambda path: str(home / path[2:]),
    )
    commands = []
    monkeypatch.setattr(
        backup_restore.subprocess,
        "run",
        lambda command, **kwargs: (
            commands.append((command, kwargs)) or SimpleNamespace(returncode=0)
        ),
    )
    checks = []
    monkeypatch.setattr(
        backup_restore, "check_error", lambda result, label: checks.append(label)
    )
    made = []
    monkeypatch.setattr(
        backup_restore.os, "makedirs", lambda *args, **kwargs: made.append(args)
    )

    backup_restore.backup_config()
    backup_restore.restore_config()

    source = str(home / "Source/repo/config")
    backup = str(home / "Backup/repo/config")
    assert made == [(backup,)]
    assert commands[0][0] == ["cp", "-r", source, backup]
    assert commands[1][0] == ["cp", "-r", backup, source]
    assert all(kwargs["capture_output"] is True for _, kwargs in commands)
    assert checks == ["Backup Configurations", "Restore Configurations"]


def test_legacy_file_manager_reads_writes_moves_and_handles_errors(
    monkeypatch, tmp_path
):
    manager = file_manager.FileManager()
    source = tmp_path / "input.txt"
    target = tmp_path / "output.txt"
    manager.write_file(str(source), "hello")
    assert manager.read_file(str(source)) == "hello"
    manager.move_file(str(source), str(target))
    assert target.read_text(encoding="utf-8") == "hello"

    handled = []
    monkeypatch.setattr(
        file_manager.ErrorHandler,
        "handle_exception",
        lambda _self, exc: handled.append(exc),
    )
    assert manager.read_file(str(tmp_path / "missing")) is None
    assert len(handled) == 1


def test_resource_file_generation_filters_sorts_and_supports_wildcard(tmp_path, capsys):
    source = tmp_path / "assets"
    source.mkdir()
    (source / "b.svg").write_text("b", encoding="utf-8")
    (source / "a.svg").write_text("a", encoding="utf-8")
    (source / "skip.txt").write_text("skip", encoding="utf-8")
    output = tmp_path / "icons.qrc"

    resources.generate_resource_file([source], output, ".svg", "/icons")

    result = output.read_text(encoding="utf-8")
    assert result.index('alias="a.svg"') < result.index('alias="b.svg"')
    assert "skip.txt" not in result
    assert capsys.readouterr().out == f"Generated: {output}\n"

    wildcard = tmp_path / "all.qrc"
    resources.generate_resource_file([source], wildcard, "*", "/all")
    assert "skip.txt" in wildcard.read_text(encoding="utf-8")


def test_auto_sort_moves_known_unknown_empty_and_duplicate_extensions(tmp_path):
    sorter = _load_auto_sort()
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "photo.jpg").write_text("one", encoding="utf-8")
    (raw / "photo2.jpg").write_text("two", encoding="utf-8")
    (raw / "notes.txt").write_text("text", encoding="utf-8")
    (raw / "README").write_text("misc", encoding="utf-8")
    (raw / "unknown.data").write_text("data", encoding="utf-8")
    (raw / "directory").mkdir()
    memory = tmp_path / "memory"
    (memory / "JPEG").mkdir(parents=True)
    (memory / "JPEG" / "photo.jpg").write_text("existing", encoding="utf-8")

    sorter.sort_raw_files(tmp_path)

    assert (memory / "JPEG" / "photo_1.jpg").read_text(encoding="utf-8") == "one"
    assert (memory / "JPEG" / "photo2.jpg").read_text(encoding="utf-8") == "two"
    assert (memory / "TXT" / "notes.txt").is_file()
    assert (memory / "MISC" / "README").is_file()
    assert (memory / "DATA" / "unknown.data").is_file()
    assert (raw / "directory").is_dir()
    assert list(raw.iterdir()) == [raw / "directory"]
