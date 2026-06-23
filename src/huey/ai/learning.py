"""Learning data capture for the speculative brain modules."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class LearningExample:
    prompt: str
    response: str
    reward: float
    metadata: dict[str, object] = field(default_factory=dict)


class LearningEngine:
    """Store feedback examples and expose simple aggregate metrics."""

    def __init__(self) -> None:
        self._examples: list[LearningExample] = []

    def record(
        self,
        prompt: str,
        response: str,
        *,
        reward: float,
        metadata: dict[str, object] | None = None,
    ) -> LearningExample:
        example = LearningExample(
            prompt=prompt,
            response=response,
            reward=reward,
            metadata=dict(metadata or {}),
        )
        self._examples.append(example)
        return example

    def dataset(self) -> list[LearningExample]:
        return list(self._examples)

    def metrics(self) -> dict[str, float]:
        if not self._examples:
            return {"examples": 0.0, "average_reward": 0.0}
        total_reward = sum(example.reward for example in self._examples)
        return {
            "examples": float(len(self._examples)),
            "average_reward": round(total_reward / len(self._examples), 4),
        }


__all__ = ["LearningEngine", "LearningExample"]
