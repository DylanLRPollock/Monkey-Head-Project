"""Tests for the legacy ``huey.run`` entry point wrapper."""

from __future__ import annotations

import sys
import types


def test_run_module_invokes_target():
    from huey import run as huey_run

    called: dict[str, bool] = {}
    module = types.ModuleType("_dummy_run_module")

    def main() -> None:
        called["main"] = True

    def alt() -> None:
        called["alt"] = True

    module.main = main  # type: ignore[attr-defined]
    module.alt = alt  # type: ignore[attr-defined]
    sys.modules[module.__name__] = module
    try:
        huey_run.run_module(module.__name__)
        huey_run.run_module(f"{module.__name__}:alt")
    finally:
        sys.modules.pop(module.__name__, None)

    assert called == {"main": True, "alt": True}


def test_main_delegates_to_run_module(monkeypatch):
    from huey import run as huey_run

    invoked: dict[str, str] = {}

    def fake_run_module(target: str) -> None:
        invoked["target"] = target

    monkeypatch.setattr(huey_run, "run_module", fake_run_module)
    monkeypatch.setattr(
        huey_run,
        "minimal_run",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected minimal_run")),
    )
    monkeypatch.setattr(
        huey_run,
        "run_sys_code",
        lambda cmd: (_ for _ in ()).throw(AssertionError("unexpected run_sys_code")),
    )

    huey_run.main(["--module", "pkg.module:func"])

    assert invoked["target"] == "pkg.module:func"


def test_main_install_gui_invokes_launcher(monkeypatch):
    from huey import run as huey_run

    called: dict[str, bool] = {}

    monkeypatch.setattr(huey_run, "launch_install_gui", lambda: called.setdefault("install", True))
    monkeypatch.setattr(
        huey_run,
        "launch_gui",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected launch_gui")),
    )

    huey_run.main(["--install-gui"])

    assert called["install"] is True


def test_main_pyhuey_info_invokes_report(monkeypatch):
    from huey import run as huey_run

    called: dict[str, str] = {}

    monkeypatch.setattr(
        huey_run,
        "print_pyhuey_info",
        lambda source=None: called.setdefault("source", source),
    )
    monkeypatch.setattr(
        huey_run,
        "launch_gui",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unexpected launch_gui")
        ),
    )

    huey_run.main(["--pyhuey-info", "--pyhuey-source", "vendor"])

    assert called["source"] == "vendor"
