"""Canonical FFmpeg and ffprobe wrapper for HueyOS media operations."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from huey.media.media_manifest import MediaProbe

Runner = Callable[..., subprocess.CompletedProcess[str]]


class FFmpegError(RuntimeError):
    """Raised when an FFmpeg or ffprobe command fails."""


@dataclass(frozen=True)
class CommandResult:
    """A completed media command with command text preserved for audit."""

    command: list[str]
    stdout: str
    stderr: str
    returncode: int


class FFmpegManager:
    """Small, testable wrapper around local FFmpeg binaries."""

    def __init__(self, ffmpeg_bin: str = "ffmpeg", ffprobe_bin: str = "ffprobe", runner: Runner = subprocess.run) -> None:
        self.ffmpeg_bin = ffmpeg_bin
        self.ffprobe_bin = ffprobe_bin
        self._runner = runner

    def validate_binaries(self) -> None:
        """Raise a clear error if FFmpeg or ffprobe is unavailable."""
        for binary in (self.ffmpeg_bin, self.ffprobe_bin):
            if shutil.which(binary) is None:
                raise FileNotFoundError(f"Required media binary not found on PATH: {binary}")

    def run(self, command: Sequence[str]) -> CommandResult:
        """Run a list-based command and return an auditable result."""
        if not command:
            raise ValueError("Command must not be empty")
        completed = self._runner(
            list(command),
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        result = CommandResult(list(command), completed.stdout or "", completed.stderr or "", completed.returncode)
        if result.returncode != 0:
            raise FFmpegError(result.stderr.strip() or f"Command failed: {result.command}")
        return result

    def probe_json(self, source: str | Path) -> dict:
        """Return raw ffprobe JSON for a media file."""
        source_path = self._require_file(source)
        command = [
            self.ffprobe_bin,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(source_path),
        ]
        return json.loads(self.run(command).stdout or "{}")

    def probe(self, source: str | Path) -> MediaProbe:
        """Return a compact probe summary for a media file."""
        source_path = self._require_file(source)
        raw = self.probe_json(source_path)
        fmt = raw.get("format", {})
        duration = _optional_float(fmt.get("duration"))
        bit_rate = _optional_int(fmt.get("bit_rate"))
        streams = raw.get("streams", [])
        return MediaProbe(str(source_path), fmt.get("format_name"), duration, bit_rate, streams)

    def prepare_transcription_wav(self, source: str | Path, output: str | Path, *, overwrite: bool = False) -> CommandResult:
        """Convert audio to mono 16 kHz WAV with loudness normalization."""
        source_path = self._require_file(source)
        output_path = self._prepare_output(output, overwrite=overwrite)
        command = [
            self.ffmpeg_bin,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-i",
            str(source_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a",
            "pcm_s16le",
            str(output_path),
        ]
        return self.run(command)

    def extract_audio(self, source: str | Path, output: str | Path, *, overwrite: bool = False) -> CommandResult:
        """Extract normalized mono WAV audio from a video or audio file."""
        return self.prepare_transcription_wav(source, output, overwrite=overwrite)

    def thumbnail(self, source: str | Path, output: str | Path, *, timestamp: str = "00:00:01", overwrite: bool = False) -> CommandResult:
        """Extract a single thumbnail image from a video."""
        source_path = self._require_file(source)
        output_path = self._prepare_output(output, overwrite=overwrite)
        command = [
            self.ffmpeg_bin,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-ss",
            timestamp,
            "-i",
            str(source_path),
            "-frames:v",
            "1",
            str(output_path),
        ]
        return self.run(command)

    def extract_frame(self, source: str | Path, output: str | Path, *, frame_number: int, overwrite: bool = False) -> CommandResult:
        """Extract one frame by zero-based frame number."""
        if frame_number < 0:
            raise ValueError("frame_number must be zero or greater")
        source_path = self._require_file(source)
        output_path = self._prepare_output(output, overwrite=overwrite)
        command = [
            self.ffmpeg_bin,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-i",
            str(source_path),
            "-vf",
            f"select=eq(n\\,{frame_number})",
            "-frames:v",
            "1",
            str(output_path),
        ]
        return self.run(command)

    def waveform(self, source: str | Path, output: str | Path, *, width: int = 1280, height: int = 240, overwrite: bool = False) -> CommandResult:
        """Generate a waveform image for an audio or video file."""
        source_path = self._require_file(source)
        output_path = self._prepare_output(output, overwrite=overwrite)
        command = [
            self.ffmpeg_bin,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-i",
            str(source_path),
            "-filter_complex",
            f"aformat=channel_layouts=mono,showwavespic=s={width}x{height}",
            "-frames:v",
            "1",
            str(output_path),
        ]
        return self.run(command)

    def spectrogram(self, source: str | Path, output: str | Path, *, width: int = 1280, height: int = 720, overwrite: bool = False) -> CommandResult:
        """Generate a spectrogram image for an audio or video file."""
        source_path = self._require_file(source)
        output_path = self._prepare_output(output, overwrite=overwrite)
        command = [
            self.ffmpeg_bin,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-i",
            str(source_path),
            "-lavfi",
            f"showspectrumpic=s={width}x{height}:legend=disabled",
            "-frames:v",
            "1",
            str(output_path),
        ]
        return self.run(command)

    def split_audio_chunks(self, source: str | Path, output_pattern: str | Path, *, seconds: int = 300, overwrite: bool = False) -> CommandResult:
        """Split audio into deterministic time chunks."""
        if seconds <= 0:
            raise ValueError("seconds must be greater than zero")
        source_path = self._require_file(source)
        output_path = self._prepare_output(output_pattern, overwrite=overwrite, allow_pattern=True)
        command = [
            self.ffmpeg_bin,
            "-hide_banner",
            "-y" if overwrite else "-n",
            "-i",
            str(source_path),
            "-f",
            "segment",
            "-segment_time",
            str(seconds),
            "-c",
            "copy",
            str(output_path),
        ]
        return self.run(command)

    @staticmethod
    def _require_file(path: str | Path) -> Path:
        candidate = Path(path)
        if not candidate.is_file():
            raise FileNotFoundError(f"Media file not found: {candidate}")
        return candidate

    @staticmethod
    def _prepare_output(path: str | Path, *, overwrite: bool, allow_pattern: bool = False) -> Path:
        output_path = Path(path)
        if output_path.exists() and not overwrite:
            raise FileExistsError(f"Output already exists: {output_path}")
        if not allow_pattern:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path


def _optional_float(value: object) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    try:
        return None if value is None else int(value)
    except (TypeError, ValueError):
        return None

