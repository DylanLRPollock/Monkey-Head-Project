"""Minimal LLM adapter used by the presidential agent layer."""

from __future__ import annotations

from enum import Enum


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    OLLAMA = "ollama"


class LLMAdapter:
    """Deterministic fallback adapter for repository-local tests and tooling."""

    def __init__(
        self,
        provider: LLMProvider | str,
        *,
        model: str,
        settings: dict[str, object] | None = None,
    ) -> None:
        self.provider = LLMProvider(provider)
        self.model = model
        self.settings = dict(settings or {})

    def generate(self, prompt: str) -> str:
        lowered = prompt.lower()
        if "risk" in lowered or "halt" in lowered:
            return f"{self.model}: reject until risk is reduced"
        return f"{self.model}: approve with logged safeguards"


__all__ = ["LLMAdapter", "LLMProvider"]
