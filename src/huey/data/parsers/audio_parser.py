"""Audio parser that delegates preprocessing to the shared speech pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from huey.media.ffmpeg_validator import validate_media_environment
from huey.media.media_manager import probe_media
from huey.media.speech_pipeline import prepare_for_whisper


@dataclass(frozen=True, slots=True)
class AudioParseResult:
    source_path: str
    prepared_path: str | None
    duration_seconds: float | None
    format_name: str | None
    metadata: dict[str, object]
    ffmpeg: dict[str, object]
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "prepared_path": self.prepared_path,
            "duration_seconds": self.duration_seconds,
            "format_name": self.format_name,
            "metadata": dict(self.metadata),
            "ffmpeg": dict(self.ffmpeg),
            "status": self.status,
        }


class AudioParser:
    """Collect audio metadata and prepare files for speech ingestion."""

    def inspect(self, source: str | Path) -> AudioParseResult:
        source_path = Path(source).expanduser().resolve()
        probe = probe_media(source_path)
        return AudioParseResult(
            source_path=str(source_path),
            prepared_path=None,
            duration_seconds=probe.duration_seconds,
            format_name=probe.format_name,
            metadata=probe.raw,
            ffmpeg=validate_media_environment(),
            status="inspected",
        )

    def prepare_audio(
        self,
        source: str | Path,
        *,
        output_path: str | Path | None = None,
    ) -> AudioParseResult:
        source_path = Path(source).expanduser().resolve()
        target_path = (
            Path(output_path).expanduser().resolve()
            if output_path is not None
            else source_path.with_name(f"{source_path.stem}.ready.wav")
        )
        prepared_path = prepare_for_whisper(source_path, output_path=target_path)
        inspected = self.inspect(source_path)
        return AudioParseResult(
            source_path=inspected.source_path,
            prepared_path=str(prepared_path),
            duration_seconds=inspected.duration_seconds,
            format_name=inspected.format_name,
            metadata=inspected.metadata,
            ffmpeg=inspected.ffmpeg,
            status="prepared",
        )


__all__ = ["AudioParseResult", "AudioParser"]
