"""Abstractions for routing LLM calls through the pygpt-MHP stack."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol

try:  # pragma: no cover - optional dependency tree
    from pygpt.provider.agents.openai import OpenAIAgent
except ModuleNotFoundError:  # pragma: no cover - llama_index missing
    OpenAIAgent = None  # type: ignore[assignment]


class ProviderExecutor(Protocol):
    """Protocol describing callables that execute provider-specific requests."""

    def __call__(
        self,
        *,
        provider: str,
        model: Dict[str, Any],
        persona: str,
        action: Dict[str, Any],
        history: List[Dict[str, Any]],
        provider_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        ...


@dataclass
class StructuredDecision:
    """Structured response from an LLM provider."""

    decision: str
    rationale: str
    confidence: float
    analysis: str
    metadata: Dict[str, Any]


class LLMProviderRegistry:
    """Registry that reads pygpt-MHP model configuration."""

    def __init__(self, models_config_path: Optional[Path] = None) -> None:
        root = Path(__file__).resolve().parents[2]
        default_path = root / "pygpt" / "data" / "config" / "models.json"
        self.models_config_path = models_config_path or default_path
        with self.models_config_path.open("r", encoding="utf-8") as handle:
            loaded: Dict[str, Any] = json.load(handle)
        self._models = loaded.get("items", loaded)

    # ------------------------------------------------------------------
    def get_model(self, model_id: str) -> Dict[str, Any]:
        if model_id not in self._models:
            raise KeyError(f"Model '{model_id}' is not available in pygpt configuration")
        return self._models[model_id]

    # ------------------------------------------------------------------
    def resolve_provider(self, model_id: str) -> str:
        model = self.get_model(model_id)
        provider = model.get("provider") or model.get("langchain", {}).get("provider")
        if not provider:
            raise KeyError(f"Model '{model_id}' does not declare a provider")
        return provider

    # ------------------------------------------------------------------
    def available_providers(self) -> List[str]:
        providers = {model.get("provider") for model in self._models.values() if model.get("provider")}
        return sorted(p for p in providers if p)


PROVIDER_CLASS_MAP: Dict[str, Callable[[], Any]] = {
    "openai": (lambda: OpenAIAgent()) if OpenAIAgent is not None else (lambda: None),
    # Anthropic and Ollama providers are surfaced for completeness even if
    # specialised provider wrappers are supplied at runtime.
    "anthropic": lambda: None,
    "ollama": lambda: None,
}


class PyGPTLLMClient:
    """Adapter that uses pygpt configuration to route LLM decisions."""

    def __init__(
        self,
        model: str,
        *,
        registry: Optional[LLMProviderRegistry] = None,
        executor: Optional[ProviderExecutor] = None,
    ) -> None:
        self.registry = registry or LLMProviderRegistry()
        self.model_id = model
        self.model_config = self.registry.get_model(model)
        self.provider_name = self.registry.resolve_provider(model)
        self.provider_metadata = self._build_provider_metadata(self.provider_name)
        self.executor = executor

    # ------------------------------------------------------------------
    def _build_provider_metadata(self, provider_name: str) -> Dict[str, Any]:
        factory = PROVIDER_CLASS_MAP.get(provider_name)
        metadata: Dict[str, Any] = {"provider": provider_name}
        if factory is None:
            return metadata

        instance = factory()
        if instance is None:
            return metadata

        metadata.update({
            "agent_id": getattr(instance, "id", provider_name),
            "mode": getattr(instance, "mode", "step"),
        })
        return metadata

    # ------------------------------------------------------------------
    def generate_decision(
        self,
        *,
        persona: str,
        action: Dict[str, Any],
        history: List[Dict[str, Any]],
    ) -> StructuredDecision:
        if self.executor is None:
            raise RuntimeError(
                "PyGPTLLMClient requires an executor callable to dispatch provider requests"
            )

        raw = self.executor(
            provider=self.provider_name,
            model=self.model_config,
            persona=persona,
            action=action,
            history=history,
            provider_metadata=self.provider_metadata,
        )

        decision = raw.get("decision", "undetermined").lower()
        rationale = raw.get("rationale", "")
        confidence = float(raw.get("confidence", 0.5))
        analysis = raw.get("analysis", rationale)
        metadata = raw.get("metadata", {})

        return StructuredDecision(
            decision=decision,
            rationale=rationale,
            confidence=confidence,
            analysis=analysis,
            metadata=metadata,
        )

