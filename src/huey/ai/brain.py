"""Central AI logic for Huey and the speculative GenCore stack."""

from __future__ import annotations

from .inference import InferenceEngine, InferenceRequest
from .learning import LearningEngine
from .model_registry import ModelRegistry


class HueyBrain:
    """Coordinate model registration, inference, and reinforcement feedback."""

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self.registry = registry or ModelRegistry()
        self.registry.register(
            "spark-4-sim",
            provider="local",
            metadata={"family": "transformer", "purpose": "general reasoning"},
            default=True,
        )
        self.learning = LearningEngine()
        self.inference = InferenceEngine(self.registry)

    def think(
        self,
        prompt: str,
        *,
        context: dict[str, object] | None = None,
        model: str | None = None,
    ) -> dict[str, object]:
        return self.inference.run(
            InferenceRequest(prompt=prompt, context=dict(context or {}), model=model)
        )

    def learn(
        self,
        prompt: str,
        response: str,
        *,
        reward: float,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        example = self.learning.record(
            prompt,
            response,
            reward=reward,
            metadata=metadata,
        )
        return {
            "prompt": example.prompt,
            "response": example.response,
            "reward": example.reward,
            "metrics": self.learning.metrics(),
        }

    def model_catalog(self) -> list[dict[str, object]]:
        return self.registry.catalog()


__all__ = ["HueyBrain"]
