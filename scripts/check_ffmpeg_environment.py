"""Fixed wrapper for Huey FFmpeg environment validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from huey.media.ffmpeg_validator import validate_media_environment


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate FFmpeg availability")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when FFmpeg is unavailable",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = validate_media_environment()
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(payload)
    if args.strict and not payload.get("ready"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
