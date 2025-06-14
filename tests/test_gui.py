from unittest.mock import patch
from types import SimpleNamespace
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
    with patch("gui.main_ui.simpledialog.askstring") as ask:
        mode = MainUI.choose_screen_mode(ui)
        ask.assert_not_called()
        assert mode == "1080p"


def test_choose_screen_mode_env_custom(monkeypatch):
    ui = MainUI.__new__(MainUI)
    monkeypatch.setenv("SCREEN_MODE", "custom")
    with patch("gui.main_ui.simpledialog.askstring") as ask:
        mode = MainUI.choose_screen_mode(ui)
        ask.assert_not_called()
        assert mode == "custom"


def test_choose_screen_mode_prompt():
    ui = MainUI.__new__(MainUI)
    with patch.dict("os.environ", {}, clear=True), patch(
        "gui.main_ui.simpledialog.askstring", return_value="4k"
    ):
        mode = MainUI.choose_screen_mode(ui)
        assert mode == "4k"


def test_choose_screen_mode_prompt_custom(monkeypatch):
    ui = MainUI.__new__(MainUI)
    with patch.dict("os.environ", {}, clear=True), patch(
        "gui.main_ui.simpledialog.askstring", return_value="custom"
    ), patch("gui.main_ui.simpledialog.askfloat", return_value=1.5) as askf, patch(
        "gui.main_ui.simpledialog.askinteger", return_value=12
    ) as aski:
        mode = MainUI.choose_screen_mode(ui)
        assert mode == "custom"
        askf.assert_called_once()
        aski.assert_called_once()


def test_build_image_calls_runner():
    ui = MainUI.__new__(MainUI)
    ui.status_label = SimpleNamespace(config=lambda **_: None)
    ui.progress = SimpleNamespace(start=lambda: None, stop=lambda: None)
    with patch.object(MainUI, "_run_container_func") as runner, patch.object(
        MainUI, "log_message"
    ), patch("gui.main_ui.threading.Thread") as th:
        th.side_effect = lambda target, args: SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.build_image(ui)
        runner.assert_called_once()


def test_deploy_kubernetes_calls_runner():
    ui = MainUI.__new__(MainUI)
    ui.status_label = SimpleNamespace(config=lambda **_: None)
    ui.progress = SimpleNamespace(start=lambda: None, stop=lambda: None)
    with patch.object(MainUI, "_run_container_func") as runner, patch.object(
        MainUI, "log_message"
    ), patch("gui.main_ui.threading.Thread") as th:
        th.side_effect = lambda target, args: SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.deploy_kubernetes(ui)
        runner.assert_called_once()


def test_scale_deployment_prompt_collects_input():
    ui = MainUI.__new__(MainUI)
    ui.status_label = SimpleNamespace(config=lambda **_: None)
    ui.progress = SimpleNamespace(start=lambda: None, stop=lambda: None)
    with patch("gui.main_ui.simpledialog.askstring", return_value="demo"), patch(
        "gui.main_ui.simpledialog.askinteger", return_value=2
    ), patch.object(MainUI, "_run_container_func") as runner, patch.object(
        MainUI, "log_message"
    ), patch(
        "gui.main_ui.threading.Thread"
    ) as th:
        th.side_effect = lambda target, args: SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.scale_deployment_prompt(ui)
        runner.assert_called_once()


def test_convert_media_prompt_runs_thread():
    ui = MainUI.__new__(MainUI)
    ui.status_label = SimpleNamespace(config=lambda **_: None)
    ui.progress = SimpleNamespace(start=lambda: None, stop=lambda: None)
    with patch("gui.main_ui.filedialog.askopenfilename", return_value="in.wav"), patch(
        "gui.main_ui.filedialog.asksaveasfilename",
        return_value="out.mp3",
    ), patch(
        "gui.main_ui.simpledialog.askstring",
        side_effect=["128k", "libx264"],
    ), patch(
        "gui.main_ui.convert_media"
    ) as conv, patch(
        "gui.main_ui.threading.Thread"
    ) as th, patch.object(
        MainUI, "log_message"
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
    with patch("gui.main_ui.run_simple_chat") as run_chat, patch(
        "gui.main_ui.threading.Thread"
    ) as th, patch.object(MainUI, "log_message"):
        th.side_effect = lambda target=None, args=(): SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.launch_simple_chat(ui)
        run_chat.assert_called_once()


def test_launch_ai_tools_runs_thread():
    ui = MainUI.__new__(MainUI)
    with patch("gui.main_ui.run_ai_tools") as run_tools, patch(
        "gui.main_ui.threading.Thread"
    ) as th, patch.object(MainUI, "log_message"):
        th.side_effect = lambda target=None, args=(): SimpleNamespace(
            start=lambda: target(*args)
        )
        MainUI.launch_ai_tools(ui)
        run_tools.assert_called_once()
