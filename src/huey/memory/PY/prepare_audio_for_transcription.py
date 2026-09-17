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
    parser = argparse.ArgumentParser(
        description="Prepare an audio fixture as mono 16 kHz transcription WAV."
    )
    parser.add_argument(
        "source",
        help="Path to the source MP3, WAV, FLAC, AAC, or Opus file.",
    )
    parser.add_argument(
        "destination",
        nargs="?",
        help=(
            "Optional legacy output destination. If it has a file suffix it is "
            "treated as the prepared WAV path; otherwise it is treated as an "
            "output directory."
        ),
    )
    parser.add_argument("--output", help="Explicit path for the prepared WAV output.")
    parser.add_argument(
        "--output-dir",
        help="Directory for the prepared WAV output.",
    )
    parser.add_argument(
        "--manifest",
        help=(
            "Optional manifest JSON path. If a directory-like path is supplied, "
            "the manifest is written there as <output>.manifest.json."
        ),
    )
    parser.add_argument("--overwrite", action="store_true", help="Allow overwrite")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    return parser


def _default_output_path(source: Path, *, output_dir: Path | None = None) -> Path:
    directory = output_dir if output_dir is not None else source.parent
    return directory / f"{source.stem}.prepared.wav"


def _resolve_output_path(
    source: Path,
    *,
    destination: str | None,
    output: str | None,
    output_dir: str | None,
) -> Path:
    selected = [
        label
        for label, value in (
            ("destination", destination),
            ("--output", output),
            ("--output-dir", output_dir),
        )
        if value
    ]
    if len(selected) > 1:
        raise ValueError("Choose only one of destination, --output, or --output-dir.")
    if output:
        return Path(output).expanduser().resolve()
    if output_dir:
        return _default_output_path(
            source,
            output_dir=Path(output_dir).expanduser().resolve(),
        )
    if destination:
        legacy_path = Path(destination).expanduser().resolve()
        if legacy_path.suffix:
            return legacy_path
        return _default_output_path(source, output_dir=legacy_path)
    return _default_output_path(source)


def _resolve_manifest_path(
    manifest: str | None,
    *,
    output_path: Path,
) -> Path | None:
    if manifest is None:
        return None
    manifest_path = Path(manifest).expanduser().resolve()
    if manifest_path.suffix:
        return manifest_path
    return manifest_path / f"{output_path.stem}.manifest.json"


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = Path(args.source).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Source audio file does not exist: {source}")
        output = _resolve_output_path(
            source,
            destination=args.destination,
            output=args.output,
            output_dir=args.output_dir,
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
        manifest_path = _resolve_manifest_path(args.manifest, output_path=output)
        if manifest_path is not None:
            manifest.write_json(manifest_path, overwrite=args.overwrite)
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    prepared = Path(manifest.artifacts[0].path)
    payload = {
        "schema": "huey.audio.preparation.result",
        "source_path": str(source),
        "output_path": str(prepared),
        "exists": prepared.exists(),
        "overwrite": args.overwrite,
        "manifest_path": str(manifest_path) if manifest_path is not None else None,
        "manifest": manifest.to_dict(),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Prepared transcription WAV: {prepared}")
        if manifest_path is not None:
            print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
