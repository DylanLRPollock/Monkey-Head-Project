#!/usr/bin/env python3
"""Convert AVI files to MKV using ffmpeg."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert AVI files to MKV using ffmpeg."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="AVI files or directories containing AVI files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output directory. Defaults to input file directory.",
    )
    parser.add_argument(
        "--reencode",
        action="store_true",
        help="Re-encode video/audio instead of stream copying.",
    )
    return parser


def iter_avi_files(paths: list[Path]) -> list[Path]:
    avi_files: list[Path] = []
    for path in paths:
        if path.is_dir():
            avi_files.extend(sorted(path.glob("*.avi")))
        elif path.is_file() and path.suffix.lower() == ".avi":
            avi_files.append(path)
    return avi_files


def convert_file(input_path: Path, output_dir: Path | None, reencode: bool) -> None:
    target_dir = output_dir if output_dir is not None else input_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{input_path.stem}.mkv"

    if reencode:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-c",
            "copy",
            str(output_path),
        ]

    subprocess.run(cmd, check=True)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    avi_files = iter_avi_files(args.inputs)
    if not avi_files:
        parser.error("No AVI files found in the provided inputs.")

    for avi_file in avi_files:
        convert_file(avi_file, args.output_dir, args.reencode)


if __name__ == "__main__":
    main()
