# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Chat Learning module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
"""Simple training utility using TensorFlow.

The function :func:`train_from_chat_and_pdfs` builds a very small language
model based on conversation history and the text extracted from one or more
PDF files.  It is intentionally minimal and intended only for demonstration
and testing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import fitz  # PyMuPDF
import tensorflow as tf


def _read_pdf_text(pdf_path: str | Path) -> str:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text


def _prepare_dataset(texts: Iterable[str]):
    joined = " ".join(texts).lower()
    tokenizer = tf.keras.preprocessing.text.Tokenizer()
    tokenizer.fit_on_texts([joined])
    seq = tokenizer.texts_to_sequences([joined])[0]
    if len(seq) < 2:
        raise ValueError("Not enough text for training")
    xs = tf.constant(seq[:-1])
    ys = tf.constant(seq[1:])
    xs = tf.expand_dims(xs, axis=-1)
    return xs, ys, tokenizer


def train_from_chat_and_pdfs(
    chat_history: List[str], pdf_files: List[str], epochs: int = 1
) -> tf.keras.Model:
    """Train a tiny model on chat history and PDFs.

    Args:
        chat_history: List of chat messages.
        pdf_files: Paths to PDF files whose text will be used.
        epochs: Training epochs (default 1).

    Returns:
        The trained :class:`tensorflow.keras.Model`.
    """
    pdf_texts = [_read_pdf_text(p) for p in pdf_files]
    xs, ys, tokenizer = _prepare_dataset(list(chat_history) + pdf_texts)
    vocab_size = len(tokenizer.word_index) + 1
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Embedding(vocab_size, 8, input_length=1),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(vocab_size, activation="softmax"),
        ]
    )
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy")
    model.fit(xs, ys, epochs=epochs, verbose=0)
    return model


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train from chat and PDFs")
    parser.add_argument("pdf", nargs="+", help="PDF files to include")
    parser.add_argument("--chat", nargs="*", default=[], help="Chat messages")
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()

    model = train_from_chat_and_pdfs(args.chat, args.pdf, epochs=args.epochs)
    print(model.summary())
