# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Pdf Pre Digestion module (tests)

import json

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
from pathlib import Path

import pytest

pytest.importorskip("fitz")
pytest.importorskip("PIL.Image")
import fitz

from huey.os.pdf_pre_digestion import pdf_pre_digestion


def _create_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Huey PDF digestion test fixture")
    document.save(path)
    document.close()


def test_pdf_pre_digestion(tmp_path):
    pdf_path = tmp_path / "doc.pdf"
    _create_pdf(pdf_path)

    mem_dir = tmp_path / "mem"
    pdf_pre_digestion(str(pdf_path), str(mem_dir))

    txt_file = mem_dir / "TXT" / "doc.txt"
    json_file = mem_dir / "JSON" / "doc.json"

    assert txt_file.exists()
    assert json_file.exists()

    text = txt_file.read_text(encoding="utf-8")
    assert "----- Page 1 -----" in text

    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert "pages" in data and isinstance(data["pages"], list)
    assert any(p.get("page") == 1 for p in data["pages"])

    assert any(mem_dir.joinpath("PNG").glob("doc-*.png"))
    assert any(mem_dir.joinpath("JPEG").glob("doc-*.jpg"))


def test_pdf_pre_digestion_env(tmp_path, monkeypatch):
    pdf_path = tmp_path / "doc.pdf"
    _create_pdf(pdf_path)

    mem_dir = tmp_path / "env_mem"
    monkeypatch.setenv("MEMORY_DIR", str(mem_dir))
    pdf_pre_digestion(str(pdf_path))

    assert (mem_dir / "TXT" / "doc.txt").exists()
