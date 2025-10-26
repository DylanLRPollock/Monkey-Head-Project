# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Convert Pdf To Text module (tests)

import importlib.util
import shutil
from pathlib import Path

import pytest

pytest.importorskip("pypdf")


def test_convert_pdf_to_text(tmp_path):
    root = Path(__file__).resolve().parents[1]
    module_path = root / "monkey_head" / "convert_pdf_to_text.py"
    spec = importlib.util.spec_from_file_location("cpt", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    convert_pdf_to_text = module.convert_pdf_to_text

    pdf_src = root / "memory" / "PDF" / "Linux_on_PlayStation_3.pdf"
    pdf_copy = tmp_path / "doc.pdf"
    shutil.copy(pdf_src, pdf_copy)
    out_txt = tmp_path / "out.txt"

    convert_pdf_to_text(str(pdf_copy), str(out_txt))
    assert out_txt.exists()
    assert "PlayStation" in out_txt.read_text(encoding="utf-8")
