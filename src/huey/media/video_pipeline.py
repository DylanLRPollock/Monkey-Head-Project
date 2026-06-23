"""Video helpers that build on the central FFmpeg media manager."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from huey.media.ffmpeg_validator import validate_media_environment
from huey.media.media_manager import (
    FFmpegManager,
    _coerce_path,
    _ensure_source,
    _run_ffmpeg,
)
from huey.media.media_manager import extract_frames as _extract_frames
from huey.media.media_manager import (
    probe_media,
)
from huey.media.media_manifest import MediaArtifact, MediaManifest


@dataclass(frozen=True, slots=True)
class VideoPipelineResult:
    source_path: str
    duration_seconds: float
    fps: float
    metadata: dict[str, object]
    ffmpeg: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "metadata": dict(self.metadata),
            "ffmpeg": dict(self.ffmpeg),
        }


@dataclass(frozen=True, slots=True)
class VideoFramePreview:
    source_path: str
    preview_path: str
    timestamp_seconds: float
    duration_seconds: float
    fps: float
    metadata: dict[str, object]
    ffmpeg: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "preview_path": self.preview_path,
            "timestamp_seconds": self.timestamp_seconds,
            "duration_seconds": self.duration_seconds,
            "fps": self.fps,
            "metadata": dict(self.metadata),
            "ffmpeg": dict(self.ffmpeg),
        }


class VideoPipeline:
    """Structured wrapper around the existing functional video helpers."""

    def inspect(self, source: str | Path) -> VideoPipelineResult:
        source_path = _ensure_source(source)
        metadata = video_metadata(source_path)
        return VideoPipelineResult(
            source_path=str(source_path),
            duration_seconds=video_duration(source_path),
            fps=video_fps(source_path),
            metadata=metadata,
            ffmpeg=validate_media_environment(),
        )

    def extract_preview(
        self,
        source: str | Path,
        target: str | Path,
        *,
        timestamp_seconds: float = 1.0,
    ) -> VideoFramePreview:
        source_path = _ensure_source(source)
        preview_path = extract_thumbnail(
            source_path,
            target,
            timestamp=timestamp_seconds,
        )
        inspection = self.inspect(source_path)
        return VideoFramePreview(
            source_path=inspection.source_path,
            preview_path=str(preview_path),
            timestamp_seconds=timestamp_seconds,
            duration_seconds=inspection.duration_seconds,
            fps=inspection.fps,
            metadata=inspection.metadata,
            ffmpeg=inspection.ffmpeg,
        )

    def segment(
        self,
        source: str | Path,
        output_dir: str | Path,
        *,
        chunk_seconds: float = 30.0,
        prefix: str = "segment",
    ) -> dict[str, object]:
        segments = split_video(
            source,
            output_dir,
            chunk_seconds=chunk_seconds,
            prefix=prefix,
        )
        inspection = self.inspect(source)
        return {
            "segments": [str(path) for path in segments],
            "chunk_seconds": chunk_seconds,
            "inspection": inspection.to_dict(),
        }


def extract_frames(
    source: str | Path,
    output_pattern: str | Path,
    *,
    fps: float = 1.0,
) -> Path:
    """Extract video frames to a numbered image sequence."""

    return _extract_frames(source, output_pattern, fps=fps)


def extract_keyframes(
    source: str | Path,
    output_pattern: str | Path,
) -> Path:
    """Extract I-frames from a video."""

    src = _ensure_source(source)
    dst = _coerce_path(output_pattern)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(
        [
            "-i",
            str(src),
            "-vf",
            "select='eq(pict_type,I)'",
            "-vsync",
            "vfr",
            str(dst),
        ]
    )
    return dst


def extract_thumbnail(
    source: str | Path,
    target: str | Path,
    *,
    timestamp: float = 1.0,
) -> Path:
    """Extract a single thumbnail frame."""

    src = _ensure_source(source)
    dst = _coerce_path(target)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(["-ss", str(timestamp), "-i", str(src), "-frames:v", "1", str(dst)])
    return dst


def split_video(
    source: str | Path,
    output_dir: str | Path,
    *,
    chunk_seconds: float = 30.0,
    prefix: str = "segment",
) -> list[Path]:
    """Split a video into fixed-duration segments."""

    src = _ensure_source(source)
    directory = _coerce_path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    pattern = directory / f"{prefix}-%03d.mp4"
    _run_ffmpeg(
        [
            "-i",
            str(src),
            "-c",
            "copy",
            "-map",
            "0",
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            str(pattern),
        ]
    )
    return sorted(directory.glob(f"{prefix}-*.mp4"))


def video_metadata(source: str | Path) -> dict[str, object]:
    """Return full ffprobe metadata for a video file."""

    return probe_media(source).raw


def video_duration(source: str | Path) -> float:
    """Return video duration in seconds."""

    payload = video_metadata(source)
    return float(payload.get("format", {}).get("duration", 0.0))


def video_fps(source: str | Path) -> float:
    """Return the primary video stream frames-per-second value."""

    payload = video_metadata(source)
    for stream in payload.get("streams", []):
        if stream.get("codec_type") != "video":
            continue
        raw_value = str(stream.get("r_frame_rate") or "0/1")
        numerator, _, denominator = raw_value.partition("/")
        if denominator and float(denominator) != 0:
            return float(numerator) / float(denominator)
        return float(numerator)
    return 0.0


def build_video_preview(
    source: str | Path,
    output_dir: str | Path,
    *,
    manager: FFmpegManager | None = None,
    overwrite: bool = False,
) -> MediaManifest:
    """Probe a video and generate a thumbnail plus transcription-ready audio."""

    media_manager = manager or FFmpegManager()
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"Video source not found: {source_path}")

    target_dir = Path(output_dir).expanduser().resolve()
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
                kind="audio",
                path=str(audio_path),
                role="extracted_transcription_audio",
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
        source,
        output,
        frame_number=frame_number,
        overwrite=overwrite,
    )
    return Path(output).expanduser().resolve()


__all__ = [
    "VideoFramePreview",
    "VideoPipeline",
    "VideoPipelineResult",
    "build_video_preview",
    "extract_video_frame",
    "extract_frames",
    "extract_keyframes",
    "extract_thumbnail",
    "split_video",
    "video_duration",
    "video_fps",
    "video_metadata",
]
