"""Inference engine built on top of the registry and transformer scaffold."""

from __future__ import annotations

from dataclasses import dataclass, field

from .model_registry import ModelRegistry
from .tokenizer import BasicTokenizer
from .transformers import TransformerBlock


@dataclass(slots=True)
class InferenceRequest:
    prompt: str
    context: dict[str, object] = field(default_factory=dict)
    model: str | None = None


class InferenceEngine:
    """Resolve a model and produce deterministic, inspectable outputs."""

    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
        self.transformer = TransformerBlock(BasicTokenizer())

    def run(self, request: InferenceRequest) -> dict[str, object]:
        record = self.registry.resolve(request.model)
        if record.runner is not None:
            return record.runner(request.prompt, request.context)
        return {
            "model": record.as_dict(),
            "summary": self.transformer.summarize(
                request.prompt,
                context=str(request.context.get("goal", "")) or None,
            ),
            "prompt": request.prompt,
            "context": dict(request.context),
        }


__all__ = ["InferenceEngine", "InferenceRequest"]
