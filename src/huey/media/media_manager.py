"""Central FFmpeg wrapper used by audio, video, and ingestion pipelines."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from huey.media.ffmpeg_validator import validate_media_environment

SilenceRange = dict[str, float]


def _coerce_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def _ensure_source(value: str | Path) -> Path:
    path = _coerce_path(value)
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def _prepare_output(value: str | Path) -> Path:
    path = _coerce_path(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _run_process(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def _run_ffmpeg(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    environment = validate_media_environment()
    if not environment["ffmpeg"]:
        raise RuntimeError("ffmpeg is not available on PATH")
    return _run_process(["ffmpeg", "-hide_banner", "-y", *arguments])


def _run_ffprobe(arguments: list[str]) -> subprocess.CompletedProcess[str]:
    environment = validate_media_environment()
    if not environment["ffprobe"]:
        raise RuntimeError("ffprobe is not available on PATH")
    return _run_process(["ffprobe", "-v", "error", *arguments])


def probe_media(path: str | Path) -> dict[str, object]:
    """Return stream and format metadata for a media file."""

    source = _ensure_source(path)
    result = _run_ffprobe(
        [
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(source),
        ]
    )
    return json.loads(result.stdout or "{}")


def convert_audio(
    source: str | Path,
    target: str | Path,
    *,
    bitrate: str = "192k",
    codec: str | None = None,
) -> Path:
    """Convert audio to a new target format."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    command = ["-i", str(src), "-vn"]
    if codec:
        command.extend(["-c:a", codec])
    command.extend(["-b:a", bitrate, str(dst)])
    _run_ffmpeg(command)
    return dst


def extract_audio(
    source: str | Path,
    target: str | Path,
    *,
    codec: str | None = None,
) -> Path:
    """Extract the audio stream from a video file."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    command = ["-i", str(src), "-vn"]
    if codec:
        command.extend(["-c:a", codec])
    else:
        command.extend(["-c:a", "copy"])
    command.append(str(dst))
    _run_ffmpeg(command)
    return dst


def normalize_audio(
    source: str | Path,
    target: str | Path,
    *,
    integrated_lufs: int = -16,
    true_peak: float = -1.5,
    loudness_range: int = 11,
) -> Path:
    """Normalize audio loudness using FFmpeg loudnorm."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    filter_value = f"loudnorm=I={integrated_lufs}:TP={true_peak}:LRA={loudness_range}"
    _run_ffmpeg(["-i", str(src), "-af", filter_value, str(dst)])
    return dst


def trim_audio(
    source: str | Path,
    target: str | Path,
    *,
    start: float | None = None,
    end: float | None = None,
    duration: float | None = None,
) -> Path:
    """Trim audio to a requested time window."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    command: list[str] = []
    if start is not None:
        command.extend(["-ss", str(start)])
    command.extend(["-i", str(src)])
    if end is not None:
        command.extend(["-to", str(end)])
    if duration is not None:
        command.extend(["-t", str(duration)])
    command.append(str(dst))
    _run_ffmpeg(command)
    return dst


def resample_audio(
    source: str | Path,
    target: str | Path,
    *,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """Resample audio for speech and analysis pipelines."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    _run_ffmpeg(
        [
            "-i",
            str(src),
            "-ar",
            str(sample_rate),
            "-ac",
            str(channels),
            str(dst),
        ]
    )
    return dst


def transcode_video(
    source: str | Path,
    target: str | Path,
    *,
    video_codec: str = "libx264",
    audio_codec: str = "aac",
    crf: int = 23,
    preset: str = "medium",
) -> Path:
    """Transcode video to a portable distribution format."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    _run_ffmpeg(
        [
            "-i",
            str(src),
            "-c:v",
            video_codec,
            "-preset",
            preset,
            "-crf",
            str(crf),
            "-c:a",
            audio_codec,
            "-movflags",
            "+faststart",
            str(dst),
        ]
    )
    return dst


def extract_frames(
    source: str | Path,
    output_pattern: str | Path,
    *,
    fps: float = 1.0,
) -> Path:
    """Extract video frames to an image sequence."""

    src = _ensure_source(source)
    dst = _prepare_output(output_pattern)
    _run_ffmpeg(["-i", str(src), "-vf", f"fps={fps}", str(dst)])
    return dst


def generate_waveform(
    source: str | Path,
    target: str | Path,
    *,
    width: int = 1280,
    height: int = 320,
    color: str = "0x7a4fa0",
) -> Path:
    """Generate a waveform image for an audio file."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    filter_value = f"showwavespic=s={width}x{height}:colors={color}"
    _run_ffmpeg(["-i", str(src), "-lavfi", filter_value, "-frames:v", "1", str(dst)])
    return dst


