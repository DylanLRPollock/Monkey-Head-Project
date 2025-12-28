from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


WEIGHTS_REGISTRY = {
    "resnet18": models.ResNet18_Weights.DEFAULT,
    "mobilenet_v3_small": models.MobileNet_V3_Small_Weights.DEFAULT,
}


@dataclass
class TrainingConfig:
    data_dir: Path
    output_dir: Path
    model_name: str = "resnet18"
    batch_size: int = 32
    num_workers: int = 2
    num_epochs: int = 5
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    momentum: float = 0.9
    image_size: int = 224
    patience: int = 2
    freeze_backbone: bool = False
    device: str = field(default_factory=lambda: "cuda" if torch.cuda.is_available() else "cpu")


@dataclass
class TrainingSummary:
    best_epoch: int
    best_val_accuracy: float
    history: List[Dict[str, float]]


def build_transforms(image_size: int) -> Dict[str, transforms.Compose]:
    """Create training and validation transforms for image classification."""

    return {
        "train": transforms.Compose(
            [
                transforms.RandomResizedCrop(image_size),
                transforms.RandomHorizontalFlip(),
                transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        ),
        "val": transforms.Compose(
            [
                transforms.Resize(int(image_size * 1.15)),
                transforms.CenterCrop(image_size),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        ),
    }


def prepare_dataloaders(config: TrainingConfig) -> Tuple[Dict[str, DataLoader], List[str]]:
    """Create :class:`DataLoader` objects from a train/val folder structure."""

    transforms_map = build_transforms(config.image_size)
    train_dir = config.data_dir / "train"
    if not train_dir.exists():
        raise FileNotFoundError("Training data not found: expected a 'train' folder")
    val_dir_candidates = [config.data_dir / "val", config.data_dir / "validation"]
    val_dir = next((candidate for candidate in val_dir_candidates if candidate.exists()), None)
    if val_dir is None:
        raise FileNotFoundError("Validation data not found: expected a 'val' or 'validation' folder")

    datasets_map = {
        "train": datasets.ImageFolder(train_dir, transform=transforms_map["train"]),
        "val": datasets.ImageFolder(val_dir, transform=transforms_map["val"]),
    }
    class_names = datasets_map["train"].classes

    dataloaders = {
        split: DataLoader(
            ds,
            batch_size=config.batch_size,
            shuffle=split == "train",
            num_workers=config.num_workers,
            pin_memory=torch.cuda.is_available(),
        )
        for split, ds in datasets_map.items()
    }

    return dataloaders, class_names


def _replace_classifier(model: nn.Module, num_classes: int, model_name: str) -> nn.Module:
    if model_name == "resnet18":
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
    elif model_name == "mobilenet_v3_small":
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
    else:
        raise ValueError(f"Unsupported model '{model_name}' for classifier replacement")

    return model


def initialise_model(model_name: str, num_classes: int, freeze_backbone: bool) -> nn.Module:
    if model_name not in WEIGHTS_REGISTRY:
        raise ValueError(f"Model '{model_name}' is not available. Choose from: {', '.join(WEIGHTS_REGISTRY)}")

    weights = WEIGHTS_REGISTRY[model_name]
    model_builder = models.__dict__[model_name]
    model = model_builder(weights=weights)

    if freeze_backbone:
        for param in model.parameters():
            param.requires_grad = False

    model = _replace_classifier(model, num_classes, model_name)
    return model


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> Dict[str, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        predictions = outputs.argmax(dim=1)
        correct += (predictions == labels).sum().item()
        total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return {"loss": epoch_loss, "accuracy": epoch_acc}


def evaluate(model: nn.Module, dataloader: DataLoader, criterion: nn.Module, device: torch.device) -> Dict[str, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * inputs.size(0)
            predictions = outputs.argmax(dim=1)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)

    epoch_loss = running_loss / total
    epoch_acc = correct / total
    return {"loss": epoch_loss, "accuracy": epoch_acc}


def train_model(
    model: nn.Module,
    dataloaders: Dict[str, DataLoader],
    config: TrainingConfig,
) -> Tuple[nn.Module, TrainingSummary]:
    device = torch.device(config.device)
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=config.learning_rate,
        momentum=config.momentum,
        weight_decay=config.weight_decay,
    )
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)

    best_accuracy = 0.0
    best_state = None
    best_epoch = 0
    history: List[Dict[str, float]] = []
    epochs_without_improvement = 0

    for epoch in range(1, config.num_epochs + 1):
        train_metrics = train_one_epoch(model, dataloaders["train"], criterion, optimizer, device)
        val_metrics = evaluate(model, dataloaders["val"], criterion, device)
        scheduler.step()

        history.append(
            {
                "epoch": int(epoch),
                "train_loss": float(train_metrics["loss"]),
                "train_accuracy": float(train_metrics["accuracy"]),
                "val_loss": float(val_metrics["loss"]),
                "val_accuracy": float(val_metrics["accuracy"]),
                "learning_rate": float(scheduler.get_last_lr()[0]),
            }
        )

        if val_metrics["accuracy"] > best_accuracy:
            best_accuracy = val_metrics["accuracy"]
            best_state = model.state_dict()
            best_epoch = epoch
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1

        if epochs_without_improvement >= config.patience:
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    summary = TrainingSummary(
        best_epoch=int(best_epoch or history[-1]["epoch"]),
        best_val_accuracy=float(best_accuracy),
        history=history,
    )
    return model, summary


def export_artifacts(
    model: nn.Module,
    class_names: List[str],
    config: TrainingConfig,
    summary: TrainingSummary,
) -> Dict[str, Path]:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    device = torch.device(config.device)
    model.to(device)
    model.eval()

    artifacts: Dict[str, Path] = {}

    weights_path = config.output_dir / "model_state.pt"
    torch.save(model.state_dict(), weights_path)
    artifacts["state_dict"] = weights_path

    metadata = {
        "model_name": config.model_name,
        "class_names": class_names,
        "config": {
            "batch_size": config.batch_size,
            "num_epochs": config.num_epochs,
            "learning_rate": config.learning_rate,
            "weight_decay": config.weight_decay,
            "momentum": config.momentum,
            "image_size": config.image_size,
            "freeze_backbone": config.freeze_backbone,
        },
        "summary": {
            "best_epoch": summary.best_epoch,
            "best_val_accuracy": summary.best_val_accuracy,
        },
    }
    metadata_path = config.output_dir / "model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    artifacts["metadata"] = metadata_path

    scripted_path = config.output_dir / "model_scripted.pt"
    example_input = torch.randn(1, 3, config.image_size, config.image_size, device=device)
    scripted_model = torch.jit.trace(model, example_input)
    scripted_model.save(scripted_path)
    artifacts["torchscript"] = scripted_path

    onnx_path = config.output_dir / "model.onnx"
    torch.onnx.export(
        model,
        example_input,
        onnx_path,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    artifacts["onnx"] = onnx_path

    summary_path = config.output_dir / "training_history.json"
    summary_path.write_text(json.dumps([row for row in summary.history], indent=2))
    artifacts["history"] = summary_path

    return artifacts


def integrate_model(
    artifacts: Dict[str, Path],
    class_names: Iterable[str],
    summary: TrainingSummary,
    registry_dir: Path | None = None,
) -> Path:
    registry_dir = registry_dir or Path("huey/models")
    registry_dir.mkdir(parents=True, exist_ok=True)
    registry_path = registry_dir / "registry.json"

    registry: List[Dict[str, object]] = []
    if registry_path.exists():
        registry = json.loads(registry_path.read_text())

    record = {
        "state_dict": str(artifacts.get("state_dict")),
        "torchscript": str(artifacts.get("torchscript")),
        "onnx": str(artifacts.get("onnx")),
        "metadata": str(artifacts.get("metadata")),
        "history": str(artifacts.get("history")),
        "classes": list(class_names),
        "best_val_accuracy": summary.best_val_accuracy,
    }
    registry.append(record)
    registry_path.write_text(json.dumps(registry, indent=2))
    return registry_path


def run_training(config: TrainingConfig) -> Tuple[Dict[str, Path], TrainingSummary]:
    dataloaders, class_names = prepare_dataloaders(config)
    model = initialise_model(config.model_name, num_classes=len(class_names), freeze_backbone=config.freeze_backbone)
    model, summary = train_model(model, dataloaders, config)
    artifacts = export_artifacts(model, class_names, config, summary)
    integrate_model(artifacts, class_names, summary)
    return artifacts, summary


__all__ = [
    "TrainingConfig",
    "TrainingSummary",
    "build_transforms",
    "prepare_dataloaders",
    "initialise_model",
    "train_one_epoch",
    "evaluate",
    "train_model",
    "export_artifacts",
    "integrate_model",
    "run_training",
]
