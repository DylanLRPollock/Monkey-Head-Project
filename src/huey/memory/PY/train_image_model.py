"""CLI entrypoint for fine-tuning image classifiers for Monkey Head.

Usage example::

    python tools/train_image_model.py \
        --data-dir /data/monkey-images \
        --output-dir /models/monkey-head/experiments/resnet18 \
        --model-name resnet18 \
        --epochs 10
"""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from monkey_head.training import TrainingConfig, run_training


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune a pretrained image model for Monkey Head")
    parser.add_argument("--data-dir", type=Path, required=True, help="Folder containing train/ and val/ splits")
    parser.add_argument("--output-dir", type=Path, required=True, help="Where to write model artifacts")
    parser.add_argument("--model-name", default="resnet18", choices=["resnet18", "mobilenet_v3_small"], help="Backbone to fine-tune")
    parser.add_argument("--batch-size", type=int, default=32, help="Mini-batch size")
    parser.add_argument("--num-workers", type=int, default=2, help="Data loader worker processes")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=1e-3, help="Optimizer learning rate")
    parser.add_argument("--weight-decay", type=float, default=1e-4, help="L2 weight decay")
    parser.add_argument("--momentum", type=float, default=0.9, help="SGD momentum")
    parser.add_argument("--image-size", type=int, default=224, help="Input resolution for the model")
    parser.add_argument("--patience", type=int, default=2, help="Early stopping patience on validation accuracy")
    parser.add_argument("--freeze-backbone", action="store_true", help="Freeze convolutional backbone layers")
    parser.add_argument("--device", choices=["cpu", "cuda"], default=None, help="Force device selection")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    config = TrainingConfig(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        model_name=args.model_name,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        num_epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=args.weight_decay,
        momentum=args.momentum,
        image_size=args.image_size,
        patience=args.patience,
        freeze_backbone=args.freeze_backbone,
        device=device,
    )

    artifacts, summary = run_training(config)
    print("Training complete")
    print(f"Best validation accuracy: {summary.best_val_accuracy:.4f}")
    for name, path in artifacts.items():
        print(f"Saved {name}: {path}")


if __name__ == "__main__":
    main()
