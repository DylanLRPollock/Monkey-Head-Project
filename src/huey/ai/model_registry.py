"""Registry for model metadata and lightweight callable backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

ModelCallable = Callable[[str, dict[str, object]], dict[str, object]]


@dataclass(slots=True)
class ModelRecord:
    name: str
    version: str
    provider: str
    metadata: dict[str, object] = field(default_factory=dict)
    runner: ModelCallable | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "provider": self.provider,
            "metadata": dict(self.metadata),
        }


class ModelRegistry:
    """Track model records and resolve a default model for inference."""

    def __init__(self) -> None:
        self._models: dict[str, ModelRecord] = {}
        self._default_model: str | None = None

    def register(
        self,
        name: str,
        *,
        version: str = "0.1.0",
        provider: str = "local",
        metadata: dict[str, object] | None = None,
        runner: ModelCallable | None = None,
        default: bool = False,
    ) -> ModelRecord:
        record = ModelRecord(
            name=name,
            version=version,
            provider=provider,
            metadata=dict(metadata or {}),
            runner=runner,
        )
        self._models[name] = record
        if default or self._default_model is None:
            self._default_model = name
        return record

    def resolve(self, name: str | None = None) -> ModelRecord:
        selected = name or self._default_model
        if selected is None:
            raise KeyError("No models have been registered")
        return self._models[selected]

    def catalog(self) -> list[dict[str, object]]:
        return [self._models[name].as_dict() for name in sorted(self._models)]


__all__ = ["ModelCallable", "ModelRecord", "ModelRegistry"]
