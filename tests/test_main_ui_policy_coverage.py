"""Cover MainUI branches that can be exercised without a desktop session."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from huey.memory.PY import main_ui
from huey.memory.PY.main_ui import MainUI


class _Variable:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_init_reports_missing_tk(monkeypatch):
    monkeypatch.setattr(main_ui, "tk", None)
    ui = MainUI.__new__(MainUI)
    with pytest.raises(RuntimeError, match="tkinter is not available"):
        MainUI.__init__(ui, None)


def test_bootstrap_state_refreshes_paths_and_emits_events():
    ui = MainUI.__new__(MainUI)
    ui.state = SimpleNamespace(operator=SimpleNamespace())
    ui.repository_var = _Variable("/repo")
    ui._refresh_path_vars = Mock()
    ui._emit_event = Mock()

    MainUI._bootstrap_state(ui)

    assert ui.state.operator.selected_repository == "/repo"
    assert ui.state.operator.active_view == "launch-pad"
    ui._refresh_path_vars.assert_called_once_with()
    assert [call.args[0] for call in ui._emit_event.call_args_list] == [
        main_ui.EventType.REPOSITORY_CHANGED,
        main_ui.EventType.MEMORY_UPDATED,
    ]


def test_background_image_lookup_and_application(monkeypatch, tmp_path: Path):
    ui = MainUI.__new__(MainUI)
    target = Path(main_ui.__file__).resolve().parents[3] / "HueyOS-background.png"
    monkeypatch.setattr(main_ui.Path, "exists", lambda _path: False)
    assert MainUI._find_background_image(ui) is None
    monkeypatch.setattr(main_ui.Path, "exists", lambda path: path == target)
    assert MainUI._find_background_image(ui) == target

    operations = []

    class Label:
        def __init__(self, *_args, **kwargs):
            operations.append(("label", kwargs))

        def place(self, **kwargs):
            operations.append(("place", kwargs))

        def lower(self):
            operations.append(("lower",))

    image = tmp_path / "background.png"
    monkeypatch.setattr(MainUI, "_find_background_image", lambda _self: image)
    monkeypatch.setattr(
        main_ui,
        "tk",
        SimpleNamespace(
            PhotoImage=lambda **kwargs: operations.append(("image", kwargs)) or "photo",
            Label=Label,
            TclError=RuntimeError,
        ),
    )
    ui.root = object()
    MainUI.apply_background_image(ui)
    assert ui.background_image == "photo"
    assert ui.background_label is not None
    assert operations[0] == ("image", {"file": str(image)})
    assert operations[-1] == ("lower",)


def test_background_image_no_tk_no_file_and_load_error(monkeypatch):
    ui = MainUI.__new__(MainUI)
    monkeypatch.setattr(main_ui, "tk", None)
    MainUI.apply_background_image(ui)

    monkeypatch.setattr(
        main_ui, "tk", SimpleNamespace(PhotoImage=Mock(), TclError=RuntimeError)
    )
    monkeypatch.setattr(MainUI, "_find_background_image", lambda _self: None)
    MainUI.apply_background_image(ui)
    main_ui.tk.PhotoImage.assert_not_called()

    monkeypatch.setattr(
        MainUI,
        "_find_background_image",
        lambda _self: Path("missing.png"),
    )
    monkeypatch.setattr(
        main_ui.tk,
        "PhotoImage",
        Mock(side_effect=OSError("bad image")),
    )
    MainUI.apply_background_image(ui)
    main_ui.tk.PhotoImage.assert_called_once()


def test_choose_screen_mode_uses_environment_and_custom_prompts(monkeypatch):
    ui = MainUI.__new__(MainUI)
    monkeypatch.setenv("SCREEN_MODE", "4k")
    assert MainUI.choose_screen_mode(ui) == "4k"

    monkeypatch.delenv("SCREEN_MODE")
    monkeypatch.setattr(main_ui, "simpledialog", None)
    assert MainUI.choose_screen_mode(ui) == "1080p"

    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(
            askstring=lambda *_args, **_kwargs: "CUSTOM",
            askfloat=lambda *_args, **_kwargs: 1.5,
            askinteger=lambda *_args, **_kwargs: 14,
        ),
    )
    assert MainUI.choose_screen_mode(ui) == "custom"
    assert main_ui.os.environ["SCREEN_FACTOR"] == "1.5"
    assert main_ui.os.environ["SCREEN_FONT_SIZE"] == "14"

    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(
            askstring=lambda *_args, **_kwargs: "custom",
            askfloat=lambda *_args, **_kwargs: None,
            askinteger=lambda *_args, **_kwargs: None,
        ),
    )
    assert MainUI.choose_screen_mode(ui) == "custom"


def test_data_summary_emits_memory_count_without_messagebox(monkeypatch):
    ui = MainUI.__new__(MainUI)
    events = []
    ui.log_message = events.append
    ui._emit_event = lambda *args, **kwargs: events.append((args, kwargs))
    monkeypatch.setattr(
        main_ui,
        "preload_all",
        lambda: {"prompts": ["a", "b"], "memory": {"one": [1, 2], "two": [3]}},
    )
    monkeypatch.setattr(main_ui, "messagebox", None)

    MainUI.show_data_summary(ui)

    assert events[0] == "Refreshing data summary..."
    assert events[1][0][0] == main_ui.EventType.MEMORY_UPDATED
    assert events[1][0][1] == {"indexed_documents": 3}
