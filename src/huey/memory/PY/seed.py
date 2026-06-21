"""Generate safe seed data for the Command Center dashboard."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from huey.media.ffmpeg_validator import check_ffmpeg


def build_seed_data(project_root: Path) -> dict[str, Any]:
    """Return read-only dashboard seed data."""

    project_root = Path(project_root)
    ffmpeg_report = check_ffmpeg().to_json_dict()
    proof_dirs = ["src/huey/media", "src/huey/v1", "tests"]
    return {
        "schema": "huey.command_center.seed",
        "generated_at": datetime.now(UTC).isoformat(),
        "project_root": str(project_root),
        "v1_proof_path": [
            "known MP3 fixture",
            "FFmpeg/local audio preparation",
            "local transcription",
            "mock-first response bridge",
            "structured log",
        ],
        "deferred_by_default": [
            "live microphone capture",
            "wake word",
            "Huey Body actuation",
            "GPIO control",
            "autonomous governance enforcement",
        ],
        "paths": {path: (project_root / path).exists() for path in proof_dirs},
        "ffmpeg": ffmpeg_report,
    }


def write_seed_data(project_root: Path, output_path: Path, *, overwrite: bool = False) -> dict[str, Any]:
    """Write seed data to JSON without overwriting by default."""

    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output exists and overwrite is false: {output_path}")
    data = build_seed_data(project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return data


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    data = (
        write_seed_data(args.project_root, args.output, overwrite=args.overwrite)
        if args.output
        else build_seed_data(args.project_root)
    )
    print(json.dumps(data, indent=2, sort_keys=True) if args.json or not args.output else f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

