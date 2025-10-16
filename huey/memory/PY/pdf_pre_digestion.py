# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Pdf Pre Digestion module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utility to convert PDF documents to plain text and images.

This version relies solely on :mod:`PyMuPDF` so no external ``pdftotext`` or
``pdftoppm`` binaries are required.  The output text is formatted using the
project's :func:`~monkey_head.formatter.format_text` helper to keep line lengths
manageable for AI models.  Each page is rendered to a PNG and also converted to
JPEG for compatibility with other tools.
"""

from __future__ import annotations

import json
from typing import List
import os
from pathlib import Path

import fitz  # PyMuPDF

from .convert_png_to_jpeg import convert_png_to_jpeg
from .formatter import format_text


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


def pdf_pre_digestion(
    pdf_file: str,
    memory_dir: str | Path | None = None,
) -> dict[str, Path]:
    """Convert a PDF file into formatted text, structured JSON and page images.

    Args:
        pdf_file: Path to the input PDF document.
        memory_dir: Base directory where output subfolders reside.

    Returns:
        Mapping of output types to the created file paths.
    """
    pdf_path = Path(pdf_file)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_file)

    if memory_dir is None:
        env = os.environ.get("MEMORY_DIR")
        mem_base = Path(env) if env else _DEF_MEM_DIR
    else:
        mem_base = Path(memory_dir)
    dirs = _ensure_dirs(mem_base)
    stem = pdf_path.stem

    txt_path = dirs["TXT"] / f"{stem}.txt"
    json_path = dirs["JSON"] / f"{stem}.json"

    doc = fitz.open(pdf_path)
    pages_data: List[dict[str, object]] = []
    with txt_path.open("w", encoding="utf-8") as txt_file:
        for i, page in enumerate(doc, start=1):
            raw = page.get_text()
            pages_data.append({"page": i, "text": raw})
            formatted = format_text(raw)
            txt_file.write(f"----- Page {i} -----\n{formatted}\n\n")

            pix = page.get_pixmap()
            png_out = dirs["PNG"] / f"{stem}-{i}.png"
            pix.save(png_out)
            jpeg_out = dirs["JPEG"] / f"{stem}-{i}.jpg"
            convert_png_to_jpeg(str(png_out), str(jpeg_out))

    json_path.write_text(
        json.dumps({"pages": pages_data}, ensure_ascii=False), encoding="utf-8"
    )

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
        default=os.environ.get("MEMORY_DIR", str(_DEF_MEM_DIR)),
        help="Base memory directory to store outputs",
    )
    args = parser.parse_args()

    pdf_pre_digestion(args.pdf_file, args.memory_dir)
    print("PDF processed")
