"""Tokenization utilities used by the lightweight AI scaffold."""

from __future__ import annotations

import re


class BasicTokenizer:
    """Whitespace and punctuation aware tokenizer with deterministic output."""

    _pattern = re.compile(r"[A-Za-z0-9_'-]+")

    def tokenize(self, text: str) -> list[str]:
        return self._pattern.findall(text.lower())

    def detokenize(self, tokens: list[str]) -> str:
        return " ".join(token.strip() for token in tokens if token.strip())

    def token_counts(self, text: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for token in self.tokenize(text):
            counts[token] = counts.get(token, 0) + 1
        return counts


__all__ = ["BasicTokenizer"]
