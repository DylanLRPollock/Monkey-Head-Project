"""Transformer-inspired summarization blocks for the scaffold."""

from __future__ import annotations

from dataclasses import dataclass

from .attention import rank_candidates
from .embeddings import embed_text
from .tokenizer import BasicTokenizer


@dataclass(slots=True)
class TransformerBlock:
    """Summarize text by combining token counts and attention ranking."""

    tokenizer: BasicTokenizer

    def encode(self, text: str) -> dict[str, object]:
        tokens = self.tokenizer.tokenize(text)
        counts = self.tokenizer.token_counts(text)
        query = embed_text(text)
        candidates = {token: embed_text(token, dimensions=len(query)) for token in counts}
        ranked = rank_candidates(query, candidates)
        return {
            "tokens": tokens,
            "token_counts": counts,
            "embedding": query,
            "salient_tokens": [name for name, _ in ranked[:5]],
        }

    def summarize(self, text: str, *, context: str | None = None) -> str:
        encoded = self.encode(text)
        summary_parts = [
            f"tokens={len(encoded['tokens'])}",
            f"salient={', '.join(encoded['salient_tokens']) or 'none'}",
        ]
        if context:
            summary_parts.append(f"context={context}")
        return " | ".join(summary_parts)


__all__ = ["TransformerBlock"]
