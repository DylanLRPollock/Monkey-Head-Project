#!/usr/bin/env python3
"""Decompress audio files to FLAC using ffmpeg."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Decompress audio files to FLAC using ffmpeg."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Audio files or directories containing audio files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory. Defaults to input file directory.",
    )
    return parser


def iter_audio_files(paths: list[Path]) -> list[Path]:
    audio_files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for ext in ("*.mp3", "*.aac", "*.m4a", "*.ogg", "*.wav", "*.wma", "*.flac"):
                audio_files.extend(sorted(path.glob(ext)))
        elif path.is_file():
            audio_files.append(path)
    return audio_files


def decompress_file(input_path: Path, output_dir: Path | None) -> None:
    target_dir = output_dir if output_dir is not None else input_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{input_path.stem}.flac"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vn",
        "-c:a",
        "flac",
        str(output_path),
    ]

    subprocess.run(cmd, check=True)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    audio_files = iter_audio_files(args.inputs)
    if not audio_files:
        parser.error("No audio files found in the provided inputs.")

    for audio_file in audio_files:
        decompress_file(audio_file, args.output_dir)


if __name__ == "__main__":
    main()
