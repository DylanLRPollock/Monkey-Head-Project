#!/usr/bin/env python3
"""CLI wrapper for HueyOS FFmpeg environment validation."""

from __future__ import annotations

import argparse
import sys

from huey.media.ffmpeg_validator import validate_ffmpeg_environment


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Check FFmpeg readiness for HueyOS V1 media preparation."
    )
    parser.add_argument(
        "--ffmpeg-bin", default="ffmpeg", help="FFmpeg binary name or path."
    )
    parser.add_argument(
        "--ffprobe-bin", default="ffprobe", help="ffprobe binary name or path."
    )
    parser.add_argument(
        "--json", action="store_true", help="Print machine-readable JSON."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the FFmpeg readiness check."""
    args = build_parser().parse_args(argv)
    report = validate_ffmpeg_environment(
        ffmpeg_bin=args.ffmpeg_bin, ffprobe_bin=args.ffprobe_bin
    )
    if args.json:
        print(report.to_json())
    else:
        status = "ready" if report.v1_ready else "not ready"
        print(f"FFmpeg environment: {status}")
        for note in report.notes:
            print(f"- {note}")
    return 0 if report.v1_ready else 2


if __name__ == "__main__":
    sys.exit(main())
