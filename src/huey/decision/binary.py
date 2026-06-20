"""Binary decision engine for yes/no governance and runtime choices."""

from __future__ import annotations

from dataclasses import dataclass

from .context import DecisionContext


@dataclass(slots=True)
class BinaryDecision:
    approved: bool
    score: float
    threshold: float
    rationale: str


def decide_yes_no(
    context: DecisionContext,
    *,
    threshold: float = 0.5,
    bias: float = 0.0,
) -> BinaryDecision:
    score = context.signal_score() + bias
    approved = score >= threshold
    rationale = (
        f"goal={context.goal}; score={score:.3f}; threshold={threshold:.3f}; "
        f"constraints={len(context.constraints)}"
    )
    return BinaryDecision(
        approved=approved,
        score=round(score, 6),
        threshold=threshold,
        rationale=rationale,
    )


__all__ = ["BinaryDecision", "decide_yes_no"]
