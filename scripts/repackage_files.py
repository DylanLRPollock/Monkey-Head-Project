#!/usr/bin/env python3
"""Repackage files or directories into a new archive."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Repackage files or directories into an archive."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Files or directories to package.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output archive path (e.g. output.zip or output.tar.gz).",
    )
    parser.add_argument(
        "--format",
        choices=["zip", "tar", "gztar", "bztar", "xztar"],
        default=None,
        help="Archive format. Defaults to inferred from output extension.",
    )
    return parser


def create_archive(
    inputs: list[Path], output: Path, archive_format: str | None
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    if archive_format is None:
        suffixes = "".join(output.suffixes)
        format_map = {
            ".zip": "zip",
            ".tar": "tar",
            ".tar.gz": "gztar",
            ".tgz": "gztar",
            ".tar.bz2": "bztar",
            ".tar.xz": "xztar",
        }
        archive_format = format_map.get(suffixes)
        if archive_format is None:
            raise ValueError(
                "Unable to infer archive format from output extension. "
                "Specify --format explicitly."
            )

    staging_dir = output.parent / f"{output.stem}_package"
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True)

    for item in inputs:
        if not item.exists():
            raise FileNotFoundError(f"Input not found: {item}")
        destination = staging_dir / item.name
        if item.is_dir():
            shutil.copytree(item, destination)
        else:
            shutil.copy2(item, destination)

    shutil.make_archive(
        base_name=str(output.with_suffix("")),
        format=archive_format,
        root_dir=staging_dir,
    )

    shutil.rmtree(staging_dir)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    create_archive(args.inputs, args.output, args.format)


if __name__ == "__main__":
    main()
