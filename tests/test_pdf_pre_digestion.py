# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
from pathlib import Path
import shutil

from monkey_head.pdf_pre_digestion import pdf_pre_digestion


def test_pdf_pre_digestion(tmp_path):
    pdf_src = Path("memory/PDF/Linux_on_PlayStation_3.pdf")
    pdf_path = tmp_path / "doc.pdf"
    shutil.copy(pdf_src, pdf_path)

    mem_dir = tmp_path / "mem"
    pdf_pre_digestion(str(pdf_path), str(mem_dir))

    assert (mem_dir / "TXT" / "doc.txt").exists()
    assert (mem_dir / "JSON" / "doc.json").exists()
    assert any(mem_dir.joinpath("PNG").glob("doc-*.png"))
    assert any(mem_dir.joinpath("JPEG").glob("doc-*.jpg"))
