# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Pdf Chat module (tests)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.12.2025
# ==================================================
import importlib

import pytest

pytest.importorskip("pypdf")

pdf_chat = importlib.import_module("huey.memory.PY.pdf_chat")


@pytest.fixture
def sample_pdf(tmp_path):
    fitz = pytest.importorskip("fitz")
    path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "PlayStation supports Linux software.")
    document.save(path)
    document.close()
    return path


def test_load_pdf_pages(sample_pdf):
    pdf_path = sample_pdf
    pages = pdf_chat.load_pdf_pages(str(pdf_path))
    assert isinstance(pages, list)
    assert pages and isinstance(pages[0], str)


def test_answer_question(sample_pdf):
    pdf_path = sample_pdf
    pages = pdf_chat.load_pdf_pages(str(pdf_path))
    answer = pdf_chat.answer_question(pages, "PlayStation")
    assert "PlayStation" in answer
