"""Exercise the training pipeline without installing optional ML dependencies."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from contextlib import nullcontext
from pathlib import Path

import pytest


class _Scalar:
    def __init__(self, value=1.0):
        self.value = value

    def item(self):
        return self.value

    def backward(self):
        return None

    def sum(self):
        return self


class _Labels:
    def __init__(self, values):
        self.values = list(values)

    def to(self, _device):
        return self

    def size(self, dimension):
        assert dimension == 0
        return len(self.values)

    def __eq__(self, other):
        return _Scalar(
            sum(
                left == right
                for left, right in zip(self.values, other.values, strict=True)
            )
        )


class _Inputs:
    def __init__(self, count=2):
        self.count = count

    def to(self, _device):
        return self

    def size(self, dimension):
        assert dimension == 0
        return self.count


class _Model:
    def __init__(self):
        self.fc = types.SimpleNamespace(in_features=4)
        self.classifier = [None, None, None, types.SimpleNamespace(in_features=6)]
        self._parameters = [types.SimpleNamespace(requires_grad=True) for _ in range(2)]
        self.loaded = None
        self.mode = None

    def parameters(self):
        return iter(self._parameters)

    def train(self):
        self.mode = "train"

    def eval(self):
        self.mode = "eval"

    def to(self, _device):
        return self

    def __call__(self, inputs):
        return types.SimpleNamespace(argmax=lambda dim: _Labels([0] * inputs.count))

    def state_dict(self):
        return {"weights": "best"}

    def load_state_dict(self, state):
        self.loaded = state


class _DataLoader:
    def __init__(self, dataset, **kwargs):
        self.dataset = dataset
        self.options = kwargs


def _external_modules():
    nn = types.ModuleType("torch.nn")
    nn.Module = _Model
    nn.Linear = lambda inputs, outputs: types.SimpleNamespace(
        in_features=inputs, out_features=outputs
    )
    nn.CrossEntropyLoss = lambda: lambda _outputs, _labels: _Scalar(0.5)

    optim = types.ModuleType("torch.optim")

    class Optimizer:
        def __init__(self, *_args, **kwargs):
            self.options = kwargs
            self.zeroed = 0
            self.stepped = 0

        def zero_grad(self):
            self.zeroed += 1

        def step(self):
            self.stepped += 1

    optim.SGD = Optimizer
    optim.lr_scheduler = types.SimpleNamespace(
        StepLR=lambda _optimizer, **_kwargs: types.SimpleNamespace(
            step=lambda: None, get_last_lr=lambda: [0.001]
        )
    )

    torch = types.ModuleType("torch")
    torch.nn = nn
    torch.optim = optim
    torch.cuda = types.SimpleNamespace(is_available=lambda: False)
    torch.device = lambda name: name
    torch.no_grad = nullcontext
    torch.randn = lambda *args, **kwargs: (args, kwargs)
    torch.save = lambda _value, path: Path(path).write_bytes(b"weights")
    torch.jit = types.SimpleNamespace(
        trace=lambda _model, _example: types.SimpleNamespace(
            save=lambda path: Path(path).write_bytes(b"script")
        )
    )
    torch.onnx = types.SimpleNamespace(
        export=lambda _model, _example, path, **_kwargs: Path(path).write_bytes(b"onnx")
    )

    data = types.ModuleType("torch.utils.data")
    data.DataLoader = _DataLoader
    utils = types.ModuleType("torch.utils")
    utils.data = data

    datasets = types.ModuleType("torchvision.datasets")

    class ImageFolder:
        def __init__(self, root, transform):
            self.root = Path(root)
            self.transform = transform
            self.classes = ["cat", "dog"]

    datasets.ImageFolder = ImageFolder

    models = types.ModuleType("torchvision.models")
    models.ResNet18_Weights = types.SimpleNamespace(DEFAULT="resnet-weights")
    models.MobileNet_V3_Small_Weights = types.SimpleNamespace(DEFAULT="mobile-weights")
    models.__dict__["resnet18"] = lambda **_kwargs: _Model()
    models.__dict__["mobilenet_v3_small"] = lambda **_kwargs: _Model()

    transforms = types.ModuleType("torchvision.transforms")

    class Transform:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    transforms.Compose = lambda items: items
    for name in (
        "RandomResizedCrop",
        "RandomHorizontalFlip",
        "ColorJitter",
        "ToTensor",
        "Normalize",
        "Resize",
        "CenterCrop",
    ):
        setattr(transforms, name, Transform)

    torchvision = types.ModuleType("torchvision")
    torchvision.datasets = datasets
    torchvision.models = models
    torchvision.transforms = transforms

    return {
        "torch": torch,
        "torch.nn": nn,
        "torch.optim": optim,
        "torch.utils": utils,
        "torch.utils.data": data,
        "torchvision": torchvision,
        "torchvision.datasets": datasets,
        "torchvision.models": models,
        "torchvision.transforms": transforms,
    }


@pytest.fixture
def pipeline(monkeypatch):
    for name, module in _external_modules().items():
        monkeypatch.setitem(sys.modules, name, module)

    path = Path(__file__).parents[1] / "src" / "huey" / "training" / "pipeline.py"
    spec = importlib.util.spec_from_file_location("huey.training.pipeline", path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


def test_config_defaults_transforms_and_data_folder_validation(pipeline, tmp_path):
    config = pipeline.TrainingConfig(tmp_path, tmp_path / "out")
    assert config.device == "cpu"
    assert config.model_name == "resnet18"
    transforms = pipeline.build_transforms(64)
    assert set(transforms) == {"train", "val"}
    assert len(transforms["train"]) == 5
    assert len(transforms["val"]) == 4

    with pytest.raises(FileNotFoundError, match="train"):
        pipeline.prepare_dataloaders(config)

    (tmp_path / "train").mkdir()
    with pytest.raises(FileNotFoundError, match="val"):
        pipeline.prepare_dataloaders(config)


def test_data_loaders_choose_validation_alias_and_options(
    pipeline, tmp_path, monkeypatch
):
    (tmp_path / "train").mkdir()
    (tmp_path / "validation").mkdir()
    monkeypatch.setattr(pipeline.torch.cuda, "is_available", lambda: True)
    config = pipeline.TrainingConfig(
        tmp_path, tmp_path / "out", batch_size=3, num_workers=0, image_size=48
    )

    loaders, classes = pipeline.prepare_dataloaders(config)

    assert classes == ["cat", "dog"]
    assert loaders["train"].options == {
        "batch_size": 3,
        "shuffle": True,
        "num_workers": 0,
        "pin_memory": True,
    }
    assert loaders["val"].dataset.root == tmp_path / "validation"
    assert loaders["val"].options["shuffle"] is False


@pytest.mark.parametrize("model_name", ["resnet18", "mobilenet_v3_small"])
def test_model_initialization_replaces_classifier_and_freezes_backbone(
    pipeline, model_name
):
    model = pipeline.initialise_model(model_name, num_classes=5, freeze_backbone=True)
    assert all(parameter.requires_grad is False for parameter in model.parameters())
    classifier = model.fc if model_name == "resnet18" else model.classifier[3]
    assert classifier.in_features in {4, 6}
    assert classifier.out_features == 5


def test_model_rejects_unknown_names_and_classifier_targets(pipeline):
    with pytest.raises(ValueError, match="not available"):
        pipeline.initialise_model("unknown", 2, False)
    with pytest.raises(ValueError, match="Unsupported model"):
        pipeline._replace_classifier(_Model(), 2, "unknown")


def test_model_initialization_leaves_backbone_trainable_when_not_frozen(pipeline):
    model = pipeline.initialise_model("resnet18", num_classes=3, freeze_backbone=False)
    assert all(parameter.requires_grad is True for parameter in model.parameters())


def test_train_and_evaluate_compute_metrics_and_set_model_modes(pipeline):
    model = _Model()

    def criterion(_outputs, _labels):
        return _Scalar(0.5)

    batch = (_Inputs(2), _Labels([0, 0]))

    trained = pipeline.train_one_epoch(
        model,
        [batch],
        criterion,
        _external_modules()["torch.optim"].SGD([], lr=0.1),
        "cpu",
    )
    assert trained == {"loss": 0.5, "accuracy": 1.0}
    assert model.mode == "train"

    evaluated = pipeline.evaluate(model, [batch], criterion, "cpu")
    assert evaluated == {"loss": 0.5, "accuracy": 1.0}
    assert model.mode == "eval"


def test_train_model_tracks_best_state_and_stops_after_patience(pipeline, monkeypatch):
    model = _Model()
    metrics = iter(
        [
            ({"loss": 1.0, "accuracy": 0.5}, {"loss": 0.7, "accuracy": 0.7}),
            ({"loss": 0.8, "accuracy": 0.6}, {"loss": 0.8, "accuracy": 0.6}),
            ({"loss": 0.7, "accuracy": 0.7}, {"loss": 0.9, "accuracy": 0.6}),
        ]
    )
    monkeypatch.setattr(pipeline, "train_one_epoch", lambda *_args: next(metrics)[0])
    validation = iter([{"loss": 0.7, "accuracy": 0.7}, {"loss": 0.8, "accuracy": 0.6}])
    monkeypatch.setattr(pipeline, "evaluate", lambda *_args: next(validation))
    config = pipeline.TrainingConfig(
        Path("."), Path("."), num_epochs=5, patience=1, device="cpu"
    )

    restored, summary = pipeline.train_model(model, {"train": [], "val": []}, config)

    assert restored.loaded == {"weights": "best"}
    assert summary.best_epoch == 1
    assert summary.best_val_accuracy == 0.7
    assert [item["epoch"] for item in summary.history] == [1, 2]
    assert summary.history[0]["learning_rate"] == 0.001


def test_train_model_without_accuracy_improvement_uses_last_epoch(
    pipeline, monkeypatch
):
    model = _Model()
    monkeypatch.setattr(
        pipeline,
        "train_one_epoch",
        lambda *_args: {"loss": 1.0, "accuracy": 0.2},
    )
    monkeypatch.setattr(
        pipeline,
        "evaluate",
        lambda *_args: {"loss": 1.1, "accuracy": 0.0},
    )
    config = pipeline.TrainingConfig(
        Path("."), Path("."), num_epochs=2, patience=3, device="cpu"
    )

    _model, summary = pipeline.train_model(model, {"train": [], "val": []}, config)

    assert summary.best_epoch == 2
    assert summary.best_val_accuracy == 0.0
    assert model.loaded is None


def test_export_and_integration_persist_artifacts_and_append_registry(
    pipeline, tmp_path
):
    model = _Model()
    config = pipeline.TrainingConfig(
        tmp_path / "data",
        tmp_path / "out",
        model_name="mobilenet_v3_small",
        batch_size=4,
        num_epochs=3,
        image_size=32,
        device="cpu",
        freeze_backbone=True,
    )
    summary = pipeline.TrainingSummary(2, 0.875, [{"epoch": 1.0}])
    artifacts = pipeline.export_artifacts(model, ["cat", "dog"], config, summary)

    assert set(artifacts) == {
        "state_dict",
        "metadata",
        "torchscript",
        "onnx",
        "history",
    }
    metadata = json.loads(artifacts["metadata"].read_text())
    assert metadata["config"]["batch_size"] == 4
    assert metadata["summary"]["best_epoch"] == 2
    assert json.loads(artifacts["history"].read_text()) == [{"epoch": 1.0}]

    registry = pipeline.integrate_model(
        artifacts, ["cat", "dog"], summary, tmp_path / "models"
    )
    assert len(json.loads(registry.read_text())) == 1
    pipeline.integrate_model(artifacts, ["bird"], summary, tmp_path / "models")
    records = json.loads(registry.read_text())
    assert len(records) == 2
    assert records[-1]["classes"] == ["bird"]


def test_run_training_wires_pipeline_stages(pipeline, monkeypatch, tmp_path):
    config = pipeline.TrainingConfig(tmp_path, tmp_path / "out")
    model = _Model()
    summary = pipeline.TrainingSummary(1, 1.0, [])
    artifacts = {"state_dict": tmp_path / "state.pt"}
    seen = []
    monkeypatch.setattr(
        pipeline,
        "prepare_dataloaders",
        lambda _config: ({"train": [], "val": []}, ["x"]),
    )
    monkeypatch.setattr(
        pipeline,
        "initialise_model",
        lambda *args, **kwargs: seen.append(("init", args, kwargs)) or model,
    )
    monkeypatch.setattr(pipeline, "train_model", lambda *args: (model, summary))
    monkeypatch.setattr(pipeline, "export_artifacts", lambda *args: artifacts)
    monkeypatch.setattr(
        pipeline, "integrate_model", lambda *args: seen.append(("integrate", args))
    )

    result_artifacts, result_summary = pipeline.run_training(config)

    assert result_artifacts is artifacts
    assert result_summary is summary
    assert seen[0][0] == "init"
    assert seen[0][2] == {"num_classes": 1, "freeze_backbone": False}
    assert seen[1][0] == "integrate"
