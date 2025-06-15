# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Tiny in-memory vector store using cosine similarity."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from typing import List


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class VectorStore:
    embeddings: list[list[float]] = field(default_factory=list)
    texts: list[str] = field(default_factory=list)

    def add(self, text: str, embedding: list[float]) -> None:
        self.texts.append(text)
        self.embeddings.append(embedding)

    def query(self, embedding: list[float], top_k: int = 1) -> list[str]:
        scores = [(_cosine(embedding, e), t) for e, t in zip(self.embeddings, self.texts)]
        scores.sort(reverse=True)
        return [t for _, t in scores[:top_k]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo vector store")
    parser.add_argument("query", type=float, nargs="+", help="Query embedding")
    args = parser.parse_args()

    store = VectorStore()
    store.add("hello", [0.1, 0.9])
    store.add("world", [0.9, 0.1])
    result = store.query(args.query)[0]
    print(f"Closest text: {result}")


if __name__ == "__main__":  # pragma: no cover - example script
    main()

