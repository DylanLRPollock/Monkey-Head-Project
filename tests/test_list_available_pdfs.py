# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test List Available Pdfs module (tests)

from huey.os.pdf_utils import list_available_pdfs


def test_list_available_pdfs():
    pdfs = list_available_pdfs("memory/PDF")
    assert "Linux_on_PlayStation_3.pdf" in pdfs


def test_pdf_dir_env(tmp_path, monkeypatch):
    mem = tmp_path / "mem"
    mem.mkdir()
    (mem / "foo.pdf").write_text("dummy")
    monkeypatch.setenv("PDF_DIR", str(mem))
    pdfs = list_available_pdfs()
    assert pdfs == ["foo.pdf"]
