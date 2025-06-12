# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Pre-digest PDF documents for AI consumption.

The utility extracts and cleans text from each page, formats it using
``format_text`` for consistent line lengths, and saves the result to both a
plain text file and structured JSON. Pages are also rendered to PNG and JPEG
images.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import fitz  # PyMuPDF
from pypdf import PdfReader

from .formatter import format_text
from .convert_png_to_jpeg import convert_png_to_jpeg


_DEF_MEM_DIR = Path("memory")


def _ensure_dirs(base: Path) -> dict[str, Path]:
    dirs = {
        "TXT": base / "TXT",
        "JSON": base / "JSON",
        "PNG": base / "PNG",
        "JPEG": base / "JPEG",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def _normalize(text: str) -> str:
    """Clean up extracted PDF text for AI consumption."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"-\n", "", text)  # join hyphenated line breaks
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def _extract_text_pages(pdf_path: Path) -> list[str]:
    """Return a list of normalized and formatted page texts."""
    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        cleaned = _normalize(page_text)
        pages.append(format_text(cleaned))
    return pages


def _save_images(pdf_path: Path, png_dir: Path, jpg_dir: Path, stem: str) -> None:
    """Render each page of ``pdf_path`` to PNG and JPEG images."""
    doc = fitz.open(str(pdf_path))
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap()
        png_path = png_dir / f"{stem}-{i + 1}.png"
        pix.save(png_path)
        jpeg_out = jpg_dir / f"{stem}-{i + 1}.jpg"
        convert_png_to_jpeg(str(png_path), str(jpeg_out))


def pdf_pre_digestion(pdf_file: str, memory_dir: str | Path = _DEF_MEM_DIR) -> dict[str, Path]:
    """Convert a PDF file into text, JSON, PNG and JPEG files.

    Args:
        pdf_file: Path to the input PDF document.
        memory_dir: Base directory where output subfolders reside.

    Returns:
        Mapping of output types to the created file paths.
    """
    pdf_path = Path(pdf_file)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_file)

    mem_base = Path(memory_dir)
    dirs = _ensure_dirs(mem_base)
    stem = pdf_path.stem

    txt_path = dirs["TXT"] / f"{stem}.txt"
    json_path = dirs["JSON"] / f"{stem}.json"

    pages = _extract_text_pages(pdf_path)

    with txt_path.open("w", encoding="utf-8") as f:
        for i, page in enumerate(pages, 1):
            f.write(f"--- Page {i} ---\n{page}\n\n")

    json_path.write_text(json.dumps({"pages": pages}, ensure_ascii=False, indent=2), encoding="utf-8")

    _save_images(pdf_path, dirs["PNG"], dirs["JPEG"], stem)

    return {
        "txt": txt_path,
        "json": json_path,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pre-digest a PDF document")
    parser.add_argument("pdf_file", help="Path to input PDF")
    parser.add_argument(
        "--memory-dir",
        default=str(_DEF_MEM_DIR),
        help="Base memory directory to store outputs",
    )
    args = parser.parse_args()

    pdf_pre_digestion(args.pdf_file, args.memory_dir)
    print("PDF processed")
