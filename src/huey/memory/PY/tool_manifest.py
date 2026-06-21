"""Generate a safe read-only PyHuey tool manifest for HueyOS scripts."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    """PyHuey-visible tool descriptor."""

    name: str
    command: list[str]
    description: str
    read_only: bool = True
    deferred: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        """Return JSON-safe manifest data."""

        return {
            "name": self.name,
            "command": self.command,
            "description": self.description,
            "read_only": self.read_only,
            "deferred": self.deferred,
        }


def build_manifest() -> dict[str, Any]:
    """Build the default PyHuey tool manifest."""

    tools = [
        ToolSpec(
            name="check_ffmpeg_environment",
            command=["python", "scripts/check_ffmpeg_environment.py", "--json"],
            description="Report FFmpeg readiness for the HueyOS V1 proof path.",
        ),
        ToolSpec(
            name="command_center_seed",
            command=["python", "-m", "huey.apps.command_center.seed", "--json"],
            description="Emit read-only Command Center seed data.",
        ),
        ToolSpec(
            name="prepare_audio_for_transcription",
            command=["python", "scripts/prepare_audio_for_transcription.py"],
            description="Prepare a known local audio fixture for transcription.",
            read_only=False,
        ),
    ]
    return {
        "schema": "huey.pyhuey.tool_manifest",
        "policy": {
            "blocks_arbitrary_shell": True,
            "hardware_actions_deferred": True,
            "network_mutation_deferred": True,
        },
        "tools": [tool.to_json_dict() for tool in tools],
    }


def write_manifest(output_path: Path, *, overwrite: bool = False) -> dict[str, Any]:
    """Write the manifest JSON file."""

    output_path = Path(output_path)
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output exists and overwrite is false: {output_path}")
    manifest = build_manifest()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    manifest = write_manifest(args.output, overwrite=args.overwrite) if args.output else build_manifest()
    print(json.dumps(manifest, indent=2, sort_keys=True) if args.json or not args.output else f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

