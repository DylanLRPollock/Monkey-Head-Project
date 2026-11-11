"""Exercise the legacy LLM adapter through deterministic provider stubs."""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

from huey.memory.PY.llm import LLMAdapter, LLMProvider


def _install_module(monkeypatch, name: str, **attributes):
    module = types.ModuleType(name)
    for key, value in attributes.items():
        setattr(module, key, value)
    monkeypatch.setitem(sys.modules, name, module)
    return module


def test_adapter_rejects_unknown_provider_and_summarizes_offline_request():
    with pytest.raises(ValueError):
        LLMAdapter("unknown", model="test")

    adapter = LLMAdapter(LLMProvider.OLLAMA, model="test")
    result = adapter._fallback_response(
        "", [{"role": "user", "content": "hello\nworld"}]
    )
    assert result == "[ollama offline] Summary of request: hello world"

    result = adapter._fallback_response(
        "", [{"role": "user", "content": "request"}], error=RuntimeError("offline")
    )
    assert "Unable to reach provider because offline" in result


def test_openai_adapter_uses_api_key_and_passes_chat_parameters(monkeypatch):
    calls = []

    class Client:
        def __init__(self, **kwargs):
            calls.append(("init", kwargs))
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: calls.append(("create", kwargs))
                    or SimpleNamespace(
                        choices=[SimpleNamespace(message={"content": "answer"})]
                    )
                )
            )

    _install_module(monkeypatch, "openai", OpenAI=Client)
    adapter = LLMAdapter("openai", model="small", settings={"api_key": "secret"})
    messages = [{"role": "user", "content": "hello"}]
    assert adapter.generate("ignored", messages=messages, temperature=0.25) == "answer"
    assert calls == [
        ("init", {"api_key": "secret"}),
        (
            "create",
            {"model": "small", "messages": messages, "temperature": 0.25},
        ),
    ]
    assert adapter._ensure_client() is adapter._client


def test_openai_adapter_falls_back_on_provider_error(monkeypatch):
    class Client:
        def __init__(self, **_kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **_kwargs: (_ for _ in ()).throw(
                        ConnectionError("service down")
                    )
                )
            )

    _install_module(monkeypatch, "openai", OpenAI=Client)
    adapter = LLMAdapter("openai", model="small")
    assert "Summary of request: question" in adapter.generate("question")
    assert "service down" in adapter.generate("question")


def test_anthropic_adapter_handles_content_empty_content_and_api_failure(monkeypatch):
    class Client:
        def __init__(self, *, api_key=None):
            self.api_key = api_key
            self.messages = SimpleNamespace(create=self._create)

        @staticmethod
        def _create(**_kwargs):
            return SimpleNamespace(content=[SimpleNamespace(text="anthropic answer")])

    _install_module(monkeypatch, "anthropic", Anthropic=Client)
    adapter = LLMAdapter("anthropic", model="claude", settings={"api_key": "key"})
    assert adapter.generate("question") == "anthropic answer"

    adapter._client = SimpleNamespace(
        messages=SimpleNamespace(create=lambda **_kwargs: SimpleNamespace(content=[]))
    )
    assert adapter.generate("question") == "namespace(content=[])"

    adapter._client.messages.create = lambda **_kwargs: (_ for _ in ()).throw(
        ConnectionError("unavailable")
    )
    assert "unavailable" in adapter.generate("question")


def test_ollama_adapter_accepts_dict_and_non_dict_responses(monkeypatch):
    ollama = SimpleNamespace(
        chat=lambda **_kwargs: {"message": {"content": "ollama answer"}}
    )
    _install_module(monkeypatch, "ollama", chat=ollama.chat)
    adapter = LLMAdapter("ollama", model="local")
    assert adapter.generate("question") == "ollama answer"

    adapter._client = SimpleNamespace(chat=lambda **_kwargs: "raw response")
    assert adapter.generate("question") == "raw response"

    adapter._client = SimpleNamespace(chat=lambda **_kwargs: {"unexpected": True})
    assert adapter.generate("question") == "{'unexpected': True}"


def test_adapter_offline_fallback_when_optional_provider_package_is_missing(
    monkeypatch,
):
    real_import = __import__

    def without_ollama(name, *args, **kwargs):
        if name == "ollama":
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", without_ollama)
    adapter = LLMAdapter("ollama", model="local")
    assert adapter.generate("offline prompt").endswith(
        "Summary of request: offline prompt"
    )
