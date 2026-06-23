"""Convert video files to GIF using FFmpeg."""

from __future__ import annotations

import argparse
from pathlib import Path

from huey.media.media_manager import _coerce_path, _ensure_source, _run_ffmpeg


def convert_video_to_gif(
    video_file: str | Path,
    output_file: str | Path,
    fps: int = 10,
    *,
    scale_width: int = 320,
    overwrite: bool = True,
) -> Path:
    """Convert ``video_file`` to a GIF preview."""

    source = _ensure_source(video_file)
    target = _coerce_path(output_file)
    target.parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(
        [
            "-i",
            str(source),
            "-vf",
            f"fps={fps},scale={scale_width}:-1:flags=lanczos",
            str(target),
        ],
        overwrite=overwrite,
    )
    return target


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description="Convert a video file to GIF.")
    parser.add_argument("video_file", help="Path to the input video file.")
    parser.add_argument("output_file", help="Path to the output GIF file.")
    parser.add_argument(
        "--fps",
        type=int,
        default=10,
        help="Frames per second for the GIF.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    args = build_parser().parse_args(argv)
    convert_video_to_gif(args.video_file, args.output_file, args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
