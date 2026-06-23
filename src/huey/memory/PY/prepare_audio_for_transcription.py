#!/usr/bin/env python3
"""CLI wrapper for HueyOS transcription audio preparation."""

from __future__ import annotations

import argparse
import json
import sys

from huey.media.speech_pipeline import prepare_audio_for_transcription


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Prepare an audio fixture as mono 16 kHz transcription WAV."
    )
    parser.add_argument(
        "source", help="Path to the source MP3, WAV, FLAC, AAC, or Opus file."
    )
    parser.add_argument(
        "output_dir", help="Directory for derived WAV and manifest outputs."
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow derived outputs to be overwritten.",
    )
    parser.add_argument(
        "--json", action="store_true", help="Print the manifest as JSON."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Prepare audio and report the generated manifest."""
    args = build_parser().parse_args(argv)
    try:
        manifest = prepare_audio_for_transcription(
            args.source, args.output_dir, overwrite=args.overwrite
        )
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(manifest.to_dict(), indent=2, sort_keys=True))
    else:
        artifact = manifest.artifacts[0]
        print(f"Prepared transcription WAV: {artifact.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
