"""Exercise legacy audit scripts and safe Debian source-list helpers."""

from __future__ import annotations

import importlib
import os
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.routing import APIRoute


def _reload(name: str):
    return importlib.reload(importlib.import_module(f"huey.memory.PY.{name}"))


def test_command_center_contract_success_and_failure(monkeypatch, capsys):
    contract = _reload("check_command_center_contract")
    assert contract.main() == 0
    assert "contract check passed" in capsys.readouterr().out

    def fail_routes():
        raise ValueError("route validation failed")

    monkeypatch.setattr(contract, "assert_routes", fail_routes)
    assert contract.main() == 1
    assert "route validation failed" in capsys.readouterr().out


def test_command_center_contract_route_guards(monkeypatch):
    contract = _reload("check_command_center_contract")
    from huey.apps.command_center import server

    monkeypatch.setattr(server, "create_app", lambda: SimpleNamespace(routes=[]))
    with pytest.raises(AssertionError, match="Missing routes"):
        contract.assert_routes()

    required = {
        "/command-center/launcher",
        "/command-center/meta",
        "/command-center/state",
        "/command-center/safety",
        "/command-center/repos",
        "/command-center/phases",
        "/command-center/validation",
        "/command-center/operator-panel",
        "/command-center/v1-runs/sample",
        "/command-center/prompts/phase/{phase_id}",
    }
    routes = [SimpleNamespace(path=path, methods={"GET"}) for path in required]
    routes[0].methods = {"POST"}
    monkeypatch.setattr(server, "create_app", lambda: SimpleNamespace(routes=routes))
    with pytest.raises(AssertionError, match="read-only"):
        contract.assert_routes()


def _route(path: str, *, methods=None, summary=None, description=None, tags=None):
    def endpoint():
        """An endpoint with useful documentation."""

    route = APIRoute(
        path,
        endpoint,
        methods=["GET"],
        summary=summary,
        description=description,
        tags=tags,
    )
    if methods is not None:
        route.methods = methods
    return route


def test_api_surface_reports_all_defect_categories(monkeypatch, capsys):
    audit = _reload("check_api_surface")
    undocumented = _route("/private", summary=None, description=None, tags=[])
    undocumented.endpoint.__doc__ = None
    undocumented.description = None
    monkeypatch.setattr(
        audit,
        "_load_app",
        lambda: SimpleNamespace(
            routes=[
                undocumented,
                _route("/private", summary="documented", tags=["x"]),
                object(),
            ]
        ),
    )
    assert audit.main() == 1
    output = capsys.readouterr().out
    assert "Duplicate endpoints" in output
    assert "Undocumented endpoints" in output
    assert "Orphan endpoints" in output

    cases = [
        (
            [
                _route("/duplicate", summary="A", tags=["x"]),
                _route("/duplicate", summary="B", tags=["x"]),
            ],
            "Duplicate endpoints",
        ),
        (
            [_route("/undocumented", tags=["x"], description="")],
            "Undocumented endpoints",
        ),
        ([_route("/orphaned", summary="A", tags=[])], "Orphan endpoints without tags"),
    ]
    for routes, expected in cases:
        if expected == "Undocumented endpoints":
            routes[0].endpoint.__doc__ = None
            routes[0].description = None
        monkeypatch.setattr(
            audit, "_load_app", lambda routes=routes: SimpleNamespace(routes=routes)
        )
        assert audit.main() == 1
        assert expected in capsys.readouterr().out


def test_api_surface_accepts_documented_routes_and_filters_http_defaults(
    monkeypatch, capsys
):
    audit = _reload("check_api_surface")
    route = _route("/ready", summary="Readiness", tags=["health"])
    route.methods = {"GET", "HEAD", "OPTIONS"}
    monkeypatch.setattr(
        audit, "_load_app", lambda: SimpleNamespace(routes=[object(), route])
    )
    assert audit._route_signature(route) == ("/ready", ("GET",))
    route.methods = None
    assert audit._route_signature(route) == ("/ready", ())
    route.methods = {"GET"}
    assert audit.main() == 0
    assert "API surface check passed" in capsys.readouterr().out


