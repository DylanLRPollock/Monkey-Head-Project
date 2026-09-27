#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Monkey Head Project
# By: Dylan L.R. Pollock
# Website: https://dlrp.ca
# GitHub: https://github.com/DylanLRPollock/Monkey-Head-Project
# HueyOS: Chapter Splitter module (huey/memory/PY)
# License: GPL-3.0 — https://opensource.org/license/gpl-3-0
# Updated: 2026-09-27
#
# SPDX-License-Identifier: GPL-3.0-only

"""Split a text document into chapter files.

Requires Python 3.10 or later. Uses only the standard library.

The default pattern recognizes headings such as:
    CHAPTER
    CHAPTER 1
    Chapter 12: A New Beginning
    CHAPTER IV
    Chapter IX — The Journey
    PROLOGUE
    EPILOGUE

Chapter headings are retained. Text before the first chapter can be
saved separately, discarded, or prepended to the first chapter.
"""

from __future__ import annotations

import argparse
import codecs
import logging
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Literal


LOGGER = logging.getLogger(__name__)

# Expanded to catch Prologue, Epilogue, and spelled-out numbers (e.g., "One")
DEFAULT_PATTERN = (
    r"^[ \t]*(?:CHAPTER|PROLOGUE|EPILOGUE)"
    r"(?:[ \t]+(?:[0-9]+|[IVXLCDM]+|[A-Za-z]+)"
    r"(?=[ \t.:—–-]|$)[^\n]*)?"
    r"[ \t]*$"
)

# Preset for Markdown ATX headings (e.g., "# Chapter 1", "## Prologue")
MARKDOWN_PATTERN = (
    r"^[ \t]*#{1,6}[ \t]+(?:CHAPTER|PROLOGUE|EPILOGUE)"
    r"(?:[ \t]+(?:[0-9]+|[IVXLCDM]+|[A-Za-z]+)"
    r"(?=[ \t.:—–-]|$)[^\n]*)?"
    r"[ \t]*$"
)

PRESETS = {
    "default": DEFAULT_PATTERN,
    "markdown": MARKDOWN_PATTERN,
}

PreambleMode = Literal["separate", "prepend", "discard"]


class ChapterSplitError(Exception):
    """Raised when the document cannot be split into chapters."""


def _format_section(text: str) -> str:
    """Remove blank boundary lines and ensure a final newline."""
    return text.strip("\n") + "\n"


def _slugify(value: str, max_length: int = 50) -> str:
    """Convert a string to a safe, URL-friendly filename slug."""
    # Normalize unicode characters (e.g., convert 'é' to 'e')
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    slug = re.sub(r"[-\s]+", "-", value).strip("-_")
    return slug[:max_length].strip("-")


def _write_atomic(
    destination: Path,
    text: str,
    *,
    encoding: str,
    overwrite: bool,
) -> None:
    """Publish a fully written file without exposing partial contents."""
    temporary: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            errors="strict",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())

        if overwrite:
            os.replace(temporary, destination)
        else:
            os.link(temporary, destination)

    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as exc:
                LOGGER.warning(
                    "Could not remove temporary file %s: %s",
                    temporary,
                    exc,
                )


