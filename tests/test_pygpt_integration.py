from __future__ import annotations

import importlib
import sys
from pathlib import Path

from huey.pygpt_integration import (
    available_sources,
    candidate_sources,
    candidate_src_paths,
    prepare_pygpt,
    pyhuey_status,
    reset_pygpt_state,
)


def test_candidate_src_paths_resolves_defaults_and_env(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]
    extra_dir = tmp_path / "custom-src"
    extra_dir.mkdir()
    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(extra_dir))

    paths = candidate_src_paths()

    assert paths[0] == root / "src"
    assert paths[1] == root / "integrations" / "pyhuey" / "src"
    assert root / "vendor" / "pygpt" / "pygpt-mhp" / "src" in paths
    assert extra_dir in paths


def test_candidate_sources_describe_available_locations():
    root = Path(__file__).resolve().parents[1]
    sources = candidate_sources()
    names = [source.name for source in sources]
    package = next(source for source in sources if source.name == "package")

    assert names[:3] == ["package", "pyhuey", "vendor"]
    assert package.package_path == root / "src" / "huey" / "connectors" / "pyhuey"
    assert package.import_name == "huey.connectors.pyhuey"
    assert any(source.name == "package" for source in available_sources())


def test_prepare_pygpt_uses_extra_paths(monkeypatch, tmp_path):
    dummy_root = tmp_path / "vendor"
    package_root = dummy_root / "pygpt_net"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("__version__ = 'test-vendor'\n")

    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(dummy_root))
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)

    reset_pygpt_state()
    assert prepare_pygpt(source="extra")

    import pygpt_net  # type: ignore

    assert getattr(pygpt_net, "__version__", None) == "test-vendor"
    reset_pygpt_state()


def test_prepare_pygpt_package_source_aliases_canonical_connector(monkeypatch):
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)

    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    module = importlib.import_module("pygpt_net")
    module_path = Path(module.__file__).resolve().as_posix()

    assert module_path.endswith("/src/huey/connectors/pyhuey/__init__.py")
    reset_pygpt_state()


def test_pyhuey_status_reports_candidates():
    reset_pygpt_state()
    status = pyhuey_status(source="package")

    assert status["prepared"] is True
    assert status["module"] == "pygpt_net"
    assert any(candidate["name"] == "pyhuey" for candidate in status["candidates"])
