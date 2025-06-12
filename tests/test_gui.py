from unittest.mock import patch
from gui.main_ui import MainUI


def test_check_license_calls_gui():
    ui = MainUI.__new__(MainUI)
    with patch("gui.main_ui.show_license_gui") as gui_call:
        MainUI.check_license(ui)
        gui_call.assert_called_once()


def test_show_license_calls_gui():
    ui = MainUI.__new__(MainUI)
    with patch("gui.main_ui.show_license_gui") as gui_call:
        MainUI.show_license(ui)
        gui_call.assert_called_once()


def test_show_data_summary_displays_info():
    ui = MainUI.__new__(MainUI)
    sample = {"prompts": [1, 2], "memory": {"a": ["x", "y"]}}
    with patch("gui.main_ui.preload_all", return_value=sample), patch(
        "gui.main_ui.messagebox.showinfo"
    ) as info:
        MainUI.show_data_summary(ui)
        info.assert_called_once()


def test_choose_screen_mode_env(monkeypatch):
    ui = MainUI.__new__(MainUI)
    monkeypatch.setenv("SCREEN_MODE", "1080p")
    with patch("gui.main_ui.messagebox.askquestion") as ask:
        mode = MainUI.choose_screen_mode(ui)
        ask.assert_not_called()
        assert mode == "1080p"


def test_choose_screen_mode_prompt():
    ui = MainUI.__new__(MainUI)
    with patch.dict("os.environ", {}, clear=True), patch(
        "gui.main_ui.messagebox.askquestion", return_value="yes"
    ):
        mode = MainUI.choose_screen_mode(ui)
        assert mode == "4k"
