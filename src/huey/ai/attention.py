"""Small attention helpers used by the transformer-inspired modules."""

from __future__ import annotations


def score_attention(query: list[float], candidate: list[float]) -> float:
    paired = zip(query, candidate, strict=False)
    numerator = sum(left * right for left, right in paired)
    denominator = max(len(query), len(candidate), 1)
    return round(numerator / denominator, 6)


def rank_candidates(
    query: list[float], candidates: dict[str, list[float]]
) -> list[tuple[str, float]]:
    ranked = [
        (name, score_attention(query, candidate))
        for name, candidate in candidates.items()
    ]
    return sorted(ranked, key=lambda item: item[1], reverse=True)


__all__ = ["rank_candidates", "score_attention"]
