"""Structured parser adapters layered on top of Huey media services."""

from __future__ import annotations

from .audio_parser import AudioParser, AudioParseResult
from .video_parser import VideoParser, VideoParseResult

__all__ = [
    "AudioParseResult",
    "AudioParser",
    "VideoParseResult",
    "VideoParser",
]
