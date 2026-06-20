"""Canonical media and FFmpeg helpers for HueyOS."""

from huey.media.ffmpeg_validator import (
    check_ffmpeg,
    check_ffprobe,
    get_ffmpeg_version,
    validate_media_environment,
)
from huey.media.media_manager import (
    compress_audio,
    compress_video,
    convert_audio,
    detect_silence,
    extract_audio,
    extract_frames,
    generate_spectrogram,
    generate_waveform,
    normalize_audio,
    probe_media,
    remove_silence,
    resample_audio,
    split_audio_chunks,
    transcode_video,
    trim_audio,
)

__all__ = [
    "check_ffmpeg",
    "check_ffprobe",
    "compress_audio",
    "compress_video",
    "convert_audio",
    "detect_silence",
    "extract_audio",
    "extract_frames",
    "generate_spectrogram",
    "generate_waveform",
    "get_ffmpeg_version",
    "normalize_audio",
    "probe_media",
    "remove_silence",
    "resample_audio",
    "split_audio_chunks",
    "transcode_video",
    "trim_audio",
    "validate_media_environment",
]