def test_api_surface_bootstrap_paths_and_app_import(monkeypatch):
    audit = importlib.import_module("huey.memory.PY.check_api_surface")
    for path in (str(audit.SRC), str(audit.VENDOR)):
        while path in sys.path:
            sys.path.remove(path)
    audit = importlib.reload(audit)
    assert str(audit.SRC) in sys.path
    assert str(audit.VENDOR) in sys.path

    app = object()
    monkeypatch.delenv("HUEY_ENV", raising=False)
    monkeypatch.setattr(
        audit.importlib,
        "import_module",
        lambda name: SimpleNamespace(app=app),
    )
    assert audit._load_app() is app
    assert os.environ["HUEY_ENV"] == "development"
    monkeypatch.setenv("HUEY_ENV", "test")
    assert audit._load_app() is app
    assert os.environ["HUEY_ENV"] == "test"


@pytest.mark.parametrize(
    ("module_name", "release"),
    [("update_sources_to_forky", "forky"), ("update_sources_to_trixie", "trixie")],
)
def test_source_line_conversion_preserves_comments_formats_and_components(
    module_name, release
):
    module = _reload(module_name)
    assert (
        module.convert_line("# deb old stable main\n", release)
        == "# deb old stable main\n"
    )
    assert module.convert_line("nonsense\n", release) == "nonsense\n"
    assert module.convert_line(
        f"deb https://example.invalid {release}-security main\r\n", release
    ) == (f"deb https://example.invalid {release}-security main\r\n")
    assert module.convert_line(
        "deb [arch=amd64] https://example.invalid stable main\n", release
    ) == (f"deb [arch=amd64] https://example.invalid {release} main\n")
    assert module.convert_line(
        "deb-src https://example.invalid stable-updates main", release
    ) == (f"deb-src https://example.invalid {release}-updates main")


@pytest.mark.parametrize(
    ("module_name", "release"),
    [("update_sources_to_forky", "forky"), ("update_sources_to_trixie", "trixie")],
)
def test_source_updater_checks_privilege_missing_file_and_writes_backup(
    module_name, release, monkeypatch, tmp_path, capsys
):
    module = _reload(module_name)
    monkeypatch.setattr(module.os, "geteuid", lambda: 1000)
    with pytest.raises(SystemExit) as denied:
        module.main()
    assert denied.value.code == 1
    assert "must be run as root" in capsys.readouterr().err

    monkeypatch.setattr(module.os, "geteuid", lambda: 0)
    monkeypatch.setattr(module.os.path, "isfile", lambda _path: False)
    with pytest.raises(SystemExit) as missing:
        module.main()
    assert missing.value.code == 1

    source = tmp_path / "sources.list"
    backup = tmp_path / "sources.list.bak"
    source.write_text(
        "deb https://example.invalid stable main\n"
        "# deb https://comment.invalid stable main\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "SOURCE_FILE", str(source))
    monkeypatch.setattr(module, "BACKUP_FILE", str(backup))
    monkeypatch.setattr(module.os.path, "isfile", lambda path: Path(path).is_file())
    monkeypatch.setattr(sys, "argv", [module_name, "testing"])
    module.main()
    assert backup.read_text(encoding="utf-8").startswith("deb ")
    assert source.read_text(encoding="utf-8").startswith(
        "deb https://example.invalid testing main"
    )
    assert "sources.list updated to testing" in capsys.readouterr().out


@pytest.mark.parametrize(
    "module_name", ["update_sources_to_forky", "update_sources_to_trixie"]
)
def test_source_updater_exercises_script_entry_guard(monkeypatch, module_name):
    source = (
        Path(__file__).parents[1]
        / "src"
        / "huey"
        / "memory"
        / "PY"
        / f"{module_name}.py"
    )
    monkeypatch.setattr(os, "geteuid", lambda: 1000)
    monkeypatch.setattr(sys, "argv", [str(source)])
    with pytest.raises(SystemExit) as exited:
        runpy.run_path(str(source), run_name="__main__")
    assert exited.value.code == 1
