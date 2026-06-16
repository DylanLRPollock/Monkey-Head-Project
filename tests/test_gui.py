# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Gui module (tests)

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

GUI_MAIN_UI_MODULE = (
    Path(__file__).resolve().parents[1] / "apps" / "huey_gui" / "main_ui.py"
)

if not GUI_MAIN_UI_MODULE.exists():
    pytest.skip(
        "GUI module not available in this repository layout", allow_module_level=True
    )

spec = importlib.util.spec_from_file_location("gui.main_ui", GUI_MAIN_UI_MODULE)
main_ui = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(main_ui)
MainUI = main_ui.MainUI


def test_check_license_calls_gui():
    ui = MainUI.__new__(MainUI)
    with patch.object(main_ui, "show_license_gui") as gui_call:
        MainUI.check_license(ui)
        gui_call.assert_called_once()


def test_show_license_calls_gui():
    ui = MainUI.__new__(MainUI)
    with patch.object(main_ui, "show_license_gui") as gui_call:
        MainUI.show_license(ui)
        gui_call.assert_called_once()


def test_show_license_gui_reads_license_file(tmp_path):
    license_file = tmp_path / "LICENSE"
    license_file.write_text("test license body", encoding="utf-8")

    with (
        patch.object(main_ui, "LICENSE_FILE", license_file),
        patch.object(main_ui.messagebox, "showinfo") as info,
    ):
        main_ui.show_license_gui()

    info.assert_called_once_with("License Agreement", "test license body")


def test_show_license_gui_falls_back_when_license_missing(tmp_path):
    with (
        patch.object(main_ui, "LICENSE_FILE", tmp_path / "missing-LICENSE"),
        patch.object(main_ui.messagebox, "showinfo") as info,
    ):
        main_ui.show_license_gui()

    info.assert_called_once_with("License Agreement", "License details unavailable.")


def test_main_ui_accepts_license_on_init():
    with (
        patch.object(main_ui.messagebox, "askyesno", return_value=True) as ask,
        patch.object(main_ui, "validate_license_acceptance") as validate,
        patch.object(main_ui, "_license_hash", return_value="hash-123"),
        patch.object(main_ui, "accept_license") as accept,
    ):
        ui = MainUI()

    assert isinstance(ui, MainUI)
    ask.assert_called_once()
    validate.assert_called_once_with(True)
    accept.assert_called_once_with(main_ui.GUI_CONFIG_PATH, "hash-123")


def test_main_ui_declines_license_before_writing_config():
    with (
        patch.object(main_ui.messagebox, "askyesno", return_value=False),
        patch.object(main_ui, "accept_license") as accept,
    ):
        with pytest.raises(PermissionError):
            MainUI()

    accept.assert_not_called()


def test_show_data_summary_displays_info():
    ui = MainUI.__new__(MainUI)
    sample = {"prompts": [1, 2], "memory": {"a": ["x", "y"]}}
    with (
        patch.object(main_ui, "preload_all", return_value=sample),
        patch.object(main_ui.messagebox, "showinfo") as info,
    ):
        MainUI.show_data_summary(ui)
        info.assert_called_once()


def test_choose_screen_mode_env(monkeypatch):
    ui = MainUI.__new__(MainUI)
    monkeypatch.setenv("SCREEN_MODE", "1080p")
    with patch.object(main_ui.simpledialog, "askstring") as ask:
        mode = MainUI.choose_screen_mode(ui)
        ask.assert_not_called()
        assert mode == "1080p"


def test_choose_screen_mode_env_custom(monkeypatch):
    ui = MainUI.__new__(MainUI)
    monkeypatch.setenv("SCREEN_MODE", "custom")
    with patch.object(main_ui.simpledialog, "askstring") as ask:
        mode = MainUI.choose_screen_mode(ui)
        ask.assert_not_called()
        assert mode == "custom"


def test_choose_screen_mode_prompt():
    ui = MainUI.__new__(MainUI)
    with (
        patch.dict("os.environ", {}, clear=True),
        patch.object(main_ui.simpledialog, "askstring", return_value="4k"),
    ):
        mode = MainUI.choose_screen_mode(ui)
        assert mode == "4k"


