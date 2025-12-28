# Image fine-tuning workflow for Monkey Head

This guide walks through preparing an image dataset, fine-tuning a pretrained model, and exporting the resulting assets so they can be consumed by the Monkey Head system.

## 1. Prepare the dataset

Organise images into a `train/` and `val/` (or `validation/`) split, with one subfolder per class:

```
my-dataset/
  train/
    class_a/
      img001.jpg
      img002.jpg
    class_b/
      ...
  val/
    class_a/
    class_b/
```

Recommendations:

- Use the same class folder names across train and val splits.
- Keep classes balanced where possible to avoid skewed accuracy.
- Resize or crop very large inputs to avoid running out of memory.

## 2. Launch training

The CLI wraps the training pipeline exposed at `monkey_head.training`:

```bash
python tools/train_image_model.py \
    --data-dir /path/to/my-dataset \
    --output-dir /models/monkey-head/experiments/resnet18 \
    --model-name resnet18 \
    --epochs 10 \
    --batch-size 32
```

Key flags:

- `--model-name` — choose from `resnet18` or `mobilenet_v3_small` (both load ImageNet weights).
- `--freeze-backbone` — update only the classifier head; useful when the dataset is small.
- `--device` — default is auto-detection; override with `cpu` for environments without CUDA.
- `--patience` — early stopping once validation accuracy stops improving.

## 3. What the training loop does

- Loads pretrained weights and swaps the classifier layer to match your class count.
- Applies standard data augmentation (random resize, flip, colour jitter) and normalization.
- Optimises with SGD + momentum and a step LR scheduler; loss is cross-entropy.
- Tracks train/val loss and accuracy each epoch and keeps the best-performing weights.

The underlying code lives in `src/monkey_head/training/pipeline.py` if you need to adjust architectures or schedulers.

## 4. Outputs and integration

The script writes a complete set of artifacts to the chosen `--output-dir`:

- `model_state.pt` — best-performing state dict for continued training or debugging.
- `model_scripted.pt` — TorchScript export for low-overhead inference.
- `model.onnx` — ONNX graph for deployment to runtimes that support ONNX.
- `model_metadata.json` — training configuration, class names, and headline metrics.
- `training_history.json` — per-epoch loss/accuracy and learning-rate trajectory.

After export, the pipeline appends an entry to `huey/models/registry.json` so the Monkey Head stack can discover the new model alongside its metadata.

## 5. Next steps

- Run a quick smoke test by loading `model_scripted.pt` in a minimal inference script before deploying to production robots.
- Track dataset provenance and class definitions in `model_metadata.json` for reproducibility.
- If you change the backbone or introduce a new architecture, update `WEIGHTS_REGISTRY` in `pipeline.py` so the CLI can expose it.
