# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test List Available Pdfs module (tests)

import pytest

from huey.os.pdf_utils import list_available_pdfs


def test_list_available_pdfs():
    pdfs = list_available_pdfs("memory/PDF")
    assert pdfs == [
        "Local Large Language Model.pdf",
        "NVIDIA V100 Private-AI Server Research Report for the Monkey Head Project.pdf",
        "Sony Amplifier - 1977.pdf",
    ]


def test_pdf_dir_env(tmp_path, monkeypatch):
    mem = tmp_path / "mem"
    mem.mkdir()
    (mem / "foo.pdf").write_text("dummy")
    monkeypatch.setenv("PDF_DIR", str(mem))
    pdfs = list_available_pdfs()
    assert pdfs == ["foo.pdf"]


def test_pdf_candidate_resolution_and_find_helpers(monkeypatch, tmp_path):
    from huey.memory.PY import pdf_utils

    project = tmp_path / "project"
    memory = tmp_path / "memory"
    project_pdf = project / "documents"
    memory_pdf = memory / "PDF"
    project_pdf.mkdir(parents=True)
    memory_pdf.mkdir(parents=True)
    (project_pdf / "project.pdf").touch()
    (memory_pdf / "memory.pdf").touch()
    monkeypatch.setattr(pdf_utils, "BASE_DIR", project)
    monkeypatch.setattr(pdf_utils, "memory_candidates", lambda: [memory])
    monkeypatch.delenv("PDF_DIR", raising=False)

    assert pdf_utils._iter_pdf_dir_candidates(project_pdf) == [project_pdf]
    assert pdf_utils.list_available_pdfs("documents") == ["project.pdf"]
    assert pdf_utils.find_pdf("memory.pdf", "memory/PDF") == memory_pdf / "memory.pdf"
    assert pdf_utils.find_pdf("missing.pdf", memory_pdf) is None
    assert pdf_utils.list_available_pdfs(tmp_path / "not-a-directory") == []
    assert pdf_utils._default_pdf_candidates() == [memory / "PDF"]


@pytest.mark.parametrize("existing_default", [True, False])
def test_default_pdf_search_prefers_first_existing_candidate(
    monkeypatch, tmp_path, existing_default
):
    from huey.memory.PY import pdf_utils

    first = tmp_path / "first"
    second = tmp_path / "second"
    candidates = [first / "PDF", second / "PDF"]
    if existing_default:
        candidates[1].mkdir(parents=True)
        (candidates[1] / "second.pdf").touch()
    monkeypatch.setattr(pdf_utils, "_default_pdf_candidates", lambda: candidates)
    monkeypatch.delenv("PDF_DIR", raising=False)

    files = pdf_utils.list_available_pdfs()
    assert files == (["second.pdf"] if existing_default else [])
    expected = candidates[1] if existing_default else candidates[0]
    assert pdf_utils.find_pdf("missing.pdf") is None
    assert pdf_utils._resolve_pdf_dir(expected) == (
        expected if expected.is_dir() else None
    )