def test_choose_screen_mode_prompt_custom(monkeypatch):
    ui = MainUI.__new__(MainUI)
    with (
        patch.dict("os.environ", {}, clear=True),
        patch.object(main_ui.simpledialog, "askstring", return_value="custom"),
        patch.object(main_ui.simpledialog, "askfloat", return_value=1.5) as askf,
        patch.object(main_ui.simpledialog, "askinteger", return_value=12) as aski,
    ):
        mode = MainUI.choose_screen_mode(ui)
        assert mode == "custom"
        askf.assert_called_once()
        aski.assert_called_once()


def test_build_image_calls_runner():
    ui = MainUI.__new__(MainUI)
    ui.status_label = SimpleNamespace(config=lambda **_: None)
    ui.progress = SimpleNamespace(start=lambda: None, stop=lambda: None)
    with (
        patch.object(MainUI, "_run_container_func") as runner,
        patch.object(MainUI, "log_message"),
        patch.object(main_ui.threading, "Thread") as th,
    ):
        th.side_effect = lambda target, args: SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.build_image(ui)
        runner.assert_called_once()


def test_deploy_kubernetes_calls_runner():
    ui = MainUI.__new__(MainUI)
    ui.status_label = SimpleNamespace(config=lambda **_: None)
    ui.progress = SimpleNamespace(start=lambda: None, stop=lambda: None)
    with (
        patch.object(MainUI, "_run_container_func") as runner,
        patch.object(MainUI, "log_message"),
        patch.object(main_ui.threading, "Thread") as th,
    ):
        th.side_effect = lambda target, args: SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.deploy_kubernetes(ui)
        runner.assert_called_once()


def test_scale_deployment_prompt_collects_input():
    ui = MainUI.__new__(MainUI)
    ui.status_label = SimpleNamespace(config=lambda **_: None)
    ui.progress = SimpleNamespace(start=lambda: None, stop=lambda: None)
    with (
        patch.object(main_ui.simpledialog, "askstring", return_value="demo"),
        patch.object(main_ui.simpledialog, "askinteger", return_value=2),
        patch.object(MainUI, "_run_container_func") as runner,
        patch.object(MainUI, "log_message"),
        patch.object(main_ui.threading, "Thread") as th,
    ):
        th.side_effect = lambda target, args: SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.scale_deployment_prompt(ui)
        runner.assert_called_once()


def test_convert_media_prompt_runs_thread():
    ui = MainUI.__new__(MainUI)
    ui.status_label = SimpleNamespace(config=lambda **_: None)
    ui.progress = SimpleNamespace(start=lambda: None, stop=lambda: None)
    with (
        patch.object(main_ui.filedialog, "askopenfilename", return_value="in.wav"),
        patch.object(
            main_ui.filedialog,
            "asksaveasfilename",
            return_value="out.mp3",
        ),
        patch.object(
            main_ui.simpledialog,
            "askstring",
            side_effect=["128k", "libx264"],
        ),
        patch.object(main_ui, "convert_media") as conv,
        patch.object(main_ui.threading, "Thread") as th,
        patch.object(MainUI, "log_message"),
    ):
        th.side_effect = lambda target, args: SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.convert_media_prompt(ui)
        conv.assert_called_once_with(
            "in.wav", "out.mp3", bitrate="128k", codec="libx264"
        )


def test_launch_simple_chat_runs_thread():
    ui = MainUI.__new__(MainUI)
    with (
        patch.object(main_ui, "run_simple_chat") as run_chat,
        patch.object(main_ui.threading, "Thread") as th,
        patch.object(MainUI, "log_message"),
    ):
        th.side_effect = lambda target=None, args=(): SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.launch_simple_chat(ui)
        run_chat.assert_called_once()


def test_launch_ai_tools_runs_thread():
    ui = MainUI.__new__(MainUI)
    with (
        patch.object(main_ui, "run_ai_tools") as run_tools,
        patch.object(main_ui.threading, "Thread") as th,
        patch.object(MainUI, "log_message"),
    ):
        th.side_effect = lambda target=None, args=(): SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.launch_ai_tools(ui)
        run_tools.assert_called_once()


def test_clear_log_invokes_delete():
    ui = MainUI.__new__(MainUI)
    dummy_log = SimpleNamespace(delete=lambda *a, **k: None)
    ui.log_text = dummy_log
    with patch.object(main_ui, "tk", SimpleNamespace(END="end")):
        with patch.object(dummy_log, "delete") as delete:
            MainUI.clear_log(ui)
            delete.assert_called_once_with("1.0", "end")
