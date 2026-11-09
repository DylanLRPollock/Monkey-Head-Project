"""Tests for the legacy ``huey.run`` entry point wrapper."""

from __future__ import annotations

import sys
import types

import pytest


def test_run_module_invokes_target():
    from huey.memory.PY import run as huey_run

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
    from huey.memory.PY import run as huey_run

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
        lambda cmd, **kwargs: (_ for _ in ()).throw(
            AssertionError("unexpected run_sys_code")
        ),
    )

    huey_run.main(["--module", "pkg.module:func"])

    assert invoked["target"] == "pkg.module:func"


def test_main_install_gui_invokes_launcher(monkeypatch):
    from huey.memory.PY import run as huey_run

    called: dict[str, bool] = {}

    monkeypatch.setattr(
        huey_run, "launch_install_gui", lambda: called.setdefault("install", True)
    )
    monkeypatch.setattr(
        huey_run,
        "launch_gui",
        lambda: (_ for _ in ()).throw(AssertionError("unexpected launch_gui")),
    )

    huey_run.main(["--install-gui"])

    assert called["install"] is True


def test_main_pyhuey_info_invokes_report(monkeypatch):
    from huey.memory.PY import run as huey_run

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

    huey_run.main(["--pyhuey-info", "--pyhuey-source", "package"])

    assert called["source"] == "package"


def test_main_list_custom_functions_invokes_report(monkeypatch):
    from huey.memory.PY import run as huey_run

    called: dict[str, str] = {}

    monkeypatch.setattr(
        huey_run,
        "print_custom_functions",
        lambda source=None: called.setdefault("source", source),
    )
    monkeypatch.setattr(
        huey_run,
        "launch_gui",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("unexpected launch_gui")
        ),
    )

    huey_run.main(["--list-custom-functions", "--pyhuey-source", "package"])

    assert called["source"] == "package"


def test_run_custom_function_executes_registered_callable():
    from huey.memory.PY import run as huey_run
    from huey.pyhuey_integration import reset_pygpt_state

    reset_pygpt_state()
    result = huey_run.run_custom_function(
        "format_text",
        '{"text": "alpha beta", "line_length": 20}',
        source="package",
    )

    assert result == "alpha beta"


def test_run_custom_function_requires_json_object():
    from huey.memory.PY import run as huey_run

    with pytest.raises(ValueError):
        huey_run.run_custom_function("format_text", '["not", "an", "object"]')


def test_launch_gui_delegates_to_upstream_launcher(monkeypatch):
    from huey.memory.PY import run as huey_run
    from huey.integrations import pygpt_cli

    captured = []
    monkeypatch.delenv("PYGPT_WORKDIR", raising=False)
    monkeypatch.setattr(
        pygpt_cli, "launch_gui", lambda *, workdir=None: captured.append(workdir) or 0
    )
    huey_run.launch_gui()
    assert captured == [None]


def test_launch_gui_failure_does_not_run_demo(monkeypatch):
    from huey.memory.PY import run as huey_run
    from huey.integrations import pygpt_cli

    monkeypatch.setattr(pygpt_cli, "launch_gui", lambda **kwargs: 2)
    with pytest.raises(RuntimeError, match="status 2"):
        huey_run.launch_gui()


def test_main_does_not_fallback_after_gui_failure(monkeypatch):
    from huey.memory.PY import run as huey_run
    from huey.memory.PY import system_checks

    monkeypatch.setattr(system_checks, "check_os_support", lambda: None)
    monkeypatch.setattr(system_checks, "check_python_version", lambda: None)
    monkeypatch.setattr(
        huey_run,
        "launch_gui",
        lambda source: (_ for _ in ()).throw(RuntimeError("GUI failed")),
    )
    monkeypatch.setattr(
        huey_run, "launch_cli", lambda **kwargs: pytest.fail("unexpected fallback")
    )
    with pytest.raises(RuntimeError, match="GUI failed"):
        huey_run.main([])
