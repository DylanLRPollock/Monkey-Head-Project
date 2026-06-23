"""Video probing and preview helpers for HueyOS media fixtures."""

from __future__ import annotations

from pathlib import Path

from huey.media.media_manager import FFmpegManager
from huey.media.media_manifest import MediaArtifact, MediaManifest


def build_video_preview(
    source: str | Path,
    output_dir: str | Path,
    *,
    manager: FFmpegManager | None = None,
    overwrite: bool = False,
) -> MediaManifest:
    """Probe a video and generate a thumbnail plus transcription-ready audio."""
    media_manager = manager or FFmpegManager()
    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(f"Video source not found: {source_path}")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_path = target_dir / f"{source_path.stem}.thumbnail.jpg"
    audio_path = target_dir / f"{source_path.stem}.audio.wav"
    manifest_path = target_dir / f"{source_path.stem}.video.manifest.json"

    probe = media_manager.probe(source_path)
    thumbnail_result = media_manager.thumbnail(
        source_path, thumbnail_path, overwrite=overwrite
    )
    audio_result = media_manager.extract_audio(
        source_path, audio_path, overwrite=overwrite
    )

    manifest = MediaManifest(
        source_path=str(source_path),
        operation="build_video_preview",
        probe=probe,
        artifacts=[
            MediaArtifact(kind="image", path=str(thumbnail_path), role="thumbnail"),
            MediaArtifact(
                kind="audio", path=str(audio_path), role="extracted_transcription_audio"
            ),
        ],
        commands=[thumbnail_result.command, audio_result.command],
        metadata={"preserves_source": True},
    )
    manifest.write_json(manifest_path, overwrite=overwrite)
    return manifest


def extract_video_frame(
    source: str | Path,
    output: str | Path,
    *,
    frame_number: int,
    manager: FFmpegManager | None = None,
    overwrite: bool = False,
) -> Path:
    """Extract one frame from ``source`` and return the output path."""
    media_manager = manager or FFmpegManager()
    media_manager.extract_frame(
        source, output, frame_number=frame_number, overwrite=overwrite
    )
    return Path(output)
