"""Pre-transcription audio preparation for Whisper-style pipelines."""

from __future__ import annotations

from pathlib import Path

from huey.media.media_manager import (
    FFmpegManager,
    _coerce_path,
    _ensure_source,
    _run_ffmpeg,
)
from huey.media.media_manager import normalize_audio as _normalize_audio
from huey.media.media_manager import remove_silence as _remove_silence
from huey.media.media_manager import resample_audio as _resample_audio
from huey.media.media_manifest import MediaArtifact, MediaManifest
from huey.utils.paths import ensure_subdirectory

TRANSCRIPTION_SAMPLE_RATE = 16000


def normalize_volume(source: str | Path, target: str | Path) -> Path:
    """Normalize audio loudness before transcription."""

    return _normalize_audio(source, target)


def denoise_audio(
    source: str | Path,
    target: str | Path,
    *,
    noise_reduction_filter: str = "afftdn=nf=-25",
) -> Path:
    """Apply a light denoise filter suitable for speech."""

    src = _ensure_source(source)
    dst = _coerce_path(target)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(["-i", str(src), "-af", noise_reduction_filter, str(dst)])
    return dst


def convert_to_mono(source: str | Path, target: str | Path) -> Path:
    """Downmix audio to a single speech channel."""

    return _resample_audio(source, target, channels=1, sample_rate=44100)


def convert_to_16khz(source: str | Path, target: str | Path) -> Path:
    """Resample audio to 16kHz for Whisper-style models."""

    return _resample_audio(source, target, channels=1, sample_rate=16000)


def remove_silence(
    source: str | Path,
    target: str | Path,
    *,
    threshold: str = "-30dB",
    min_silence_duration: float = 0.5,
) -> Path:
    """Remove silence regions from a speech file."""

    return _remove_silence(
        source,
        target,
        threshold=threshold,
        min_silence_duration=min_silence_duration,
    )


def _default_output_path(source: str | Path, suffix: str) -> Path:
    prepared_dir = ensure_subdirectory("AUDIO", "prepared")
    src = _ensure_source(source)
    return prepared_dir / f"{src.stem}.{suffix}.wav"


def generate_transcription_ready_file(
    source: str | Path,
    *,
    output_path: str | Path | None = None,
) -> Path:
    """Run the full pre-transcription audio pipeline."""

    src = _ensure_source(source)
    normalized = _default_output_path(src, "normalized")
    trimmed = _default_output_path(src, "nosilence")
    mono = _default_output_path(src, "mono")
    final_path = (
        _coerce_path(output_path) if output_path else _default_output_path(src, "ready")
    )

    normalize_volume(src, normalized)
    remove_silence(normalized, trimmed)
    convert_to_mono(trimmed, mono)
    convert_to_16khz(mono, final_path)
    return final_path


def _command_list(result: object) -> list[str]:
    command = getattr(result, "command", None)
    if isinstance(command, list):
        return [str(part) for part in command]
    return []


def prepare_audio_for_transcription(
    source: str | Path,
    output_path: str | Path,
    *,
    manager: FFmpegManager | object | None = None,
    overwrite: bool = False,
) -> MediaManifest:
    """Prepare an audio file and return a manifest describing the derived output."""

    media_manager = manager or FFmpegManager()
    source_path = _ensure_source(source)
    target_path = _coerce_path(output_path)
    if target_path.exists() and not overwrite:
        raise FileExistsError(f"Output already exists: {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    intermediate_path = target_path.with_name(f"{target_path.stem}.converted.wav")
    probe = (
        media_manager.probe(source_path) if hasattr(media_manager, "probe") else None
    )

    try:
        convert_result = media_manager.convert_audio(
            source_path,
            intermediate_path,
            sample_rate=TRANSCRIPTION_SAMPLE_RATE,
            channels=1,
            overwrite=overwrite,
        )
        normalize_result = media_manager.normalize_audio(
            intermediate_path,
            target_path,
            overwrite=overwrite,
        )
    finally:
        if intermediate_path.exists():
            intermediate_path.unlink()

    return MediaManifest(
        source_path=str(source_path),
        operation="prepare_audio_for_transcription",
        probe=probe,
        artifacts=[
            MediaArtifact(
                kind="audio",
                path=str(target_path),
                role="transcription_wav",
                metadata={
                    "channels": 1,
                    "sample_rate_hz": TRANSCRIPTION_SAMPLE_RATE,
                },
            )
        ],
        commands=[_command_list(convert_result), _command_list(normalize_result)],
        metadata={"preserves_source": True},
    )


def prepare_for_whisper(
    source: str | Path,
    *,
    output_path: str | Path | None = None,
) -> Path:
    """Prepare an audio file for Whisper ingestion."""

    return generate_transcription_ready_file(source, output_path=output_path)


__all__ = [
    "convert_to_16khz",
    "convert_to_mono",
    "denoise_audio",
    "generate_transcription_ready_file",
    "normalize_volume",
    "prepare_audio_for_transcription",
    "prepare_for_whisper",
    "remove_silence",
]
