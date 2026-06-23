"""Transcription helpers that connect FFmpeg preprocessing to speech models."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from huey.media.speech_pipeline import prepare_for_whisper
from huey.utils.paths import ensure_subdirectory

type TranscriptionPayload = dict[str, object]
type Transcriber = Callable[[str], TranscriptionPayload | str]


def _default_prepared_path(source: str | Path) -> Path:
    prepared_dir = ensure_subdirectory("AUDIO", "prepared")
    src = Path(source).expanduser().resolve()
    return prepared_dir / f"{src.stem}.whisper.wav"


def transcribe(
    source: str | Path,
    *,
    transcriber: Transcriber | None = None,
    model_name: str = "small.en",
    language: str = "en",
    prepare_audio: bool = True,
    mock: bool = False,
) -> dict[str, object]:
    """Transcribe audio through an injected or local Whisper-compatible backend."""

    source_path = Path(source).expanduser().resolve()
    if mock and transcriber is None:
        prepared_path = source_path
    else:
        prepared_path = (
            prepare_for_whisper(
                source_path,
                output_path=_default_prepared_path(source_path),
            )
            if prepare_audio
            else source_path
        )

    if transcriber is not None:
        result = transcriber(str(prepared_path))
        if isinstance(result, dict):
            payload = dict(result)
        else:
            payload = {"transcript": str(result)}
        payload.setdefault("transcription_engine", "custom")
        payload.setdefault("transcription_model", model_name)
        payload.setdefault("language", language)
        payload["source_file"] = str(source_path)
        payload["prepared_file"] = str(prepared_path)
        return payload

    if mock:
        return {
            "source_file": str(source_path),
            "prepared_file": str(prepared_path),
            "transcript": f"Mock transcript for {source_path.name}",
            "segments": [],
            "language": language,
            "transcription_engine": "mock-transcriber",
            "transcription_model": model_name,
        }

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster_whisper is not installed; pass a custom transcriber or mock=True"
        ) from exc

    model = WhisperModel(model_name, device="auto", compute_type="int8")
    segments, info = model.transcribe(str(prepared_path), language=language)
    collected_segments = []
    transcript_parts: list[str] = []
    for segment in segments:
        segment_payload = {
            "start": float(segment.start),
            "end": float(segment.end),
            "text": segment.text.strip(),
        }
        collected_segments.append(segment_payload)
        transcript_parts.append(segment_payload["text"])
    return {
        "source_file": str(source_path),
        "prepared_file": str(prepared_path),
        "transcript": " ".join(part for part in transcript_parts if part),
        "segments": collected_segments,
        "language": getattr(info, "language", language),
        "duration": getattr(info, "duration", None),
        "transcription_engine": "faster-whisper",
        "transcription_model": model_name,
    }


def batch_transcribe(
    sources: list[str | Path],
    *,
    transcriber: Transcriber | None = None,
    model_name: str = "small.en",
    language: str = "en",
    prepare_audio: bool = True,
    mock: bool = False,
) -> list[TranscriptionPayload]:
    """Transcribe multiple audio fixtures."""

    return [
        transcribe(
            source,
            transcriber=transcriber,
            model_name=model_name,
            language=language,
            prepare_audio=prepare_audio,
            mock=mock,
        )
        for source in sources
    ]


def transcription_metadata(payload: TranscriptionPayload) -> TranscriptionPayload:
    """Return a stable metadata subset for a transcription result."""

    return {
        "source_file": payload.get("source_file"),
        "prepared_file": payload.get("prepared_file"),
        "language": payload.get("language"),
        "transcription_engine": payload.get("transcription_engine"),
        "transcription_model": payload.get("transcription_model"),
        "duration": payload.get("duration"),
        "segment_count": len(payload.get("segments", [])),
    }


__all__ = ["batch_transcribe", "transcribe", "transcription_metadata"]
