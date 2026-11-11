"""Exercise manager authorization, path guards, reporting, and menu callbacks."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock


def _manager_types():
    import huey.connectors.pyhuey.tools.manager as module
    from huey.connectors.pyhuey.tools.manager import MonkeyManager

    return module, MonkeyManager


def test_capability_handles_unknown_denied_provider_error_and_dry_run(caplog):
    _module, MonkeyManager = _manager_types()
    callback = Mock()
    manager = MonkeyManager(
        authorization_provider=lambda *_args: (_ for _ in ()).throw(
            RuntimeError("prompt unavailable")
        )
    )
    with caplog.at_level(logging.WARNING):
        assert manager._run_capability("unregistered", callback) is False
        assert manager._run_capability("project.container.start", callback) is False
    assert "Blocked unknown operation" in caplog.text
    assert "Authorization provider failed" in caplog.text
    assert callback.call_count == 0

    assert (
        manager._run_capability("project.container.start", callback, dry_run=True)
        is False
    )
    assert callback.call_count == 0


def test_script_execution_guards_paths_and_handles_process_results(
    monkeypatch, tmp_path, caplog
):
    manager_module, MonkeyManager = _manager_types()
    project = tmp_path / "project"
    project.mkdir()
    script = project / "run.py"
    script.write_text("pass\n")
    monkeypatch.setattr(manager_module, "_project_root", lambda: project)
    run = Mock(return_value=SimpleNamespace(returncode=0))
    monkeypatch.setattr(manager_module.subprocess, "run", run)
    manager = MonkeyManager()

    manager._execute_script(None)
    manager._execute_script(project / "missing.py")
    outside = tmp_path / "outside.py"
    outside.write_text("pass\n")
    with caplog.at_level(logging.ERROR):
        manager._execute_script(outside)
    assert "Refusing script outside" in caplog.text
    run.assert_not_called()

    manager._execute_script(script)
    run.assert_called_once_with([str(script)], check=False, shell=False, timeout=300)

    run.reset_mock(return_value=True)
    run.return_value = SimpleNamespace(returncode=3)
    with caplog.at_level(logging.ERROR):
        manager._execute_script(script)
    assert "exit code 3" in caplog.text

    run.side_effect = OSError("not executable")
    with caplog.at_level(logging.ERROR):
        manager._execute_script(script)
    assert "Error running script" in caplog.text


def test_script_capabilities_route_setup_and_action_mappings(monkeypatch):
    manager_module, MonkeyManager = _manager_types()
    calls = []
    paths = SimpleNamespace(
        install=Path("install"), update=Path("update"), run=Path("run")
    )
    monkeypatch.setattr(
        manager_module, "resolve_platform_script_paths", lambda root: paths
    )
    manager = MonkeyManager(
        authorization_provider=lambda operation, _capability: ("operator", True)
    )
    monkeypatch.setattr(manager, "_execute_script", lambda script: calls.append(script))
    manager.install()
    manager.update()
    manager.run_app()
    assert calls == [paths.install, paths.update, paths.run]

    called = []
    manager._run_destructive_action("not_registered", lambda: called.append("bad"))
    manager._run_mutating_action("not_registered", lambda: called.append("bad"))
    assert called == []


def test_path_and_integration_status_printing(monkeypatch, capsys, tmp_path):
    manager_module, MonkeyManager = _manager_types()
    paths = SimpleNamespace(
        install=tmp_path / "install.sh", update=None, run=tmp_path / "run.sh"
    )
    paths.install.touch()
    monkeypatch.setattr(manager_module, "_project_root", lambda: tmp_path)
    monkeypatch.setattr(
        manager_module, "resolve_platform_script_paths", lambda _root: paths
    )
    monkeypatch.setattr(
        manager_module,
        "detect_host_platform",
        lambda: SimpleNamespace(
            runtime_display_name="Test Linux",
            family="linux",
            installer_target="debian",
            is_wsl=False,
        ),
    )
    monkeypatch.setattr(
        manager_module,
        "pyhuey_status",
        lambda: {
            "prepared": True,
            "version": None,
            "module_file": None,
            "custom_function_count": 1,
            "custom_functions": [{"name": "say_hi", "signature": "()"}],
        },
    )
    manager = MonkeyManager()
    payload = manager.path_status()
    assert payload["platform"] == "Test Linux"
    assert payload["install"]["exists"] is True
    assert payload["update"] == {"path": None, "exists": False}
    manager.print_path_status()
    assert '"platform_family": "linux"' in capsys.readouterr().out
    manager.print_integration_status()
    integration = capsys.readouterr().out
    assert "version: unknown" in integration
    assert "module: unresolved" in integration
    assert "say_hi()" in integration


def test_pdf_and_function_reports_and_menu_actions(monkeypatch, capsys, tmp_path):
    _module, MonkeyManager = _manager_types()
    pdf_module = ModuleType("huey.pdf_utils")
    pdf_module.list_available_pdfs = lambda: [tmp_path / "guide.pdf"]
    monkeypatch.setitem(sys.modules, "huey.pdf_utils", pdf_module)
    manager = MonkeyManager()
    assert manager.list_pdfs() == [str(tmp_path / "guide.pdf")]
    manager.print_pdfs()
    assert "Available PDFs:" in capsys.readouterr().out
    pdf_module.list_available_pdfs = lambda: []
    manager.print_pdfs()
    assert "No PDFs found." in capsys.readouterr().out

    monkeypatch.setattr(manager, "registered_functions", lambda: [])
    manager.print_registered_functions()
    assert "No custom functions registered." in capsys.readouterr().out
    monkeypatch.setattr(
        manager, "invoke_registered_function", lambda *_a, **_k: {"ok": True}
    )
    manager.print_registered_function_result("format_text", text="x")
    assert '"ok": true' in capsys.readouterr().out

    monkeypatch.setattr(
        manager,
        "_setup_paths",
        lambda: setattr(manager, "install_path", tmp_path / "install"),
    )
    menu = manager.setup_menu()
    assert "monkey.docker.clean" in menu
    assert menu["monkey.paths.status"].text == "Project Paths"
    menu["monkey.paths.status"].triggered.emit()


def test_manager_system_check_delegates(monkeypatch):
    _module, MonkeyManager = _manager_types()
    calls = []
    check = ModuleType("huey.system_checks")
    check.system_check = lambda: calls.append("checked")
    monkeypatch.setitem(sys.modules, "huey.system_checks", check)
    MonkeyManager().run_system_check()
    assert calls == ["checked"]
