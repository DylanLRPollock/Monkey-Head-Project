# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.12.2025
# ==================================================
"""Interactive utility for chatting with a PDF document."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

try:  # pragma: no cover - optional dependency
    from pypdf import PdfReader
except Exception:  # pragma: no cover - missing optional dep
    PdfReader = None  # type: ignore

from .formatter import format_text


def load_pdf_pages(pdf_file: str | Path) -> List[str]:
    """Return the text of each page in ``pdf_file`` as a list."""
    if PdfReader is None:  # pragma: no cover - optional dependency
        raise RuntimeError("pypdf is required to load PDFs")
    path = Path(pdf_file)
    if not path.is_file():
        raise FileNotFoundError(pdf_file)
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return pages


def answer_question(pages: List[str], question: str) -> str:
    """Return a sentence from ``pages`` matching ``question``."""
    words = re.findall(r"\w+", question.lower())
    best_sentence = None
    best_score = 0
    for page in pages:
        for sentence in re.split(r"[.!?]\s+", page):
            tokens = re.findall(r"\w+", sentence.lower())
            score = sum(1 for w in words if w in tokens)
            if score > best_score:
                best_score = score
                best_sentence = sentence
    if best_sentence:
        return format_text(best_sentence.strip())
    return "I could not find an answer in the document."


def chat_with_pdf(pdf_file: str) -> None:
    """Start an interactive Q&A session using ``pdf_file``."""
    pages = load_pdf_pages(pdf_file)
    print(f"Loaded {len(pages)} pages from {pdf_file}")
    while True:
        try:
            question = input("Ask about the PDF ('quit' to exit): ")
        except EOFError:  # pragma: no cover - interactive mode
            break
        if question.lower().strip() in {"quit", "exit"}:
            break
        answer = answer_question(pages, question)
        print(answer)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Conversation with a PDF file")
    parser.add_argument("pdf", help="Path to the PDF document")
    args = parser.parse_args()

    chat_with_pdf(args.pdf)
