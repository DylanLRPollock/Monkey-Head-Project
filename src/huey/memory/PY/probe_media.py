"""Fixed wrapper for Huey media probing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from huey.media.media_manager import probe_media


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe media metadata")
    parser.add_argument("path", help="Path to the media file")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(args.path).expanduser().resolve()
    result = probe_media(source)
    payload = {
        "path": str(result.path),
        "format_name": result.format_name,
        "duration_seconds": result.duration_seconds,
        "bit_rate": result.bit_rate,
        "size_bytes": result.size_bytes,
        "streams": result.streams,
        "raw": result.raw,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True, default=str))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
