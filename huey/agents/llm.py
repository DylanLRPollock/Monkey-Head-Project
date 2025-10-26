# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Llm module (huey/agents)

"""Abstractions for interacting with LLM providers via the pygpt-MHP stack."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


class LLMProvider(str, Enum):
    """Supported language model providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMAdapter:
    """Provider agnostic wrapper around chat completion style APIs."""

    def __init__(
        self,
        provider: LLMProvider | str,
        *,
        model: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.provider = LLMProvider(provider)
        self.model = model
        self.settings = settings or {}
        self.metadata = self._load_metadata()
        self._client: Any | None = None
        self._pygpt_agent: Any | None = None
        self._register_with_pygpt()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate(
        self,
        prompt: str,
        *,
        messages: Optional[Sequence[Dict[str, str]]] = None,
        **kwargs: Any,
    ) -> str:
        """Generate a response using the configured provider.

        When the actual provider SDK is unavailable a deterministic fallback
        response is returned to keep the system operational during tests or on
        air-gapped deployments.
        """

        message_history = (
            list(messages) if messages else [{"role": "user", "content": prompt}]
        )
        try:
            client = self._ensure_client()
        except RuntimeError as exc:  # pragma: no cover - exercised when deps missing
            return self._fallback_response(prompt, message_history, error=exc)

        if self.provider is LLMProvider.OPENAI:
            return self._call_openai(client, message_history, kwargs)
        if self.provider is LLMProvider.ANTHROPIC:
            return self._call_anthropic(client, message_history, kwargs)
        if self.provider is LLMProvider.OLLAMA:
            return self._call_ollama(client, message_history, kwargs)
        raise ValueError(f"Unsupported provider: {self.provider.value}")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _load_metadata(self) -> Dict[str, Any]:
        """Load preset metadata from the pygpt configuration tree."""

        preset_name = f"agent_{self.provider.value}.json"
        preset_path = (
            Path(__file__).resolve().parents[2]
            / "pygpt"
            / "data"
            / "config"
            / "presets"
            / preset_name
        )
        if preset_path.exists():
            try:
                return json.loads(preset_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def _register_with_pygpt(self) -> None:
        """Instantiate a pygpt agent wrapper for integration metadata."""

        try:
            if self.provider is LLMProvider.OPENAI:
                from pygpt.provider.agents.openai import OpenAIAgent as ProviderAgent
            elif self.provider is LLMProvider.ANTHROPIC:
                from pygpt.provider.agents.react import ReactAgent as ProviderAgent
            else:
                from pygpt.provider.agents.planner import PlannerAgent as ProviderAgent
        except Exception:  # pragma: no cover - optional dependency path
            self._pygpt_agent = None
            return

        try:
            self._pygpt_agent = ProviderAgent()
        except Exception:  # pragma: no cover - defensive
            self._pygpt_agent = None

    def _ensure_client(self) -> Any:
        if self._client is not None:
            return self._client
        try:
            if self.provider is LLMProvider.OPENAI:
                from openai import OpenAI

                api_key = self.settings.get("api_key")
                self._client = OpenAI(api_key=api_key) if api_key else OpenAI()
            elif self.provider is LLMProvider.ANTHROPIC:
                from anthropic import Anthropic

                api_key = self.settings.get("api_key")
                self._client = Anthropic(api_key=api_key) if api_key else Anthropic()
            else:  # Ollama
                import ollama

                self._client = ollama
        except ImportError as exc:
            raise RuntimeError(
                f"The {self.provider.value} client library is not installed"
            ) from exc
        return self._client

    def _call_openai(
        self,
        client: Any,
        messages: Sequence[Dict[str, str]],
        kwargs: Dict[str, Any],
    ) -> str:
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=list(messages),
                **kwargs,
            )
            return response.choices[0].message["content"]
        except Exception as exc:  # pragma: no cover - depends on external API
            return self._fallback_response("", messages, error=exc)

    def _call_anthropic(
        self,
        client: Any,
        messages: Sequence[Dict[str, str]],
        kwargs: Dict[str, Any],
    ) -> str:
        try:
            response = client.messages.create(
                model=self.model,
                messages=list(messages),
                **kwargs,
            )
            # anthropic SDK returns list of content blocks
            if getattr(response, "content", None):
                block = response.content[0]
                return getattr(block, "text", str(block))
            return str(response)
        except Exception as exc:  # pragma: no cover - depends on external API
            return self._fallback_response("", messages, error=exc)

    def _call_ollama(
        self,
        client: Any,
        messages: Sequence[Dict[str, str]],
        kwargs: Dict[str, Any],
    ) -> str:
        try:
            result = client.chat(
                model=self.model,
                messages=list(messages),
                **kwargs,
            )
            if isinstance(result, dict) and "message" in result:
                return result["message"].get("content", "")
            return str(result)
        except Exception as exc:  # pragma: no cover - depends on external API
            return self._fallback_response("", messages, error=exc)

    def _fallback_response(
        self,
        prompt: str,
        messages: Sequence[Dict[str, str]],
        *,
        error: Optional[Exception] = None,
    ) -> str:
        """Return a deterministic offline response."""

        last_message = messages[-1]["content"] if messages else prompt
        summary = last_message[:160].strip().replace("\n", " ")
        provider = self.provider.value
        if error:
            return (
                f"[{provider} offline] Unable to reach provider because {error}. "
                f"Summary of request: {summary}"
            )
        return f"[{provider} offline] Summary of request: {summary}"


__all__ = ["LLMAdapter", "LLMProvider"]
