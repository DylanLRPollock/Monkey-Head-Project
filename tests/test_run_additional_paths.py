"""Cover the remaining safe dispatch branches in the legacy run entry point."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

import huey.memory.PY.run as runtime


def test_system_diagnostic_validates_alias_and_reports_command_errors(
    monkeypatch, capsys
):
    monkeypatch.setattr(runtime, "authorize_privileged_operation", lambda *a, **k: True)
    with pytest.raises(ValueError, match="string alias"):
        runtime.run_sys_code(4, confirmed=True, actor_role="admin")
    with pytest.raises(ValueError, match="Unsupported diagnostic"):
        runtime.run_sys_code("uname; id", confirmed=True, actor_role="admin")

    monkeypatch.setattr(
        runtime.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(
            stdout=b"diagnostic output\n", stderr=b"diagnostic warning\n", returncode=0
        ),
    )
    assert runtime.run_sys_code(" WHOAMI ", confirmed=True, actor_role="admin")
    assert capsys.readouterr().out == "diagnostic output\n"

    monkeypatch.setattr(
        runtime.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(stdout=b"", stderr=b"", returncode=7),
    )
    with pytest.raises(RuntimeError, match="exit code 7"):
        runtime.run_sys_code("date", confirmed=True, actor_role="admin")


def test_import_custom_functions_and_pyhuey_report(monkeypatch, capsys):
    calls = []
    module = ModuleType("sample_runtime")
    module.main = lambda: calls.append("main")
    module.run = lambda: calls.append("run")
    monkeypatch.setitem(sys.modules, "sample_runtime", module)
    runtime.run_module("sample_runtime")
    runtime.run_module("sample_runtime:run")
    assert calls == ["main", "run"]
    with pytest.raises(ImportError, match="Function absent"):
        runtime.run_module("sample_runtime:absent")

    functions = [{"name": "format_text", "signature": "(text)", "module": "utils"}]
    monkeypatch.setattr(runtime, "_prepare_pygpt", lambda source=None: True)
    monkeypatch.setattr(runtime, "describe_functions", lambda: functions)
    assert runtime.list_custom_functions("package") == functions
    runtime.print_custom_functions()
    assert "format_text(text) :: utils" in capsys.readouterr().out
    monkeypatch.setattr(runtime, "describe_functions", lambda: [])
    runtime.print_custom_functions()
    assert "No custom functions registered." in capsys.readouterr().out

    monkeypatch.setattr(
        runtime,
        "pyhuey_status",
        lambda **kwargs: {
            "active_source": {"name": "local", "kind": "package", "path": "/pkg"},
            "prepared": True,
            "version": "2.0",
            "module_file": "/pkg/__init__.py",
            "candidates": [{"name": "external", "exists": False, "path": "/missing"}],
            "custom_function_count": 1,
            "custom_functions": functions,
        },
    )
    runtime.print_pyhuey_info()
    report = capsys.readouterr().out
    assert "source: local (package)" in report
    assert "external: no :: /missing" in report


def test_custom_function_json_validation_and_invocation(monkeypatch):
    assert runtime._parse_custom_function_kwargs(None) == {}
    assert runtime._parse_custom_function_kwargs('{"limit": 2}') == {"limit": 2}
    with pytest.raises(ValueError, match="valid JSON"):
        runtime._parse_custom_function_kwargs("{")
    with pytest.raises(ValueError, match="JSON object"):
        runtime._parse_custom_function_kwargs("[1]")
    calls = []
    monkeypatch.setattr(runtime, "_prepare_pygpt", lambda source=None: True)
    monkeypatch.setattr(
        runtime,
        "invoke_function",
        lambda name, **kwargs: calls.append((name, kwargs)) or "done",
    )
    assert runtime.run_custom_function("format_text", '{"text": "hi"}') == "done"
    assert calls == [("format_text", {"text": "hi"})]


@pytest.mark.parametrize(
    ("args", "target", "expected"),
    [
        (["--minimal"], "minimal_run", ((), {})),
        (["--pyhuey-info"], "print_pyhuey_info", (("auto",), {})),
        (["--list-custom-functions"], "print_custom_functions", (("auto",), {})),
        (["--manager-ui"], "launch_manager_ui", ((), {})),
        (["--install-gui"], "launch_install_gui", ((), {})),
        (["--cli"], "launch_cli", ((), {"source": "auto"})),
    ],
)
def test_main_simple_dispatch_branches(monkeypatch, args, target, expected):
    calls = []
    monkeypatch.setattr(runtime, target, lambda *a, **k: calls.append((a, k)))
    monkeypatch.setattr("huey.memory.PY.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr(
        "huey.memory.PY.system_checks.check_python_version", lambda: None
    )
    runtime.main(args)
    assert calls == [expected]


def test_main_list_pdfs_config_workdir_and_version(monkeypatch, capsys, tmp_path):
    pdfs = ModuleType("huey.memory.PY.pdf_utils")
    pdfs.list_available_pdfs = lambda: [Path("one.pdf"), Path("two.pdf")]
    monkeypatch.setitem(sys.modules, pdfs.__name__, pdfs)
    runtime.main(["--list-pdfs"])
    assert capsys.readouterr().out.splitlines() == ["one.pdf", "two.pdf"]

    check_calls = []
    system_checks = ModuleType("huey.memory.PY.system_checks")
    system_checks.system_check = lambda: check_calls.append("check")
    monkeypatch.setitem(sys.modules, system_checks.__name__, system_checks)
    runtime.main(["--system-check"])
    assert check_calls == ["check"]

    workdir = tmp_path / "work"
    config = tmp_path / "main.config"
    runtime_module = ModuleType("runtime_test_main")
    runtime_module.main = lambda: None
    monkeypatch.setitem(sys.modules, runtime_module.__name__, runtime_module)
    monkeypatch.setenv("PYGPT_WORKDIR", "original")
    monkeypatch.setenv("MONKEY_HEAD_CONFIG", "original")
    runtime.main(
        [
            "--workdir",
            str(workdir),
            "--config",
            str(config),
            "--module",
            "runtime_test_main",
        ]
    )
    assert Path(__import__("os").environ["PYGPT_WORKDIR"]) == workdir
    assert Path(__import__("os").environ["MONKEY_HEAD_CONFIG"]) == config

    cli = ModuleType("huey.integrations.pygpt_cli")
    cli.doctor = lambda: {"ready": True}
    monkeypatch.setitem(sys.modules, cli.__name__, cli)
    runtime.main(["--version"])
    assert json.loads(capsys.readouterr().out) == {"ready": True}


def test_launch_gui_passes_workdir_and_reports_exit_status(monkeypatch, tmp_path):
    calls = []
    cli = ModuleType("huey.integrations.pygpt_cli")
    cli.launch_gui = lambda **kwargs: calls.append(kwargs) or 0
    monkeypatch.setitem(sys.modules, cli.__name__, cli)
    monkeypatch.setenv("PYGPT_WORKDIR", str(tmp_path))
    runtime.launch_gui()
    assert calls == [{"workdir": tmp_path}]
    cli.launch_gui = lambda **kwargs: 3
    with pytest.raises(RuntimeError, match="status 3"):
        runtime.launch_gui()


def test_launch_cli_reports_retired_entrypoint():
    with pytest.raises(RuntimeError, match="legacy PyGPT CLI is retired"):
        runtime.launch_cli("--help")


def test_manager_ui_uses_tk_root_and_mainloop(monkeypatch):
    calls = []

    class FakeRoot:
        def mainloop(self):
            calls.append("mainloop")

    tkinter = ModuleType("tkinter")
    tkinter.Tk = lambda: calls.append("Tk") or FakeRoot()
    ui = ModuleType("huey.memory.PY.main_ui")
    ui.MainUI = lambda root: calls.append(("MainUI", root.__class__.__name__))
    monkeypatch.setitem(sys.modules, "tkinter", tkinter)
    monkeypatch.setitem(sys.modules, ui.__name__, ui)

    runtime.launch_manager_ui()
    assert calls == ["Tk", ("MainUI", "FakeRoot"), "mainloop"]


def test_main_simple_chat_and_custom_function_dispatch(monkeypatch, capsys):
    monkeypatch.setattr("huey.memory.PY.system_checks.check_os_support", lambda: None)
    monkeypatch.setattr(
        "huey.memory.PY.system_checks.check_python_version", lambda: None
    )
    calls = []
    chat = ModuleType("huey.memory.PY.legacy.simple_chat")
    chat.main = lambda: calls.append("chat")
    monkeypatch.setitem(sys.modules, chat.__name__, chat)
    runtime.main(["--simple-chat"])
    assert calls == ["chat"]

    monkeypatch.setattr(
        runtime,
        "run_custom_function",
        lambda name, kwargs, source=None: {
            "name": name,
            "args": json.loads(kwargs),
            "source": source,
        },
    )
    runtime.main(
        [
            "--run-custom-function",
            "demo",
            "--custom-function-kwargs",
            '{"n": 2}',
            "--pyhuey-source",
            "package",
        ]
    )
    assert json.loads(capsys.readouterr().out) == {
        "name": "demo",
        "args": {"n": 2},
        "source": "package",
    }
