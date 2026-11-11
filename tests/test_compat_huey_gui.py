"""Exercise the lightweight GUI compatibility facade without Tk windows."""

from __future__ import annotations

from types import SimpleNamespace

from huey.apps.huey_gui import main_ui


def test_license_display_hash_and_gate(tmp_path, monkeypatch):
    license_path = tmp_path / "LICENSE"
    monkeypatch.setattr(main_ui, "LICENSE_FILE", license_path)
    assert main_ui._license_hash() == "unknown"
    seen = []
    monkeypatch.setattr(
        main_ui, "messagebox", SimpleNamespace(showinfo=lambda *args: seen.append(args))
    )
    main_ui.show_license_gui()
    assert seen[-1] == ("License Agreement", "License details unavailable.")

    license_path.write_text("license text", encoding="utf-8")
    assert len(main_ui._license_hash()) == 64
    main_ui.show_license_gui()
    assert seen[-1] == ("License Agreement", "license text")

    validated = []
    accepted = []
    monkeypatch.setattr(main_ui, "validate_license_acceptance", validated.append)
    monkeypatch.setattr(main_ui, "accept_license", lambda *args: accepted.append(args))
    monkeypatch.setattr(
        main_ui,
        "messagebox",
        SimpleNamespace(
            showinfo=lambda *args: seen.append(args), askyesno=lambda *_args: True
        ),
    )
    monkeypatch.setattr(main_ui, "GUI_CONFIG_PATH", tmp_path / "config.json")
    ui = main_ui.MainUI.__new__(main_ui.MainUI)
    main_ui.MainUI.ensure_license_accepted(ui)
    assert validated == [True]
    assert accepted[-1] == (tmp_path / "config.json", main_ui._license_hash())
    main_ui.MainUI.check_license(ui)
    main_ui.MainUI.show_license(ui)


def test_summary_and_screen_mode_preferences(monkeypatch):
    messages = []
    monkeypatch.setattr(main_ui, "preload_all", lambda: {"prompts": [1, 2]})
    monkeypatch.setattr(
        main_ui,
        "messagebox",
        SimpleNamespace(showinfo=lambda *args: messages.append(args)),
    )
    ui = main_ui.MainUI.__new__(main_ui.MainUI)
    main_ui.MainUI.show_data_summary(ui)
    assert messages[-1] == ("Data Summary", "{'prompts': [1, 2]}")

    monkeypatch.setenv("SCREEN_MODE", "4k")
    assert main_ui.MainUI.choose_screen_mode(ui) == "4k"
    monkeypatch.delenv("SCREEN_MODE")
    calls = []
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(
            askstring=lambda *_args: "custom",
            askfloat=lambda *_args: calls.append("scale") or 1.5,
            askinteger=lambda *_args: calls.append("font") or 13,
        ),
    )
    assert main_ui.MainUI.choose_screen_mode(ui) == "custom"
    assert calls == ["scale", "font"]


def test_compatibility_actions_dispatch_without_starting_threads(monkeypatch):
    launched = []

    class ImmediateThread:
        def __init__(self, *, target, args=(), kwargs=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            launched.append((self.target, self.args, self.kwargs))
            self.target(*self.args, **self.kwargs)

    monkeypatch.setattr(main_ui.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(
        main_ui,
        "convert_media",
        lambda *args, **kwargs: launched.append((args, kwargs)),
    )
    monkeypatch.setattr(main_ui, "run_simple_chat", lambda: launched.append("chat"))
    monkeypatch.setattr(main_ui, "run_ai_tools", lambda: launched.append("ai"))
    monkeypatch.setattr(
        main_ui,
        "filedialog",
        SimpleNamespace(
            askopenfilename=lambda: "input.wav", asksaveasfilename=lambda: "output.wav"
        ),
    )
    monkeypatch.setattr(
        main_ui,
        "simpledialog",
        SimpleNamespace(
            askstring=lambda _title, prompt: {
                "Enter deployment name": "deployment",
                "Enter bitrate": "128k",
                "Enter codec": "aac",
            }[prompt],
            askinteger=lambda *_args: 3,
        ),
    )
    ui = main_ui.MainUI.__new__(main_ui.MainUI)
    ui._run_container_func = lambda *args: launched.append(("container", args))
    main_ui.MainUI.build_image(ui)
    main_ui.MainUI.deploy_kubernetes(ui)
    main_ui.MainUI.scale_deployment_prompt(ui)
    main_ui.MainUI.convert_media_prompt(ui)
    main_ui.MainUI.launch_simple_chat(ui)
    main_ui.MainUI.launch_ai_tools(ui)
    assert any(
        item[1] == ("deployment", 3)
        for item in launched
        if isinstance(item, tuple) and item and item[0] == "container"
    )
    assert (
        ("input.wav", "output.wav"),
        {"bitrate": "128k", "codec": "aac"},
    ) in launched
    assert "chat" in launched and "ai" in launched

    deleted = []
    ui.log_text = SimpleNamespace(delete=lambda *args: deleted.append(args))
    main_ui.MainUI.clear_log(ui)
    assert deleted == [("1.0", main_ui.tk.END)]
