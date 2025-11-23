# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Tensorflow Feed module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Utilities to train TensorFlow models on project data."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import List

from .chat_learning import train_from_chat_and_pdfs


def load_logs(log_dir: str | Path) -> List[str]:
    """Return contents of ``log_dir`` text and log files."""
    texts: List[str] = []
    for path in Path(log_dir).glob("*"):
        if path.is_file() and path.suffix in {".txt", ".log"}:
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except Exception:
                pass
    return texts


def load_prompts(prompts_dir: str | Path) -> List[str]:
    """Return text from prompt files under ``prompts_dir``."""
    texts: List[str] = []
    base = Path(prompts_dir)
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix == ".txt":
            try:
                texts.append(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        elif path.suffix == ".csv":
            try:
                with path.open(encoding="utf-8") as f:
                    reader = csv.reader(f)
                    for row in reader:
                        texts.extend(row)
            except Exception:
                pass
    return texts


def load_memory_texts(memory_dir: str | Path) -> List[str]:
    """Return JSON contents stored under ``memory_dir``."""
    texts: List[str] = []
    base = Path(memory_dir)
    for path in base.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            texts.append(json.dumps(data))
        except Exception:
            pass
    return texts


def train_from_project_sources(
    log_dir: str | Path,
    prompts_dir: str | Path,
    memory_dir: str | Path,
    epochs: int = 1,
):
    """Train a model on logs, prompts and memory PDFs."""
    chat_history = (
        load_logs(log_dir) + load_prompts(prompts_dir) + load_memory_texts(memory_dir)
    )
    pdf_files = [str(p) for p in Path(memory_dir).rglob("*.pdf")]
    return train_from_chat_and_pdfs(chat_history, pdf_files, epochs=epochs)
