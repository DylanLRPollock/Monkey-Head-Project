"""Deterministic embedding helpers for text and lightweight multimodal IDs."""

from __future__ import annotations

from hashlib import sha256

from .tokenizer import BasicTokenizer


def embed_text(text: str, *, dimensions: int = 12) -> list[float]:
    tokenizer = BasicTokenizer()
    normalized = tokenizer.detokenize(tokenizer.tokenize(text))
    digest = sha256(normalized.encode("utf-8")).digest()
    vector = [round(byte / 255.0, 6) for byte in digest[:dimensions]]
    if len(vector) < dimensions:
        vector.extend(0.0 for _ in range(dimensions - len(vector)))
    return vector


def embed_media_id(identifier: str, *, kind: str) -> list[float]:
    return embed_text(f"{kind}:{identifier}", dimensions=8)


__all__ = ["embed_media_id", "embed_text"]
