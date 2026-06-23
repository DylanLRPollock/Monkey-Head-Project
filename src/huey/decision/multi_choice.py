"""Multi-option decision helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from .context import DecisionContext


@dataclass(slots=True)
class ChoiceOption:
    name: str
    weight: float
    metadata: dict[str, object] = field(default_factory=dict)


def choose_option(
    context: DecisionContext, options: list[ChoiceOption]
) -> dict[str, object]:
    scored: list[tuple[ChoiceOption, float]] = []
    signal_bonus = context.signal_score()
    for option in options:
        policy_boost = float(option.metadata.get("policy_boost", 0.0))
        scored.append((option, option.weight + signal_bonus + policy_boost))
    winner, final_score = max(scored, key=lambda item: item[1])
    return {
        "winner": winner.name,
        "score": round(final_score, 6),
        "candidates": [
            {"name": option.name, "score": round(score, 6)}
            for option, score in sorted(scored, key=lambda item: item[1], reverse=True)
        ],
    }


__all__ = ["ChoiceOption", "choose_option"]
