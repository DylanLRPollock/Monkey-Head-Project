"""Generate preview asset manifests for waveforms and spectrograms."""

from __future__ import annotations

from pathlib import Path

from huey.media.media_manager import FFmpegManager
from huey.media.media_manifest import MediaArtifact, MediaManifest


def generate_waveform_manifest(
    source: str | Path,
    output_dir: str | Path,
    *,
    manager: FFmpegManager | None = None,
    overwrite: bool = False,
) -> MediaManifest:
    """Generate waveform and spectrogram images plus a manifest."""

    media_manager = manager or FFmpegManager()
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"Media source not found: {source_path}")

    target_dir = Path(output_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    waveform_path = target_dir / f"{source_path.stem}.waveform.png"
    spectrogram_path = target_dir / f"{source_path.stem}.spectrogram.png"
    manifest_path = target_dir / f"{source_path.stem}.preview.manifest.json"

    probe = media_manager.probe(source_path)
    waveform_result = media_manager.waveform(
        source_path, waveform_path, overwrite=overwrite
    )
    spectrogram_result = media_manager.spectrogram(
        source_path, spectrogram_path, overwrite=overwrite
    )

    manifest = MediaManifest(
        source_path=str(source_path),
        operation="generate_waveform_manifest",
        probe=probe,
        artifacts=[
            MediaArtifact(kind="image", path=str(waveform_path), role="waveform"),
            MediaArtifact(kind="image", path=str(spectrogram_path), role="spectrogram"),
        ],
        commands=[waveform_result.command, spectrogram_result.command],
        metadata={"preserves_source": True},
    )
    manifest.write_json(manifest_path, overwrite=overwrite)
    return manifest


__all__ = ["generate_waveform_manifest"]
