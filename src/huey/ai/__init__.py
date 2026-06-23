"""AI and learning helpers for the HueyOS scaffold."""

from __future__ import annotations

from .attention import rank_candidates, score_attention
from .brain import HueyBrain
from .embeddings import embed_text
from .inference import InferenceEngine, InferenceRequest
from .learning import LearningEngine, LearningExample
from .model_registry import ModelRecord, ModelRegistry
from .neural_net import NeuralLayer, SimpleNeuralNetwork
from .tokenizer import BasicTokenizer
from .training import TrainingPipeline
from .transformers import TransformerBlock

__all__ = [
    "BasicTokenizer",
    "HueyBrain",
    "InferenceEngine",
    "InferenceRequest",
    "LearningEngine",
    "LearningExample",
    "ModelRecord",
    "ModelRegistry",
    "NeuralLayer",
    "SimpleNeuralNetwork",
    "TrainingPipeline",
    "TransformerBlock",
    "embed_text",
    "rank_candidates",
    "score_attention",
]
