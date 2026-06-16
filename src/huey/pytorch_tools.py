"""Utility helpers for working with PyTorch in Monkey Head workflows."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Sequence, Tuple

import numpy as np
import torch
from torch import nn


@dataclass(frozen=True)
class TorchDeviceInfo:
    device: str
    torch_version: str
    cuda_available: bool
    cuda_device_count: int
    cuda_devices: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_device(prefer_cuda: bool = True) -> torch.device:
    """Return the best available torch device."""

    if prefer_cuda and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def device_summary(prefer_cuda: bool = True) -> Dict[str, Any]:
    """Summarize the current PyTorch runtime and device availability."""

    cuda_available = torch.cuda.is_available()
    cuda_device_count = torch.cuda.device_count() if cuda_available else 0
    cuda_devices = tuple(
        torch.cuda.get_device_name(index) for index in range(cuda_device_count)
    )
    info = TorchDeviceInfo(
        device=str(get_device(prefer_cuda)),
        torch_version=torch.__version__,
        cuda_available=cuda_available,
        cuda_device_count=cuda_device_count,
        cuda_devices=cuda_devices,
    )
    return info.to_dict()


def seed_everything(seed: int) -> Dict[str, int]:
    """Seed common RNGs for reproducible PyTorch experiments."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    return {"seed": int(seed)}


def build_mlp(layer_sizes: Sequence[int], dropout: float = 0.0) -> nn.Module:
    """Build a simple multi-layer perceptron for experimentation."""

    if len(layer_sizes) < 2:
        raise ValueError("layer_sizes must contain input and output dimensions")
    if dropout < 0.0:
        raise ValueError("dropout must be non-negative")

    layers: list[nn.Module] = []
    for index, (in_dim, out_dim) in enumerate(zip(layer_sizes, layer_sizes[1:])):
        layers.append(nn.Linear(in_dim, out_dim))
        if index < len(layer_sizes) - 2:
            layers.append(nn.ReLU())
            if dropout:
                layers.append(nn.Dropout(dropout))
    return nn.Sequential(*layers)


def tensor_stats(tensor: torch.Tensor) -> Dict[str, float]:
    """Return basic statistics for a tensor."""

    return {
        "mean": float(tensor.mean().item()),
        "std": float(tensor.std(unbiased=False).item()),
        "min": float(tensor.min().item()),
        "max": float(tensor.max().item()),
    }


def sample_tensor(
    shape: Iterable[int], device: torch.device | None = None
) -> torch.Tensor:
    """Create a random tensor for quick checks."""

    device = device or get_device()
    return torch.randn(tuple(shape), device=device)


def load_state_dict_checkpoint(
    model: nn.Module,
    checkpoint_path: str | Path,
    *,
    map_location: str | torch.device = "cpu",
    strict: bool = True,
    trusted_source: bool = False,
) -> nn.Module:
    """Load a state dict checkpoint into ``model`` with an explicit trust gate.

    PyTorch checkpoint loading is still pickle-based, including many
    ``weights_only=True`` flows. To reduce accidental RCE exposure, callers must
    explicitly mark the source as trusted before this helper will invoke
    :func:`torch.load`.
    """

    if not trusted_source:
        raise PermissionError(
            "Refusing to load checkpoint with torch.load from an untrusted source. "
            "Review the artifact, or prefer a non-pickle format (for example safetensors), "
            "then call with trusted_source=True."
        )

    state = torch.load(checkpoint_path, map_location=map_location, weights_only=True)
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]
    model.load_state_dict(state, strict=strict)
    return model


__all__ = [
    "TorchDeviceInfo",
    "get_device",
    "device_summary",
    "seed_everything",
    "build_mlp",
    "tensor_stats",
    "sample_tensor",
    "load_state_dict_checkpoint",
]
