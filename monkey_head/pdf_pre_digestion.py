# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Utility to convert PDF documents to plain text and images."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

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
    png_prefix = dirs["PNG"] / stem

    subprocess.run(["pdftotext", str(pdf_path), str(txt_path)], check=True)
    text = txt_path.read_text(encoding="utf-8", errors="ignore")

    json_path.write_text(json.dumps({"text": text}, ensure_ascii=False), encoding="utf-8")

    subprocess.run(["pdftoppm", "-png", str(pdf_path), str(png_prefix)], check=True)

    for png in dirs["PNG"].glob(f"{stem}-*.png"):
        jpeg_out = dirs["JPEG"] / f"{png.stem}.jpg"
        convert_png_to_jpeg(str(png), str(jpeg_out))

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
