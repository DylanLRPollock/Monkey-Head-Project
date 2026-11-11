"""Tests for the dependency-free AI scaffold helpers."""

from __future__ import annotations

import pytest

from huey.ai.attention import rank_candidates, score_attention
from huey.ai.embeddings import embed_media_id, embed_text
from huey.ai.model_registry import ModelRegistry
from huey.ai.tokenizer import BasicTokenizer


def test_tokenizer_handles_punctuation_empty_input_and_counts():
    tokenizer = BasicTokenizer()
    assert tokenizer.tokenize("Hi, Huey's v2!") == ["hi", "huey's", "v2"]
    assert tokenizer.detokenize([" hi ", "", "there "]) == "hi there"
    assert tokenizer.token_counts("A a, B") == {"a": 2, "b": 1}
    assert tokenizer.tokenize("") == []


def test_deterministic_embeddings_normalize_and_pad_dimensions():
    first = embed_text("Hello, WORLD!")
    assert first == embed_text("hello world")
    assert len(first) == 12
    assert embed_text("hello", dimensions=0) == []
    padded = embed_text("hello", dimensions=40)
    assert len(padded) == 40
    assert padded[-8:] == [0.0] * 8
    assert embed_media_id("frame-1", kind="image") == embed_text(
        "image:frame-1", dimensions=8
    )
    assert embed_media_id("frame-1", kind="video") != embed_media_id(
        "frame-1", kind="image"
    )


def test_attention_scoring_handles_unequal_and_empty_vectors():
    assert score_attention([1.0, 2.0, 100.0], [2.0, 3.0]) == 2.666667
    assert score_attention([], []) == 0.0
    ranked = rank_candidates(
        [1.0, 0.0], {"low": [0.0, 1.0], "high": [1.0, 0.0], "tie": [1.0, 0.0]}
    )
    assert ranked == [("high", 0.5), ("tie", 0.5), ("low", 0.0)]


def test_model_registry_defaults_overrides_catalog_and_unknown_names():
    registry = ModelRegistry()
    with pytest.raises(KeyError, match="No models have been registered"):
        registry.resolve()
    metadata = {"family": "test"}
    registry.register("first", metadata=metadata)
    metadata["family"] = "changed"
    registry.register("second", version="2.0", default=True)
    assert registry.resolve().name == "second"
    assert registry.resolve("first").metadata == {"family": "test"}
    assert [item["name"] for item in registry.catalog()] == ["first", "second"]
    with pytest.raises(KeyError):
        registry.resolve("missing")
