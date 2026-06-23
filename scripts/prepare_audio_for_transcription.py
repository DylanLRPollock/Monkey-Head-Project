"""Fixed wrapper for Huey speech-pipeline audio preparation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from huey.media.speech_pipeline import prepare_audio_for_transcription


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare audio for transcription")
    parser.add_argument("source", help="Source audio path")
    parser.add_argument("--output", help="Target output path")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwrite")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source audio file does not exist: {source}")
    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else source.with_name(f"{source.stem}.prepared.wav")
    )
    if output.exists() and not args.overwrite:
        raise FileExistsError(
            f"Refusing to overwrite existing output without --overwrite: {output}"
        )
    manifest = prepare_audio_for_transcription(
        source,
        output,
        overwrite=args.overwrite,
    )
    prepared = Path(manifest.artifacts[0].path)
    payload = {
        "source_path": str(source),
        "output_path": str(prepared),
        "exists": Path(prepared).exists(),
        "overwrite": args.overwrite,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
