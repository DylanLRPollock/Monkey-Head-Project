"""Video parser built on the shared FFmpeg-aware video pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from huey.media.video_pipeline import VideoPipeline


@dataclass(frozen=True, slots=True)
class VideoParseResult:
    source_path: str
    preview_path: str | None
    duration_seconds: float
    fps: float
    metadata: dict[str, object]
    ffmpeg: dict[str, object]
    status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "preview_path": self.preview_path,
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "metadata": dict(self.metadata),
            "ffmpeg": dict(self.ffmpeg),
            "status": self.status,
        }


class VideoParser:
    """Read metadata and delegate preview extraction to ``huey.media``."""

    def __init__(self, pipeline: VideoPipeline | None = None) -> None:
        self.pipeline = pipeline or VideoPipeline()

    def inspect(self, source: str | Path) -> VideoParseResult:
        inspection = self.pipeline.inspect(source)
        return VideoParseResult(
            source_path=inspection.source_path,
            preview_path=None,
            duration_seconds=inspection.duration_seconds,
            fps=inspection.fps,
            metadata=inspection.metadata,
            ffmpeg=inspection.ffmpeg,
            status="inspected",
        )

    def extract_preview(
        self,
        source: str | Path,
        *,
        output_path: str | Path | None = None,
        timestamp_seconds: float = 1.0,
    ) -> VideoParseResult:
        source_path = Path(source).expanduser().resolve()
        target_path = (
            Path(output_path).expanduser().resolve()
            if output_path is not None
            else source_path.with_name(f"{source_path.stem}.preview.png")
        )
        preview = self.pipeline.extract_preview(
            source_path,
            target_path,
            timestamp_seconds=timestamp_seconds,
        )
        return VideoParseResult(
            source_path=preview.source_path,
            preview_path=preview.preview_path,
            duration_seconds=preview.duration_seconds,
            fps=preview.fps,
            metadata=preview.metadata,
            ffmpeg=preview.ffmpeg,
            status="preview-extracted",
        )


__all__ = ["VideoParseResult", "VideoParser"]
