"""Safety and compatibility regressions for the canonical V1 proof path."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from huey.v1.fixture_registry import (
    list_fixtures,
    load_fixture,
    register_fixture,
    verify_fixture,
)
from huey.v1.proof_loop import run_fixture
from huey.v1.report_generator import generate_html_report
from huey.v1.response_bridge import ResponseBridge
from huey.v1.structured_run_log import StructuredRunLog


def test_registry_does_not_create_default_memory_dir_on_read(tmp_path, monkeypatch):
    memory = tmp_path / "uncreated"
    monkeypatch.setenv("MEMORY_PATH", str(memory))
    assert list_fixtures() == []
    assert not memory.exists()


def test_register_and_verify_sha_and_size(tmp_path):
    source = tmp_path / "fixture.txt"
    source.write_text("original", encoding="utf-8")
    registry_path = tmp_path / "registry.json"
    entry = register_fixture(source, registry_path=registry_path)
    assert verify_fixture(entry)
    assert load_fixture(entry["id"], registry_path=registry_path) == entry


def test_duplicate_id_rejected_and_explicit_overwrite_allowed(tmp_path):
    source = tmp_path / "fixture.txt"
    source.write_text("one")
    registry_path = tmp_path / "registry.json"
    register_fixture(source, fixture_id="id", registry_path=registry_path)
    with pytest.raises(ValueError, match="already registered"):
        register_fixture(source, fixture_id="id", registry_path=registry_path)
    updated = register_fixture(
        source, fixture_id="id", registry_path=registry_path,
        description="replacement", overwrite=True,
    )
    assert updated["description"] == "replacement"


def test_registry_detects_modified_and_missing_source(tmp_path):
    source = tmp_path / "fixture.txt"
    source.write_text("original")
    registry_path = tmp_path / "registry.json"
    register_fixture(source, registry_path=registry_path)
    source.write_text("modified")
    with pytest.raises(ValueError, match="integrity"):
        load_fixture("fixture", registry_path=registry_path)
    assert load_fixture("fixture", registry_path=registry_path, verify=False)
    source.unlink()
    with pytest.raises(FileNotFoundError):
        load_fixture("fixture", registry_path=registry_path)


def test_copy_rejects_same_filename_with_different_content(tmp_path, monkeypatch):
    memory = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(memory))
    first = tmp_path / "first" / "fixture.txt"
    second = tmp_path / "second" / "fixture.txt"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("first")
    second.write_text("second")
    registry = tmp_path / "reg.json"
    saved = register_fixture(first, registry_path=registry, copy_to_registry=True)
    with pytest.raises(FileExistsError, match="Different fixture"):
        register_fixture(
            second, fixture_id="second", registry_path=registry,
            copy_to_registry=True,
        )
    assert Path(saved["path"]).read_text() == "first"
    assert len(list_fixtures(registry_path=registry)) == 1


def test_copy_reuses_identical_existing_content(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_PATH", str(tmp_path / "memory"))
    a = tmp_path / "a" / "fixture.txt"
    b = tmp_path / "b" / "fixture.txt"
    a.parent.mkdir()
    b.parent.mkdir()
    a.write_text("equal")
    b.write_text("equal")
    registry_path = tmp_path / "index.json"
    x = register_fixture(a, registry_path=registry_path, copy_to_registry=True)
    y = register_fixture(
        b, fixture_id="second", registry_path=registry_path, copy_to_registry=True
    )
    assert x["path"] == y["path"]


def test_failed_registry_replacement_preserves_old_data(tmp_path, monkeypatch):
    from huey.v1 import fixture_registry as module

    source = tmp_path / "fixture.txt"
    source.write_text("contents")
    registry = tmp_path / "registry.json"
    register_fixture(source, registry_path=registry)
    before = registry.read_bytes()

    def fail_replace(*args):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(module.os, "replace", fail_replace)
    with pytest.raises(OSError):
        register_fixture(
            source, fixture_id="next", registry_path=registry
        )
    assert registry.read_bytes() == before
    assert not list(tmp_path.glob("*.tmp"))


def test_registry_rejects_wrong_shape(tmp_path):
    target = tmp_path / "fixture_registry.json"
    target.write_text("[]")
    with pytest.raises(ValueError, match="Malformed"):
        list_fixtures(registry_path=target)


def test_proof_loop_rejects_tampered_registered_record_before_logging(tmp_path):
    source = tmp_path / "fixture.txt"
    source.write_text("original")
    registry = tmp_path / "fixtures.json"
    record = register_fixture(source, registry_path=registry)
    source.write_text("tampered")
    with pytest.raises(ValueError, match="integrity"):
        run_fixture(record, log_dir=tmp_path / "runs")
    assert not (tmp_path / "runs").exists()


@pytest.mark.parametrize(
    ("legacy", "canonical"),
    [
        ("proof_loop", "proof_loop"),
        ("response_bridge", "response_bridge"),
        ("structured_run_log", "structured_run_log"),
    ],
)
def test_legacy_v1_imports_share_canonical_module_identity(legacy, canonical):
    assert importlib.import_module("huey.memory.PY." + legacy) is (
        importlib.import_module("huey.v1." + canonical)
    )


def test_api_mode_never_fakes_a_successful_inference(monkeypatch):
    monkeypatch.setenv("HUEY_RESPONSE_API_KEY", "test-only")
    with pytest.raises(RuntimeError, match="not implemented"):
        ResponseBridge("api").respond("hello")


def test_html_report_escapes_untrusted_input():
    record = {
        "run_id": "<script>alert(1)</script>",
        "exit_status": "success",
        "transcript": "<b>hello</b>",
        "response": "<img src=x onerror=alert(1)>",
    }
    html = generate_html_report([record])
    assert "<script>" not in html
    assert "<img " not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;" in html


def test_structured_log_rejects_nonobject_jsonl(tmp_path):
    log_file = tmp_path / "run.jsonl"
    log_file.write_text("null\n")
    with pytest.raises(ValueError, match="record type"):
        StructuredRunLog(log_file).read()


def test_structured_log_rejects_non_dict_payload(tmp_path):
    log_file = tmp_path / "run.jsonl"
    with pytest.raises(TypeError, match="dictionary"):
        StructuredRunLog(log_file).append("event", "wrong")
    assert not log_file.exists()
