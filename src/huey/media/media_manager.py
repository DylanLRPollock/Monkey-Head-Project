"""Safe FFmpeg/ffprobe helpers for HueyOS media preprocessing."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MediaProbeResult:
    """Structured ffprobe metadata for a media file."""

    path: Path
    format_name: str | None
    duration_seconds: float | None
    bit_rate: int | None
    size_bytes: int | None
    streams: list[dict[str, Any]]
    raw: dict[str, Any]


@dataclass(frozen=True)
class FFmpegCommandResult:
    """Result from an FFmpeg or ffprobe subprocess invocation."""

    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """Return True when the subprocess exited cleanly."""
        return self.returncode == 0


@dataclass(frozen=True)
class AudioTransformOptions:
    """Options for safe audio preprocessing and conversion."""

    sample_rate: int | None = None
    channels: int | None = None
    normalize: bool = False
    loudnorm: bool = False
    remove_silence: bool = False
    start_seconds: float | None = None
    duration_seconds: float | None = None
    output_format: str | None = None


class FFmpegMediaManager:
    """Safe, subprocess-based wrapper around FFmpeg and ffprobe."""

    def __init__(
        self,
        ffmpeg_path: str | Path | None = None,
        ffprobe_path: str | Path | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.ffmpeg_path = self._resolve_binary(ffmpeg_path, "ffmpeg")
        self.ffprobe_path = self._resolve_binary(ffprobe_path, "ffprobe")
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _resolve_binary(
        explicit_path: str | Path | None, binary_name: str
    ) -> Path | None:
        if explicit_path is not None:
            return Path(explicit_path)

        resolved = shutil.which(binary_name)
        if resolved is None:
            return None

        return Path(resolved)

    @staticmethod
    def _stringify_output(value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode(errors="replace")
        return value

    @staticmethod
    def _parse_float(value: object) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_int(value: object) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _validate_existing_input(path: str | Path) -> Path:
        input_path = Path(path)
        if not input_path.exists():
            raise FileNotFoundError(f"Media input does not exist: {input_path}")
        return input_path

    @staticmethod
    def _validate_output_available(path: str | Path, overwrite: bool) -> Path:
        output_path = Path(path)
        if output_path.exists() and not overwrite:
            raise FileExistsError(
                f"Output already exists: {output_path}. Pass overwrite=True to replace it."
            )
        return output_path

    @staticmethod
    def _overwrite_arg(overwrite: bool) -> str:
        return "-y" if overwrite else "-n"

    def ffmpeg_available(self) -> bool:
        """Return True if an FFmpeg binary path is configured."""
        return self.ffmpeg_path is not None

    def ffprobe_available(self) -> bool:
        """Return True if an ffprobe binary path is configured."""
        return self.ffprobe_path is not None

    def require_ffmpeg(self) -> Path:
        """Return the FFmpeg path or raise with a clear installation hint."""
        if self.ffmpeg_path is None:
            raise RuntimeError(
                "FFmpeg is not available. Install FFmpeg and ensure 'ffmpeg' is on "
                "PATH, or pass ffmpeg_path explicitly."
            )
        return self.ffmpeg_path

    def require_ffprobe(self) -> Path:
        """Return the ffprobe path or raise with a clear installation hint."""
        if self.ffprobe_path is None:
            raise RuntimeError(
                "ffprobe is not available. Install FFmpeg and ensure 'ffprobe' is on "
                "PATH, or pass ffprobe_path explicitly."
            )
        return self.ffprobe_path

    def version(self) -> dict[str, str | None]:
        """Return the first version line for FFmpeg and ffprobe when available."""
        return {
            "ffmpeg": self._read_version(self.ffmpeg_path),
            "ffprobe": self._read_version(self.ffprobe_path),
        }

    def _read_version(self, binary_path: Path | None) -> str | None:
        if binary_path is None:
            return None

        result = self.run([str(binary_path), "-version"])
        if not result.ok or not result.stdout:
            return None

        return result.stdout.splitlines()[0] if result.stdout.splitlines() else None

    def probe(self, path: str | Path) -> MediaProbeResult:
        """Probe media metadata with ffprobe JSON output."""
        input_path = self._validate_existing_input(path)
        ffprobe = self.require_ffprobe()
        command = [
            str(ffprobe),
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(input_path),
        ]
        result = self.run(command)
        if not result.ok:
            raise RuntimeError(f"ffprobe failed for {input_path}: {result.stderr}")

        try:
            raw: dict[str, Any] = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"ffprobe returned invalid JSON for {input_path}"
            ) from exc

        format_info = raw.get("format", {})
        if not isinstance(format_info, dict):
            format_info = {}

        streams = raw.get("streams", [])
        if not isinstance(streams, list):
            streams = []

        return MediaProbeResult(
            path=input_path,
            format_name=format_info.get("format_name"),
            duration_seconds=self._parse_float(format_info.get("duration")),
            bit_rate=self._parse_int(format_info.get("bit_rate")),
            size_bytes=self._parse_int(format_info.get("size")),
            streams=streams,
            raw=raw,
        )

    def run(
        self, args: list[str], timeout_seconds: float | None = None
    ) -> FFmpegCommandResult:
        """Execute a list-based subprocess command without shell interpolation."""
        command = [str(arg) for arg in args]
        timeout = self.timeout_seconds if timeout_seconds is None else timeout_seconds

        try:
            completed = subprocess.run(
                command,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return FFmpegCommandResult(
                command=command,
                returncode=124,
                stdout=self._stringify_output(exc.stdout),
                stderr=(
                    f"Command timed out after {timeout} seconds: "
                    f"{' '.join(command)}"
                ),
            )
        except FileNotFoundError as exc:
            return FFmpegCommandResult(
                command=command,
                returncode=127,
                stdout="",
                stderr=str(exc),
            )
        except OSError as exc:
            return FFmpegCommandResult(
                command=command,
                returncode=1,
                stdout="",
                stderr=str(exc),
            )

        return FFmpegCommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def build_audio_transform_command(
        self,
        input_path: str | Path,
        output_path: str | Path,
        options: AudioTransformOptions,
        overwrite: bool = False,
    ) -> list[str]:
        """Build, but do not run, a safe FFmpeg audio transform command."""
        input_file = self._validate_existing_input(input_path)
        output_file = self._validate_output_available(output_path, overwrite)
        ffmpeg = self.require_ffmpeg()

        command = [str(ffmpeg), self._overwrite_arg(overwrite)]

        if options.start_seconds is not None:
            command.extend(["-ss", str(options.start_seconds)])

        command.extend(["-i", str(input_file)])

        if options.duration_seconds is not None:
            command.extend(["-t", str(options.duration_seconds)])

        if options.channels is not None:
            command.extend(["-ac", str(options.channels)])

        if options.sample_rate is not None:
            command.extend(["-ar", str(options.sample_rate)])

        filters = self._build_audio_filters(options)
        if filters:
            command.extend(["-af", ",".join(filters)])

        if options.output_format is not None:
            command.extend(["-f", options.output_format])

        command.append(str(output_file))
        return command

    @staticmethod
    def _build_audio_filters(options: AudioTransformOptions) -> list[str]:
        filters: list[str] = []

        if options.loudnorm:
            filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        elif options.normalize:
            filters.append("dynaudnorm")

        if options.remove_silence:
            filters.append(
                "silenceremove=start_periods=1:start_duration=0.2:"
                "start_threshold=-45dB:stop_periods=-1:stop_duration=0.2:"
                "stop_threshold=-45dB"
            )

        return filters

    def transform_audio(
        self,
        input_path: str | Path,
        output_path: str | Path,
        options: AudioTransformOptions | None = None,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Run an FFmpeg audio transform without modifying the source file."""
        output_file = self._validate_output_available(output_path, overwrite)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        transform_options = options or AudioTransformOptions()
        command = self.build_audio_transform_command(
            input_path=input_path,
            output_path=output_file,
            options=transform_options,
            overwrite=overwrite,
        )
        return self.run(command)

    def convert_audio(
        self,
        input_path: str | Path,
        output_path: str | Path,
        sample_rate: int | None = None,
        channels: int | None = None,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Convenience wrapper for basic audio conversion."""
        return self.transform_audio(
            input_path=input_path,
            output_path=output_path,
            options=AudioTransformOptions(sample_rate=sample_rate, channels=channels),
            overwrite=overwrite,
        )

    def prepare_for_transcription(
        self,
        input_path: str | Path,
        output_path: str | Path,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Prepare audio for the HueyOS V1 local transcription stage."""
        return self.transform_audio(
            input_path=input_path,
            output_path=output_path,
            options=AudioTransformOptions(
                sample_rate=16000,
                channels=1,
                loudnorm=True,
                remove_silence=True,
            ),
            overwrite=overwrite,
        )

    def extract_audio(
        self,
        input_path: str | Path,
        output_path: str | Path,
        sample_rate: int | None = 16000,
        channels: int | None = 1,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Extract or convert audio from an audio/video input."""
        return self.transform_audio(
            input_path=input_path,
            output_path=output_path,
            options=AudioTransformOptions(sample_rate=sample_rate, channels=channels),
            overwrite=overwrite,
        )

    def generate_waveform_image(
        self,
        input_path: str | Path,
        output_path: str | Path,
        width: int = 1280,
        height: int = 320,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Generate a waveform image from an audio file."""
        return self._run_visual_media_command(
            input_path=input_path,
            output_path=output_path,
            filter_arg=f"showwavespic=s={width}x{height}",
            overwrite=overwrite,
        )

    def generate_spectrogram_image(
        self,
        input_path: str | Path,
        output_path: str | Path,
        width: int = 1280,
        height: int = 720,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Generate a spectrogram image from an audio file."""
        return self._run_visual_media_command(
            input_path=input_path,
            output_path=output_path,
            filter_arg=f"showspectrumpic=s={width}x{height}",
            overwrite=overwrite,
        )

    def _run_visual_media_command(
        self,
        input_path: str | Path,
        output_path: str | Path,
        filter_arg: str,
        overwrite: bool,
    ) -> FFmpegCommandResult:
        input_file = self._validate_existing_input(input_path)
        output_file = self._validate_output_available(output_path, overwrite)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = self.require_ffmpeg()
        command = [
            str(ffmpeg),
            self._overwrite_arg(overwrite),
            "-i",
            str(input_file),
            "-filter_complex",
            filter_arg,
            "-frames:v",
            "1",
            str(output_file),
        ]
        return self.run(command)

    def extract_frames(
        self,
        input_path: str | Path,
        output_dir: str | Path,
        fps: float = 1.0,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Extract image frames from a video input."""
        input_file = self._validate_existing_input(input_path)
        frames_dir = Path(output_dir)
        frames_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg = self.require_ffmpeg()
        output_pattern = frames_dir / "frame_%06d.png"
        command = [
            str(ffmpeg),
            self._overwrite_arg(overwrite),
            "-i",
            str(input_file),
            "-vf",
            f"fps={fps}",
            str(output_pattern),
        ]
        return self.run(command)

    def extract_thumbnail(
        self,
        input_path: str | Path,
        output_path: str | Path,
        timestamp_seconds: float = 1.0,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Extract a single thumbnail frame from a video input."""
        input_file = self._validate_existing_input(input_path)
        output_file = self._validate_output_available(output_path, overwrite)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        ffmpeg = self.require_ffmpeg()
        command = [
            str(ffmpeg),
            self._overwrite_arg(overwrite),
            "-ss",
            str(timestamp_seconds),
            "-i",
            str(input_file),
            "-frames:v",
            "1",
            str(output_file),
        ]
        return self.run(command)

    def detect_silence(
        self,
        input_path: str | Path,
        noise_db: int = -45,
        duration_seconds: float = 0.2,
    ) -> FFmpegCommandResult:
        """Run FFmpeg silencedetect without parsing the output yet."""
        input_file = self._validate_existing_input(input_path)
        ffmpeg = self.require_ffmpeg()
        command = [
            str(ffmpeg),
            "-i",
            str(input_file),
            "-af",
            f"silencedetect=noise={noise_db}dB:d={duration_seconds}",
            "-f",
            "null",
            "-",
        ]
        return self.run(command)

    def split_audio_chunks(
        self,
        input_path: str | Path,
        output_dir: str | Path,
        chunk_seconds: int = 300,
        overwrite: bool = False,
    ) -> FFmpegCommandResult:
        """Split audio into fixed-length chunks with FFmpeg's segment muxer."""
        input_file = self._validate_existing_input(input_path)
        chunks_dir = Path(output_dir)
        chunks_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg = self.require_ffmpeg()
        output_pattern = chunks_dir / "chunk_%03d.wav"
        command = [
            str(ffmpeg),
            self._overwrite_arg(overwrite),
            "-i",
            str(input_file),
            "-f",
            "segment",
            "-segment_time",
            str(chunk_seconds),
            "-c",
            "copy",
            str(output_pattern),
        ]
        return self.run(command)


def get_default_manager() -> FFmpegMediaManager:
    """Return a default FFmpeg media manager instance."""
    return FFmpegMediaManager()


def check_ffmpeg_available() -> bool:
    """Return True when FFmpeg is available to the default manager."""
    return get_default_manager().ffmpeg_available()


def _coerce_path(path: str | Path) -> Path:
    """Resolve ``path`` to an absolute filesystem path."""

    return Path(path).expanduser().resolve()


def _ensure_source(path: str | Path) -> Path:
    """Resolve ``path`` and ensure the source file exists."""

    source = _coerce_path(path)
    if not source.exists():
        raise FileNotFoundError(source)
    return source


def _raise_for_failure(result: FFmpegCommandResult, operation: str) -> None:
    """Raise a runtime error when an FFmpeg command did not complete cleanly."""

    if result.ok:
        return
    details = result.stderr.strip() or result.stdout.strip() or operation
    raise RuntimeError(f"{operation}: {details}")


def _run_ffmpeg(
    args: list[str], timeout_seconds: float | None = None
) -> FFmpegCommandResult:
    """Run an FFmpeg command through the default manager and enforce success."""

    manager = get_default_manager()
    ffmpeg = manager.require_ffmpeg()
    result = manager.run([str(ffmpeg), *[str(arg) for arg in args]], timeout_seconds)
    _raise_for_failure(result, "ffmpeg command failed")
    return result


def probe_media(path: str | Path) -> MediaProbeResult:
    """Probe media with a default FFmpeg media manager."""
    return get_default_manager().probe(path)


def prepare_audio_for_transcription(
    input_path: str | Path,
    output_path: str | Path,
    overwrite: bool = False,
) -> FFmpegCommandResult:
    """Prepare audio for V1 transcription with a default manager."""
    return get_default_manager().prepare_for_transcription(
        input_path=input_path,
        output_path=output_path,
        overwrite=overwrite,
    )


__all__ = [
    "AudioTransformOptions",
    "convert_audio",
    "detect_silence",
    "extract_audio",
    "extract_frames",
    "FFmpegCommandResult",
    "FFmpegMediaManager",
    "MediaProbeResult",
    "check_ffmpeg_available",
    "get_default_manager",
    "normalize_audio",
    "prepare_audio_for_transcription",
    "probe_media",
    "remove_silence",
    "resample_audio",
    "transcode_video",
]


def convert_audio(
    source: str | Path,
    target: str | Path,
    *,
    bitrate: str | None = None,
    sample_rate: int | None = None,
    channels: int | None = None,
    overwrite: bool = True,
) -> Path:
    """Convert audio to a new container or codec using the default manager."""

    src = _ensure_source(source)
    dst = _coerce_path(target)
    dst.parent.mkdir(parents=True, exist_ok=True)
    manager = get_default_manager()
    ffmpeg = manager.require_ffmpeg()
    command = [str(ffmpeg), "-y" if overwrite else "-n", "-i", str(src)]
    if channels is not None:
        command.extend(["-ac", str(channels)])
    if sample_rate is not None:
        command.extend(["-ar", str(sample_rate)])
    if bitrate is not None:
        command.extend(["-b:a", str(bitrate)])
    command.append(str(dst))
    result = manager.run(command)
    _raise_for_failure(result, f"audio conversion failed for {src}")
    return dst


def extract_audio(
    source: str | Path,
    target: str | Path,
    *,
    codec: str | None = None,
    sample_rate: int | None = 16000,
    channels: int | None = 1,
    overwrite: bool = True,
) -> Path:
    """Extract audio from a media file using the default manager."""

    src = _ensure_source(source)
    dst = _coerce_path(target)
    dst.parent.mkdir(parents=True, exist_ok=True)
    manager = get_default_manager()
    ffmpeg = manager.require_ffmpeg()
    command = [str(ffmpeg), "-y" if overwrite else "-n", "-i", str(src), "-vn"]
    if codec is not None:
        command.extend(["-acodec", codec])
    if channels is not None:
        command.extend(["-ac", str(channels)])
    if sample_rate is not None:
        command.extend(["-ar", str(sample_rate)])
    command.append(str(dst))
    result = manager.run(command)
    _raise_for_failure(result, f"audio extraction failed for {src}")
    return dst


def transcode_video(
    source: str | Path,
    target: str | Path,
    *,
    video_codec: str = "libx264",
    audio_codec: str | None = None,
    overwrite: bool = True,
) -> Path:
    """Transcode video to a new container or codec using the default manager."""

    src = _ensure_source(source)
    dst = _coerce_path(target)
    dst.parent.mkdir(parents=True, exist_ok=True)
    manager = get_default_manager()
    ffmpeg = manager.require_ffmpeg()
    command = [
        str(ffmpeg),
        "-y" if overwrite else "-n",
        "-i",
        str(src),
        "-c:v",
        video_codec,
    ]
    if audio_codec is not None:
        command.extend(["-c:a", audio_codec])
    command.append(str(dst))
    result = manager.run(command)
    _raise_for_failure(result, f"video transcode failed for {src}")
    return dst


def resample_audio(
    source: str | Path,
    target: str | Path,
    *,
    channels: int | None = None,
    sample_rate: int | None = None,
    overwrite: bool = True,
) -> Path:
    """Resample audio to the requested channel count or sample rate."""

    manager = get_default_manager()
    result = manager.transform_audio(
        input_path=source,
        output_path=target,
        options=AudioTransformOptions(sample_rate=sample_rate, channels=channels),
        overwrite=overwrite,
    )
    _raise_for_failure(result, f"audio resample failed for {source}")
    return _coerce_path(target)


def normalize_audio(
    source: str | Path,
    target: str | Path,
    *,
    overwrite: bool = True,
) -> Path:
    """Normalize audio loudness for downstream processing."""

    manager = get_default_manager()
    result = manager.transform_audio(
        input_path=source,
        output_path=target,
        options=AudioTransformOptions(loudnorm=True),
        overwrite=overwrite,
    )
    _raise_for_failure(result, f"audio normalization failed for {source}")
    return _coerce_path(target)


def remove_silence(
    source: str | Path,
    target: str | Path,
    *,
    threshold: str = "-30dB",
    min_silence_duration: float = 0.5,
    overwrite: bool = True,
) -> Path:
    """Trim silence from an audio file using FFmpeg's silenceremove filter."""

    src = _ensure_source(source)
    dst = _coerce_path(target)
    dst.parent.mkdir(parents=True, exist_ok=True)
    filter_arg = (
        "silenceremove="
        f"start_periods=1:start_duration={min_silence_duration}:start_threshold={threshold}:"
        f"stop_periods=-1:stop_duration={min_silence_duration}:stop_threshold={threshold}"
    )
    command = [
        "-y" if overwrite else "-n",
        "-i",
        str(src),
        "-af",
        filter_arg,
        str(dst),
    ]
    _run_ffmpeg(command)
    return dst


def extract_frames(
    source: str | Path,
    output_pattern: str | Path,
    *,
    fps: float = 1.0,
) -> Path:
    """Extract frames to ``output_pattern`` using a legacy-compatible wrapper."""

    src = _ensure_source(source)
    dst = _coerce_path(output_pattern)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(["-i", str(src), "-vf", f"fps={fps}", str(dst)])
    return dst


def extract_thumbnail(
    source: str | Path,
    target: str | Path,
    *,
    timestamp: float = 1.0,
) -> Path:
    """Extract a single thumbnail frame from a video source."""

    src = _ensure_source(source)
    dst = _coerce_path(target)
    dst.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(["-ss", str(timestamp), "-i", str(src), "-frames:v", "1", str(dst)])
    return dst


def split_audio_chunks(
    source: str | Path,
    output_dir: str | Path,
    *,
    chunk_seconds: int = 300,
    overwrite: bool = True,
) -> Path:
    """Split audio into fixed-length chunks and return the output directory."""

    manager = get_default_manager()
    result = manager.split_audio_chunks(
        input_path=source,
        output_dir=output_dir,
        chunk_seconds=chunk_seconds,
        overwrite=overwrite,
    )
    _raise_for_failure(result, f"audio chunking failed for {source}")
    return _coerce_path(output_dir)


def detect_silence(
    source: str | Path,
    noise_db: int = -45,
    duration_seconds: float = 0.2,
) -> list[dict[str, float]]:
    """Detect silence ranges and return parsed segment boundaries."""

    result = get_default_manager().detect_silence(
        input_path=source,
        noise_db=noise_db,
        duration_seconds=duration_seconds,
    )
    _raise_for_failure(result, f"silence detection failed for {source}")
    segments: list[dict[str, float]] = []
    start: float | None = None
    start_pattern = re.compile(r"silence_start:\s*([0-9.]+)")
    end_pattern = re.compile(
        r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)"
    )
    for line in result.stderr.splitlines():
        start_match = start_pattern.search(line)
        if start_match:
            start = float(start_match.group(1))
            continue
        end_match = end_pattern.search(line)
        if end_match:
            end = float(end_match.group(1))
            duration = float(end_match.group(2))
            segments.append(
                {
                    "start": start if start is not None else max(0.0, end - duration),
                    "end": end,
                    "duration": duration,
                }
            )
            start = None
    return segments
