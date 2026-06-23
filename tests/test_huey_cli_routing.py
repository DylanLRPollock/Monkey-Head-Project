"""Tests for top-level Huey CLI routing."""

from __future__ import annotations

from huey import cli as huey_cli


def test_main_routes_gui_to_unified_shell(monkeypatch) -> None:
    called: dict[str, list[str] | None] = {}

    def fake_run_gui(argv=None):
        called["gui"] = argv
        return 0

    monkeypatch.setattr(huey_cli, "run_gui", fake_run_gui)
    monkeypatch.setattr(
        huey_cli,
        "run_command_center",
        lambda argv=None: (_ for _ in ()).throw(
            AssertionError("unexpected command-center")
        ),
    )

    assert huey_cli.main(["gui"]) == 0
    assert called["gui"] == []


def test_main_routes_command_center_to_backend(monkeypatch) -> None:
    called: dict[str, list[str] | None] = {}

    def fake_run_command_center(argv=None):
        called["command-center"] = argv
        return 0

    monkeypatch.setattr(
        huey_cli,
        "run_gui",
        lambda argv=None: (_ for _ in ()).throw(AssertionError("unexpected gui")),
    )
    monkeypatch.setattr(huey_cli, "run_command_center", fake_run_command_center)

    assert huey_cli.main(["command-center", "--open"]) == 0
    assert called["command-center"] == ["--open"]
