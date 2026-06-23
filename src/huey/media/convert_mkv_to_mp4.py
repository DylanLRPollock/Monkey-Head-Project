"""Convert MKV video files to MP4 using FFmpeg."""

from __future__ import annotations

import argparse
from pathlib import Path

from huey.media.media_manager import _coerce_path, _ensure_source, _run_ffmpeg


def convert_mkv_to_mp4(
    mkv_file: str | Path,
    output_file: str | Path,
    *,
    overwrite: bool = True,
) -> Path:
    """Convert an MKV video to MP4 without re-encoding."""

    source = _ensure_source(mkv_file)
    target = _coerce_path(output_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(
        ["-i", str(source), "-c", "copy", "-map", "0", str(target)],
        overwrite=overwrite,
    )
    return target


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description="Convert an MKV video to MP4.")
    parser.add_argument("mkv_file", help="Path to the input MKV file.")
    parser.add_argument("output_file", help="Path to the output MP4 file.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    convert_mkv_to_mp4(args.mkv_file, args.output_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
