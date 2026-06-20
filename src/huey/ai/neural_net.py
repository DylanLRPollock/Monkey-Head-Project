"""Small neural-network inspired utilities without external dependencies."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import tanh


@dataclass(slots=True)
class NeuralLayer:
    weights: list[float]
    bias: float = 0.0

    def activate(self, inputs: list[float]) -> float:
        paired = zip(self.weights, inputs, strict=False)
        signal = sum(weight * value for weight, value in paired) + self.bias
        return tanh(signal)


@dataclass(slots=True)
class SimpleNeuralNetwork:
    layers: list[NeuralLayer] = field(default_factory=list)

    def forward(self, inputs: list[float]) -> list[float]:
        activations = list(inputs)
        outputs: list[float] = []
        for layer in self.layers:
            output = layer.activate(activations)
            outputs.append(output)
            activations = [output for _ in activations] or [output]
        return outputs


__all__ = ["NeuralLayer", "SimpleNeuralNetwork"]
