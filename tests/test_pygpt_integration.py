from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

from huey import function_registry
from huey.pygpt_integration import (
    available_sources,
    candidate_sources,
    candidate_src_paths,
    prepare_pygpt,
    pyhuey_status,
    reset_pygpt_state,
)


def test_candidate_src_paths_ignore_external_paths(monkeypatch, tmp_path):
    root = Path(__file__).resolve().parents[1]
    extra_dir = tmp_path / "custom-src"
    extra_dir.mkdir()
    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(extra_dir))

    paths = candidate_src_paths()

    assert paths[0] == root / "src"
    assert paths == [root / "src"]
    assert candidate_src_paths([extra_dir]) == paths


def test_candidate_sources_describe_available_locations():
    root = Path(__file__).resolve().parents[1]
    sources = candidate_sources()
    names = [source.name for source in sources]
    package = next(source for source in sources if source.name == "package")

    assert names == ["package"]
    assert package.package_path == root / "src" / "huey" / "connectors" / "pyhuey"
    assert package.import_name == "huey.connectors.pyhuey"
    assert any(source.name == "package" for source in available_sources())


def test_prepare_pygpt_never_loads_external_sources(monkeypatch, tmp_path):
    dummy_root = tmp_path / "vendor"
    package_root = dummy_root / "pygpt_net"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("__version__ = 'test-vendor'\n")

    monkeypatch.setenv("PYGPT_EXTRA_PATHS", str(dummy_root))
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)

    reset_pygpt_state()
    before = list(sys.path)
    assert not prepare_pygpt()
    assert not prepare_pygpt(source="extra")
    assert not prepare_pygpt(source="installed")
    assert not prepare_pygpt(source="package", search_paths=[dummy_root])
    assert "pygpt_net" not in sys.modules
    assert sys.path == before


def test_prepare_pygpt_package_source_aliases_canonical_connector(monkeypatch):
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)

    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    module = importlib.import_module("pygpt_net")
    module_path = Path(module.__file__).resolve().as_posix()

    assert module_path.endswith("/src/huey/connectors/pyhuey/__init__.py")
    reset_pygpt_state()


def test_prepare_pygpt_registers_custom_functions(monkeypatch):
    monkeypatch.setattr(function_registry, "_FUNCTIONS", {})
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)

    reset_pygpt_state()
    assert prepare_pygpt(source="package")

    assert {
        "auto_sort_memory",
        "find_pdf",
        "format_text",
        "list_available_pdfs",
    } <= set(function_registry.list_functions())


def test_prepare_refuses_to_replace_a_loaded_upstream_module(monkeypatch):
    existing = types.ModuleType("pygpt_net")
    monkeypatch.setitem(sys.modules, "pygpt_net", existing)
    with pytest.raises(RuntimeError, match="refusing to replace"):
        prepare_pygpt(source="package")
    assert sys.modules["pygpt_net"] is existing


def test_default_does_not_activate_previously_prepared_stub(monkeypatch):
    monkeypatch.delitem(sys.modules, "pygpt_net", raising=False)
    assert prepare_pygpt(source="package")
    assert not prepare_pygpt()


def test_llm_adapter_does_not_import_pygpt_even_if_installed(monkeypatch):
    from huey.memory.PY.llm import LLMAdapter

    existing = types.ModuleType("pygpt_net")
    monkeypatch.setitem(sys.modules, "pygpt_net", existing)
    adapter = LLMAdapter("openai", model="test")
    assert adapter.metadata == {}
    assert adapter._pygpt_agent is None
    assert sys.modules["pygpt_net"] is existing
    response = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message={"content": "provider reply"})]
    )
    adapter._client = types.SimpleNamespace(
        chat=types.SimpleNamespace(
            completions=types.SimpleNamespace(create=lambda **kwargs: response)
        )
    )
    assert adapter.generate("hello") == "provider reply"


def test_pyhuey_status_reports_candidates():
    reset_pygpt_state()
    status = pyhuey_status(source="package")

    assert status["prepared"] is True
    assert status["module"] == "pygpt_net"
    assert [candidate["name"] for candidate in status["candidates"]] == ["package"]
    assert status["custom_function_count"] >= 4
    assert {
        "auto_sort_memory",
        "find_pdf",
        "format_text",
        "list_available_pdfs",
    } <= {item["name"] for item in status["custom_functions"]}
