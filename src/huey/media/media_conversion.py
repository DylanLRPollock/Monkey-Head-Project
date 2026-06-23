"""Higher-level audio, video, and image conversion helpers."""

from __future__ import annotations

import shutil
from pathlib import Path

from huey.media.convert_video_to_gif import convert_video_to_gif
from huey.media.media_manager import convert_audio as _convert_audio
from huey.media.media_manager import extract_audio as _extract_audio
from huey.media.media_manager import transcode_video as _transcode_video

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".m4a", ".aac", ".ogg"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff"}


def _require_source(path: str | Path) -> Path:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    return source


def convert_audio(src: str | Path, dst: str | Path, bitrate: str = "192k") -> Path:
    """Convert an audio file to a new format using FFmpeg."""

    source = _require_source(src)
    return _convert_audio(source, dst, bitrate=bitrate)


def convert_video(src: str | Path, dst: str | Path, codec: str = "libx264") -> Path:
    """Convert a video file to a new format using FFmpeg."""

    source = _require_source(src)
    return _transcode_video(source, dst, video_codec=codec)


def convert_file(src: str | Path, dst: str | Path) -> Path:
    """Generic file conversion by copying to a new path."""

    source = _require_source(src)
    target = Path(dst).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    return target


def extract_audio(src: str | Path, dst: str | Path) -> Path:
    """Extract the audio track from a video file."""

    source = _require_source(src)
    extension = Path(dst).suffix.lower()
    codec = "libmp3lame" if extension == ".mp3" else None
    return _extract_audio(source, dst, codec=codec)


def convert_media(
    src: str | Path,
    dst: str | Path,
    *,
    bitrate: str = "192k",
    codec: str = "libx264",
) -> Path:
    """Convert audio, video, or images, falling back to a plain file copy."""

    source = _require_source(src)
    source_extension = source.suffix.lower()
    target_extension = Path(dst).suffix.lower()

    if source_extension in VIDEO_EXTENSIONS and target_extension in AUDIO_EXTENSIONS:
        return extract_audio(source, dst)
    if source_extension in AUDIO_EXTENSIONS:
        return convert_audio(source, dst, bitrate=bitrate)
    if source_extension in VIDEO_EXTENSIONS:
        if target_extension == ".gif":
            return convert_video_to_gif(source, dst)
        return convert_video(source, dst, codec=codec)
    if source_extension in IMAGE_EXTENSIONS and target_extension in IMAGE_EXTENSIONS:
        return convert_file(source, dst)
    return convert_file(source, dst)


__all__ = [
    "AUDIO_EXTENSIONS",
    "IMAGE_EXTENSIONS",
    "VIDEO_EXTENSIONS",
    "convert_audio",
    "convert_file",
    "convert_media",
    "convert_video",
    "extract_audio",
]
