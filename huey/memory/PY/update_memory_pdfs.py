# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Update Memory Pdfs module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import logging
from pathlib import Path

from ..logging_setup import configure_logging
from .convert_pdf_to_text import convert_pdf_to_text, save_text_to_file

configure_logging()

BASE_DIR = Path(__file__).resolve().parents[2]
PDF_DIR = BASE_DIR / "memory" / "PDF"


def update_memory_pdfs() -> None:
    """Regenerate text files for bundled PDF documents."""
    if not PDF_DIR.is_dir():
        logging.error(f"PDF directory {PDF_DIR} not found")
        return

    for pdf_path in sorted(PDF_DIR.glob("*.pdf")):
        txt_path = PDF_DIR / f"{pdf_path.stem}.txt"
        text = convert_pdf_to_text(str(pdf_path))
        save_text_to_file(text, txt_path)


if __name__ == "__main__":
    update_memory_pdfs()