def split_chapters(
    input_file: str | Path,
    output_dir: str | Path,
    *,
    pattern: str = DEFAULT_PATTERN,
    input_encoding: str = "utf-8-sig",
    output_encoding: str = "utf-8",
    preamble: PreambleMode = "separate",
    ignore_case: bool = True,
    overwrite: bool = False,
    dry_run: bool = False,
    name_files: bool = False,
    generate_toc: bool = False,
) -> list[Path]:
    """Split a document and return the written or planned output paths."""
    if preamble not in {"separate", "prepend", "discard"}:
        raise ValueError("preamble must be 'separate', 'prepend', or 'discard'.")

    for encoding in (input_encoding, output_encoding):
        try:
            codecs.lookup(encoding)
        except LookupError as exc:
            raise ValueError(f"Unknown encoding: {encoding!r}") from exc

    flags = re.MULTILINE
    if ignore_case:
        flags |= re.IGNORECASE

    try:
        heading_regex = re.compile(pattern, flags)
    except re.error as exc:
        raise ValueError(f"Invalid chapter pattern: {exc}") from exc

    source = Path(input_file).expanduser().resolve(strict=True)
    destination = Path(output_dir).expanduser().resolve()

    if not source.is_file():
        raise ValueError(f"Input is not a regular file: {source}")

    with source.open("r", encoding=input_encoding, errors="strict", newline=None) as handle:
        content = handle.read()

    if not content.strip():
        raise ChapterSplitError(f"Input file is empty: {source}")

    matches = list(heading_regex.finditer(content))

    if not matches:
        raise ChapterSplitError(
            "No chapter headings matched. Check the document format "
            "or supply a custom pattern."
        )

    for match in matches:
        if match.start() == match.end():
            raise ValueError("The chapter pattern produced an empty match.")
        if match.start() > 0 and content[match.start() - 1] != "\n":
            raise ValueError(
                "Chapter matches must begin at line boundaries. "
                "Use an anchored pattern such as '^CHAPTER...'."
            )

    width = max(3, len(str(len(matches))))
    outputs: list[tuple[Path, str]] = []
    toc_lines: list[str] = ["# Table of Contents\n"]

    intro = content[:matches[0].start()]

    if intro.strip() and preamble == "separate":
        outputs.append((destination / "preamble.txt", _format_section(intro)))
        toc_lines.append("- [Preamble](preamble.txt)")

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        section = content[match.start():end]

        if index == 0 and preamble == "prepend" and intro.strip():
            section = intro + section

        # Determine filename
        heading_text = match.group(0).strip()
        # Strip markdown hashes if present for cleaner slugs
        clean_heading = re.sub(r"^#+\s*", "", heading_text) 
        
        if name_files:
            slug = _slugify(clean_heading)
            filename = f"chapter_{index + 1:0{width}d}_{slug}.txt" if slug else f"chapter_{index + 1:0{width}d}.txt"
        else:
            filename = f"chapter_{index + 1:0{width}d}.txt"

        outputs.append((destination / filename, _format_section(section)))
        toc_lines.append(f"- [{clean_heading}]({filename})")

    if generate_toc:
        outputs.append((destination / "toc.md", "\n".join(toc_lines) + "\n"))

    if destination.exists() and not destination.is_dir():
        raise NotADirectoryError(f"Output path is not a directory: {destination}")

    # Validate collisions
    for target, text in outputs:
        if target.resolve() == source:
            raise ValueError(f"Output would replace the input: {target}")
        if target.exists() and target.samefile(source):
            raise ValueError(f"Output refers to the input file: {target}")
        if target.is_symlink():
            raise ValueError(f"Refusing to write through an output symlink: {target}")
        if target.exists():
            if not target.is_file():
                raise FileExistsError(f"Output is not a regular file: {target}")
            if not overwrite:
                raise FileExistsError(
                    f"Output already exists: {target}. "
                    "Use overwrite=True or --overwrite to replace it."
                )
        text.encode(output_encoding, errors="strict")

    if not dry_run:
        destination.mkdir(parents=True, exist_ok=True)
        for target, text in outputs:
            _write_atomic(target, text, encoding=output_encoding, overwrite=overwrite)
            LOGGER.info("Saved %s", target)
    else:
        for target, _ in outputs:
            LOGGER.info("Would save %s", target)

    return [target for target, _ in outputs]


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(
        description="Split a text document into chapter files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("input_file", type=Path, help="Source text file")
    parser.add_argument("output_dir", type=Path, help="Output directory")
    
    pattern_group = parser.add_mutually_exclusive_group()
    pattern_group.add_argument(
        "--pattern",
        default=DEFAULT_PATTERN,
        help="Regular expression matching chapter headings",
    )
    pattern_group.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        help="Use a built-in regex preset (overrides --pattern)",
    )

    parser.add_argument("--input-encoding", default="utf-8-sig", help="Source text encoding")
    parser.add_argument("--output-encoding", default="utf-8", help="Generated file encoding")
    parser.add_argument(
        "--preamble",
        choices=("separate", "prepend", "discard"),
        default="separate",
        help="Handling for text before the first chapter",
    )
    parser.add_argument("--case-sensitive", action="store_true", help="Make heading detection case-sensitive")
    parser.add_argument("--name-files", action="store_true", help="Append slugified chapter titles to filenames")
    parser.add_argument("--generate-toc", action="store_true", help="Generate a toc.md file linking to chapters")
    parser.add_argument("--overwrite", action="store_true", help="Replace existing generated files")
    parser.add_argument("--dry-run", action="store_true", help="Validate and list outputs without creating files")

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("-v", "--verbose", action="store_true", help="Show each output path")
    verbosity.add_argument("-q", "--quiet", action="store_true", help="Show errors only")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI: 0 = success, 1 = failure, 2 = invalid CLI usage."""
    args = build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    active_pattern = PRESETS[args.preset] if args.preset else args.pattern

    try:
        paths = split_chapters(
            args.input_file,
            args.output_dir,
            pattern=active_pattern,
            input_encoding=args.input_encoding,
            output_encoding=args.output_encoding,
            preamble=args.preamble,
            ignore_case=not args.case_sensitive,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            name_files=args.name_files,
            generate_toc=args.generate_toc,
        )
    except (ChapterSplitError, OSError, UnicodeError, ValueError) as exc:
        LOGGER.error("%s", exc)
        return 1
    except KeyboardInterrupt:
        LOGGER.error("Interrupted; some output files may already exist.")
        return 130

    if not args.quiet:
        if args.dry_run:
            print(f"Dry run: {len(paths)} file(s) planned.")
            for path in paths:
                print(path)
        else:
            print(f"Saved {len(paths)} file(s) to '{args.output_dir.expanduser().resolve()}'.")

    return 0


if __name__ == "__main__":
    sys.exit(main())