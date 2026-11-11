"""Test read-only repository audits and legacy license state helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

LEGACY = Path(__file__).resolve().parents[1] / "src/huey/memory/PY"


def _load_script(monkeypatch, filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, LEGACY / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def test_api_surface_audit_reports_success_and_duplicate_or_missing_docs(
    monkeypatch, capsys
):
    module = _load_script(monkeypatch, "check_api_surface.py", "coverage_api_surface")

    class Route:
        def __init__(
            self, path, methods, *, summary=None, description=None, tags=None, doc=None
        ):
            self.path = path
            self.methods = methods
            self.summary = summary
            self.description = description
            self.tags = tags
            self.endpoint = SimpleNamespace(__doc__=doc)

    monkeypatch.setattr(module, "APIRoute", Route)
    good = Route("/ready", {"GET", "HEAD", "OPTIONS"}, summary="Ready", tags=["health"])
    assert module._route_signature(good) == ("/ready", ("GET",))
    assert module._route_signature(SimpleNamespace(path="/empty", methods=None)) == (
        "/empty",
        (),
    )
    monkeypatch.setattr(
        module, "_load_app", lambda: SimpleNamespace(routes=[good, object()])
    )
    assert module.main() == 0
    assert "API surface check passed" in capsys.readouterr().out

    undocumented = Route("/private", {"POST"})
    monkeypatch.setattr(
        module,
        "_load_app",
        lambda: SimpleNamespace(routes=[good, good, undocumented]),
    )
    assert module.main() == 1
    output = capsys.readouterr().out
    assert "Duplicate endpoints" in output
    assert "Undocumented endpoints" in output
    assert "Orphan endpoints without tags" in output


def test_command_center_contract_checks_and_error_report(monkeypatch, capsys):
    module = _load_script(
        monkeypatch,
        "check_command_center_contract.py",
        "coverage_command_center_contract",
    )
    module.assert_imports()
    module.assert_routes()
    module.assert_launcher_support()
    module.assert_safety_policy()
    assert module.main() == 0
    assert "Command Center contract check passed" in capsys.readouterr().out

    monkeypatch.setattr(
        module,
        "assert_imports",
        lambda: (_ for _ in ()).throw(AssertionError("policy drift")),
    )
    assert module.main() == 1
    assert "policy drift" in capsys.readouterr().out


def test_license_acceptance_hash_and_missing_tk_path(tmp_path, monkeypatch):
    from huey.memory.PY import install_gui, license_gui

    config = tmp_path / "license.json"
    license_gui.accept_license(config, "abc123")
    assert license_gui.license_is_current(config, "abc123")
    assert not license_gui.license_is_current(config, "new-hash")
    assert not license_gui.license_is_current(tmp_path / "empty.json", "abc123")

    text, digest = license_gui._read_license_text()
    assert text
    assert len(digest) == 64
    assert install_gui._read_license_text()
    install_gui.validate_license_acceptance(True)
    with pytest.raises(PermissionError):
        install_gui.validate_license_acceptance(False)

    monkeypatch.setattr(license_gui, "tk", None)
    with pytest.raises(RuntimeError, match="tkinter is not available"):
        license_gui.show_license_gui(config)
    monkeypatch.setattr(install_gui, "tk", None)
    with pytest.raises(RuntimeError, match="tkinter is not available"):
        install_gui.launch_install_gui(config)
