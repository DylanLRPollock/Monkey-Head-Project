"""Test launcher setup, theming, and background paths with fake Tk objects."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from huey.memory.PY import main_ui
from huey.memory.PY.main_ui import MainUI


class _Var:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _Style:
    def __init__(self, *, fail_theme=False):
        self.fail_theme = fail_theme
        self.calls = []

    def theme_use(self, theme):
        self.calls.append(("theme", theme))
        if self.fail_theme:
            raise RuntimeError("theme not installed")

    def configure(self, *args, **kwargs):
        self.calls.append(("configure", args, kwargs))

    def map(self, *args, **kwargs):
        self.calls.append(("map", args, kwargs))


def _theme_tk():
    return SimpleNamespace(RAISED="raised", TclError=RuntimeError)


def test_apply_dark_theme_configures_widgets_and_recovers_from_theme_error(
    monkeypatch,
):
    style = _Style(fail_theme=True)
    root_calls = []
    monkeypatch.setattr(main_ui, "tk", _theme_tk())
    monkeypatch.setattr(
        main_ui,
        "ttk",
        SimpleNamespace(Style=lambda _root: style),
    )
    ui = MainUI.__new__(MainUI)
    ui.root = SimpleNamespace(configure=lambda **kwargs: root_calls.append(kwargs))

    MainUI.apply_dark_theme(ui)

    assert root_calls[0]["highlightthickness"] == 1
    assert ("theme", "clam") in style.calls
    assert len([call for call in style.calls if call[0] == "configure"]) == 6
    assert len([call for call in style.calls if call[0] == "map"]) == 2


def test_apply_background_image_handles_missing_and_successful_images(monkeypatch):
    ui = MainUI.__new__(MainUI)
    ui.root = object()
    ui.background_image = None
    ui._find_background_image = lambda: None
    monkeypatch.setattr(main_ui, "tk", SimpleNamespace())

    MainUI.apply_background_image(ui)

    assert ui.background_image is None

    image_path = Path("/tmp/hueyos-background.png")
    calls = []

    class _Label:
        def place(self, **kwargs):
            calls.append(("place", kwargs))

        def lower(self):
            calls.append(("lower",))

    ui._find_background_image = lambda: image_path
    monkeypatch.setattr(
        main_ui,
        "tk",
        SimpleNamespace(
            PhotoImage=lambda **kwargs: ("image", kwargs["file"]),
            Label=lambda *_args, **kwargs: _Label(),
        ),
    )

    MainUI.apply_background_image(ui)

    assert ui.background_image == ("image", str(image_path))
    assert calls == [
        ("place", {"relx": 0, "rely": 0, "relwidth": 1, "relheight": 1}),
        ("lower",),
    ]


def test_apply_background_image_catches_unreadable_image(monkeypatch):
    ui = MainUI.__new__(MainUI)
    ui.root = object()
    ui._find_background_image = lambda: Path("/tmp/broken.png")
    ui.background_image = None
    monkeypatch.setattr(
        main_ui,
        "tk",
        SimpleNamespace(
            PhotoImage=lambda **_kwargs: (_ for _ in ()).throw(OSError("bad image"))
        ),
    )

    MainUI.apply_background_image(ui)

    assert ui.background_image is None


def test_choose_screen_mode_custom_without_optional_values(monkeypatch):
    monkeypatch.delenv("SCREEN_MODE", raising=False)
    monkeypatch.delenv("SCREEN_FACTOR", raising=False)
    monkeypatch.delenv("SCREEN_FONT_SIZE", raising=False)
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(
            askstring=lambda *_args, **_kwargs: "CUSTOM",
            askfloat=lambda *_args, **_kwargs: None,
            askinteger=lambda *_args, **_kwargs: None,
        ),
    )
    assert MainUI.choose_screen_mode(MainUI.__new__(MainUI)) == "custom"
    assert "SCREEN_FACTOR" not in main_ui.os.environ
    assert "SCREEN_FONT_SIZE" not in main_ui.os.environ


def test_choose_screen_mode_falls_back_for_invalid_prompt_and_missing_dialog(
    monkeypatch,
):
    monkeypatch.delenv("SCREEN_MODE", raising=False)
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(askstring=lambda *_args, **_kwargs: "tv"),
    )
    assert MainUI.choose_screen_mode(MainUI.__new__(MainUI)) == "1080p"
    monkeypatch.setattr(main_ui, "simpledialog", None)
    assert MainUI.choose_screen_mode(MainUI.__new__(MainUI)) == "1080p"


def test_setup_paths_refreshes_display_variables(monkeypatch, tmp_path):
    paths = SimpleNamespace(
        install=tmp_path / "install.py",
        update=None,
        run=tmp_path / "run.py",
    )
    monkeypatch.setattr(main_ui, "resolve_platform_script_paths", lambda root: paths)
    ui = MainUI.__new__(MainUI)
    ui.project_root = tmp_path
    ui.install_path_var = _Var()
    ui.update_path_var = _Var()
    ui.run_path_var = _Var()

    MainUI.setup_paths(ui)

    assert ui.install_path == paths.install
    assert ui.update_path == paths.update
    assert ui.run_path == paths.run
    assert ui.install_path_var.get() == str(paths.install)
    assert ui.update_path_var.get() == "Unavailable on this platform"
    assert ui.run_path_var.get() == str(paths.run)
