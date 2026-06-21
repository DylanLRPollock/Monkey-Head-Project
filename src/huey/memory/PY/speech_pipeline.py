"""Prepare known audio fixtures into transcription-ready WAV files."""

from __future__ import annotations

from pathlib import Path

from huey.media.media_manager import FFmpegManager
from huey.media.media_manifest import MediaArtifact, MediaManifest

TRANSCRIPTION_SAMPLE_RATE = 16000


def prepare_audio_for_transcription(
    source: str | Path,
    output_dir: str | Path,
    *,
    manager: FFmpegManager | None = None,
    overwrite: bool = False,
) -> MediaManifest:
    """Prepare ``source`` as mono 16 kHz WAV and write an audit manifest."""
    media_manager = manager or FFmpegManager()
    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(f"Audio source not found: {source_path}")

    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    wav_path = target_dir / f"{source_path.stem}.transcription.wav"
    manifest_path = target_dir / f"{source_path.stem}.transcription.manifest.json"

    probe = media_manager.probe(source_path)
    result = media_manager.prepare_transcription_wav(source_path, wav_path, overwrite=overwrite)

    manifest = MediaManifest(
        source_path=str(source_path),
        operation="prepare_audio_for_transcription",
        probe=probe,
        artifacts=[
            MediaArtifact(
                kind="audio",
                path=str(wav_path),
                role="transcription_wav",
                metadata={"channels": 1, "sample_rate_hz": TRANSCRIPTION_SAMPLE_RATE, "codec": "pcm_s16le"},
            )
        ],
        commands=[result.command],
        metadata={"preserves_source": True},
    )
    manifest.write_json(manifest_path, overwrite=overwrite)
    return manifest

