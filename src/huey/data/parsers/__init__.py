"""Structured parser adapters layered on top of Huey media services."""

from __future__ import annotations

from .audio_parser import AudioParseResult, AudioParser
from .video_parser import VideoParseResult, VideoParser

__all__ = [
    "AudioParseResult",
    "AudioParser",
    "VideoParseResult",
    "VideoParser",
]