def generate_spectrogram(
    source: str | Path,
    target: str | Path,
    *,
    width: int = 1280,
    height: int = 720,
) -> Path:
    """Generate a spectrogram image for an audio file."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    filter_value = f"showspectrumpic=s={width}x{height}"
    _run_ffmpeg(["-i", str(src), "-lavfi", filter_value, "-frames:v", "1", str(dst)])
    return dst


def compress_audio(
    source: str | Path,
    target: str | Path,
    *,
    bitrate: str = "128k",
) -> Path:
    """Create a smaller audio derivative."""

    return convert_audio(source, target, bitrate=bitrate)


def compress_video(
    source: str | Path,
    target: str | Path,
    *,
    crf: int = 28,
    preset: str = "slow",
) -> Path:
    """Create a smaller video derivative."""

    return transcode_video(source, target, crf=crf, preset=preset)


def detect_silence(
    source: str | Path,
    *,
    noise: str = "-30dB",
    duration: float = 0.5,
) -> list[SilenceRange]:
    """Return detected silence spans from an audio file."""

    src = _ensure_source(source)
    result = _run_process(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(src),
            "-af",
            f"silencedetect=noise={noise}:d={duration}",
            "-f",
            "null",
            "-",
        ]
    )
    silence_start = re.compile(r"silence_start: (?P<start>[0-9.]+)")
    silence_end = re.compile(
        r"silence_end: (?P<end>[0-9.]+) \| silence_duration: (?P<duration>[0-9.]+)"
    )
    starts: list[float] = []
    ranges: list[SilenceRange] = []
    for line in (result.stderr or "").splitlines():
        start_match = silence_start.search(line)
        if start_match:
            starts.append(float(start_match.group("start")))
            continue
        end_match = silence_end.search(line)
        if end_match and starts:
            start = starts.pop(0)
            ranges.append(
                {
                    "start": start,
                    "end": float(end_match.group("end")),
                    "duration": float(end_match.group("duration")),
                }
            )
    return ranges


def remove_silence(
    source: str | Path,
    target: str | Path,
    *,
    threshold: str = "-30dB",
    min_silence_duration: float = 0.5,
) -> Path:
    """Remove leading, trailing, and internal silence using FFmpeg filters."""

    src = _ensure_source(source)
    dst = _prepare_output(target)
    filter_value = (
        "silenceremove="
        f"start_periods=1:start_duration={min_silence_duration}:"
        f"start_threshold={threshold}:"
        f"stop_periods=-1:stop_duration={min_silence_duration}:"
        f"stop_threshold={threshold}"
    )
    _run_ffmpeg(["-i", str(src), "-af", filter_value, str(dst)])
    return dst


def split_audio_chunks(
    source: str | Path,
    output_dir: str | Path,
    *,
    chunk_seconds: float = 30.0,
    prefix: str = "chunk",
    extension: str = ".wav",
) -> list[Path]:
    """Split an audio file into evenly-sized chunks."""

    src = _ensure_source(source)
    directory = _coerce_path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    suffix = extension if extension.startswith(".") else f".{extension}"
    pattern = directory / f"{prefix}-%03d{suffix}"
    _run_ffmpeg(
        [
            "-i",
            str(src),
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-c",
            "copy",
            str(pattern),
        ]
    )
    return sorted(directory.glob(f"{prefix}-*{suffix}"))


__all__ = [
    "compress_audio",
    "compress_video",
    "convert_audio",
    "detect_silence",
    "extract_audio",
    "extract_frames",
    "generate_spectrogram",
    "generate_waveform",
    "normalize_audio",
    "probe_media",
    "remove_silence",
    "resample_audio",
    "split_audio_chunks",
    "transcode_video",
    "trim_audio",
]
