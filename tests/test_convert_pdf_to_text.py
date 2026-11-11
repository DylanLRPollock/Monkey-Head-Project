# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Convert Pdf To Text module (tests)

from huey.memory.PY.convert_files import convert_pdf_to_text

import pytest

pytest.importorskip("pypdf")


def test_convert_pdf_to_text(tmp_path):
    fitz = pytest.importorskip("fitz")
    pdf_path = tmp_path / "doc.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "PlayStation supports Linux software.")
    document.save(pdf_path)
    document.close()

    result = convert_pdf_to_text(pdf_path)
    assert "PlayStation" in result
