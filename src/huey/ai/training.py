"""Training pipeline primitives for model iteration and registry updates."""

from __future__ import annotations

from dataclasses import dataclass, field

from .learning import LearningEngine
from .model_registry import ModelRecord, ModelRegistry


@dataclass(slots=True)
class TrainingRun:
    model_name: str
    examples_seen: int
    average_reward: float
    metadata: dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_record(cls, record: ModelRecord) -> "TrainingRun":
        return cls(
            model_name=record.name,
            examples_seen=int(record.metadata.get("examples_seen", 0)),
            average_reward=float(record.metadata.get("average_reward", 0.0)),
            metadata=dict(record.metadata),
        )


class TrainingPipeline:
    """Compile learning metrics into a new model registry record."""

    def __init__(self, learning: LearningEngine, registry: ModelRegistry) -> None:
        self.learning = learning
        self.registry = registry

    def train(self, *, model_name: str, provider: str = "local") -> TrainingRun:
        metrics = self.learning.metrics()
        examples_seen = int(metrics["examples"])
        average_reward = float(metrics["average_reward"])
        record = self.registry.register(
            model_name,
            version=f"0.1.{examples_seen}",
            provider=provider,
            metadata={
                "examples_seen": examples_seen,
                "average_reward": average_reward,
            },
            default=True,
        )
        return TrainingRun.from_record(record)

__all__ = ["TrainingPipeline", "TrainingRun"]
