"""Compatibility wrapper for canonical audio analysis helpers.

The canonical implementation lives in :mod:`huey.media.audio_analysis`.
This module is retained so existing imports from :mod:`huey.audio.audio_analysis`
continue to work during the media-tools consolidation.
"""

from huey.media.audio_analysis import (
    AudioAnalysis,
    analyze_audio,
    bitrate,
    channels,
    duration,
    peak_level,
    rms_level,
    sample_rate,
    silence_map,
)

__all__ = [
    "AudioAnalysis",
    "analyze_audio",
    "bitrate",
    "channels",
    "duration",
    "peak_level",
    "rms_level",
    "sample_rate",
    "silence_map",
]
