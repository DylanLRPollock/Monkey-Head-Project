"""Test PyTorch helper behavior without requiring the optional torch package."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def pytorch_tools(monkeypatch):
    numpy = ModuleType("numpy")
    numpy.random = SimpleNamespace(seed=lambda seed: None)
    torch = ModuleType("torch")
    torch.__version__ = "test-version"
    torch.device = lambda name: f"device:{name}"
    torch.cuda = SimpleNamespace(
        is_available=lambda: False,
        device_count=lambda: 0,
        get_device_name=lambda index: f"gpu-{index}",
        manual_seed_all=lambda seed: None,
    )
    torch.manual_seed = lambda seed: None
    torch.randn = lambda shape, device=None: (tuple(shape), device)
    torch.load = lambda path, **kwargs: {"state_dict": {"weights": path}}

    class Linear:
        def __init__(self, in_dim, out_dim):
            self.in_dim, self.out_dim = in_dim, out_dim

    class ReLU:
        pass

    class Dropout:
        def __init__(self, probability):
            self.probability = probability

    class Sequential:
        def __init__(self, *layers):
            self.layers = layers

    nn = SimpleNamespace(
        Module=object,
        Linear=Linear,
        ReLU=ReLU,
        Dropout=Dropout,
        Sequential=Sequential,
    )
    torch.nn = nn
    monkeypatch.setitem(sys.modules, "numpy", numpy)
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "torch.nn", nn)
    path = Path(__file__).parents[1] / "src" / "huey" / "pytorch_tools.py"
    spec = importlib.util.spec_from_file_location("huey.pytorch_tools_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module, torch


def test_device_summary_seeding_and_tensor_generation(pytorch_tools, monkeypatch):
    module, torch = pytorch_tools
    assert module.get_device() == "device:cpu"
    assert module.get_device(prefer_cuda=False) == "device:cpu"
    summary = module.device_summary()
    assert summary["torch_version"] == "test-version"
    assert summary["cuda_devices"] == ()
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 2)
    assert module.get_device() == "device:cuda"
    assert module.device_summary()["cuda_devices"] == ("gpu-0", "gpu-1")
    assert module.seed_everything(7) == {"seed": 7}
    assert module.sample_tensor([2, 3], device="cpu") == ((2, 3), "cpu")


def test_mlp_validation_and_layer_composition(pytorch_tools):
    module, _torch = pytorch_tools
    with pytest.raises(ValueError, match="input and output"):
        module.build_mlp([4])
    with pytest.raises(ValueError, match="non-negative"):
        module.build_mlp([4, 2], dropout=-0.1)
    model = module.build_mlp([4, 3, 2], dropout=0.25)
    assert [type(layer).__name__ for layer in model.layers] == [
        "Linear",
        "ReLU",
        "Dropout",
        "Linear",
    ]
    assert model.layers[0].in_dim == 4
    assert model.layers[-1].out_dim == 2
    no_dropout = module.build_mlp([2, 1], dropout=0)
    assert len(no_dropout.layers) == 1


def test_tensor_statistics_and_checkpoint_trust_gate(pytorch_tools):
    module, torch = pytorch_tools

    class Tensor:
        def mean(self):
            return SimpleNamespace(item=lambda: 2.0)

        def std(self, unbiased):
            assert unbiased is False
            return SimpleNamespace(item=lambda: 1.0)

        def min(self):
            return SimpleNamespace(item=lambda: 0.0)

        def max(self):
            return SimpleNamespace(item=lambda: 4.0)

    assert module.tensor_stats(Tensor()) == {
        "mean": 2.0,
        "std": 1.0,
        "min": 0.0,
        "max": 4.0,
    }

    class Model:
        def load_state_dict(self, state, strict):
            self.loaded = (state, strict)

    model = Model()
    with pytest.raises(PermissionError, match="untrusted source"):
        module.load_state_dict_checkpoint(model, "weights.pt")
    assert (
        module.load_state_dict_checkpoint(
            model, "weights.pt", trusted_source=True, strict=False
        )
        is model
    )
    assert model.loaded == ({"weights": "weights.pt"}, False)
    assert torch.load  # The trusted path reached the controlled loader.
