#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Monkey Head Project
# By: Dylan L.R. Pollock
# Website: https://dlrp.ca
# GitHub: https://github.com/DylanLRPollock/Monkey-Head-Project
# HueyOS: Unified File Conversion Module
# License: GPL-3.0 — https://opensource.org/license/gpl-3-0
# Updated: 2026-09-27

"""Unified media conversion and PDF text extraction.

Requires Python 3.10+.
PDF extraction requires pypdf.

PDF outputs are published atomically per file, not as a whole batch.
Without overwrite permission, publication requires hard-link support.
Image-only PDFs require OCR, which this module does not perform.
"""

from __future__ import annotations

import argparse
import importlib
import logging
import os
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence


LOGGER = logging.getLogger(__name__)

# Preserves the original project's import-root assumption.
_ROOT = Path(__file__).resolve().parents[1]

MEDIA_COMMANDS = {
    "avi2mkv": "scripts.media.convert_avi_to_mkv",
    "mkv2mp4": "huey.media.convert_mkv_to_mp4",
    "png2jpeg": "huey.media.convert_png_to_jpeg",
    "video2gif": "huey.media.convert_video_to_gif",
}


class ConversionError(Exception):
    """A conversion or output publication failed."""


class DependencyError(ConversionError):
    """A required dependency could not be loaded."""


@dataclass
class BatchResult:
    """Results for a completed PDF batch."""

    written: list[Path] = field(default_factory=list)
    failed: dict[Path, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.failed


def _load_pdf_reader() -> Any:
    """Import pypdf only when PDF functionality is requested."""
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError as exc:
        if exc.name == "pypdf":
            raise DependencyError(
                "PDF extraction requires pypdf. Install it in this "
                "Python environment with: python -m pip install pypdf"
            ) from exc
        raise DependencyError(
            f"A dependency needed by pypdf is missing: {exc.name}"
        ) from exc
    except ImportError as exc:
        raise DependencyError(f"Could not import pypdf: {exc}") from exc

    return PdfReader


def convert_pdf_to_text(
    path: str | Path,
    *,
    allow_empty: bool = False,
) -> str:
    """Extract PDF text, or raise ConversionError.

    Empty extraction is rejected by default to make scanned or otherwise
    non-extractable documents visible as failures rather than empty outputs.
    """
    reader_class = _load_pdf_reader()
    source = Path(path).expanduser()

    try:
        if not source.is_file():
            raise ConversionError(
                f"PDF input is not a regular file: {source}"
            )

        with source.open("rb") as handle:
            reader = reader_class(handle)

            # Some encrypted PDFs can be opened with an empty password.
            if reader.is_encrypted and not reader.decrypt(""):
                raise ConversionError(
                    f"PDF requires a password: {source}. "
                    "Password-protected extraction is not supported."
                )

            pages: list[str] = []

            for number, page in enumerate(reader.pages, start=1):
                try:
                    pages.append(page.extract_text() or "")
                except Exception as exc:
                    raise ConversionError(
                        f"Could not extract page {number} of "
                        f"{source}: {exc}"
                    ) from exc

        # Separate pages so words at adjacent page boundaries do not merge.
        text = "\n\n".join(pages)

        if not text.strip() and not allow_empty:
            raise ConversionError(
                f"No extractable text found in {source}. "
                "The document may require OCR; use --allow-empty "
                "only if an empty result is acceptable."
            )

        return text

    except ConversionError:
        raise
    except Exception as exc:
        # Third-party PDF parsing may raise several exception types.
        # Do not catch BaseException: interrupts must still propagate.
        raise ConversionError(
            f"Could not read PDF {source}: {exc}"
        ) from exc


def save_text_to_file(
    text: str,
    file_path: str | Path,
    *,
    overwrite: bool = False,
) -> str:
    """Atomically publish UTF-8 text; return 'OK' or raise.

    No-overwrite publication uses an atomic hard-link operation.
    It intentionally has no unsafe check-then-rename fallback.
    """
    destination = Path(file_path).expanduser()
    temporary: Path | None = None

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)

        if destination.is_symlink():
            raise ConversionError(
                f"Refusing output symlink: {destination}"
            )

        if destination.exists():
            if not destination.is_file():
                raise ConversionError(
                    f"Output is not a regular file: {destination}"
                )
            if not overwrite:
                raise ConversionError(
                    f"Output already exists: {destination}. "
                    "Use --overwrite to replace it."
                )

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
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

        # The temporary file is closed before publication, including Windows.
        if overwrite:
            os.replace(temporary, destination)
        else:
            try:
                os.link(temporary, destination)
            except FileExistsError as exc:
                raise ConversionError(
                    f"Output already exists or was created concurrently: "
                    f"{destination}"
                ) from exc
            except OSError as exc:
                raise ConversionError(
                    f"Could not publish {destination} without overwriting: "
                    f"{exc}. No-overwrite mode requires hard-link support."
                ) from exc

        return "OK"

    except ConversionError:
        raise
    except (OSError, UnicodeError, ValueError) as exc:
        raise ConversionError(
            f"Could not save {destination}: {exc}"
        ) from exc
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


def process_pdf(
    pdf_path: str | Path,
    output_dir: str | Path,
    *,
    overwrite: bool = False,
    allow_empty: bool = False,
) -> Path:
    """Extract and save one PDF. Never save an extraction error as text."""
    source = Path(pdf_path).expanduser().resolve(strict=True)

    if source.suffix.lower() != ".pdf":
        raise ConversionError(f"Input must have a .pdf extension: {source}")

    destination = Path(output_dir).expanduser().resolve()
    target = destination / source.with_suffix(".txt").name

    if target.resolve() == source:
        raise ConversionError(f"Output would replace the source: {target}")

    if target.exists() and target.samefile(source):
        raise ConversionError(f"Output refers to the source: {target}")

    text = convert_pdf_to_text(source, allow_empty=allow_empty)
    save_text_to_file(text, target, overwrite=overwrite)
    return target


def process_pdfs_in_directory(
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    workers: int = 4,
    overwrite: bool = False,
    allow_empty: bool = False,
) -> BatchResult:
    """Convert immediate child PDFs and collect every worker outcome.

    Setup failures raise exceptions. Individual conversion failures are
    recorded in the returned result while other conversions continue.
    """
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 1:
        raise ValueError("workers must be a positive integer")

    _load_pdf_reader()

    source = Path(input_dir).expanduser().resolve(strict=True)
    destination = Path(output_dir).expanduser().resolve()

    if not source.is_dir():
        raise NotADirectoryError(f"Input is not a directory: {source}")

    pdf_files = sorted(
        (
            path
            for path in source.iterdir()
            if path.suffix.lower() == ".pdf" and path.is_file()
        ),
        key=lambda path: path.name,
    )

    if not pdf_files:
        raise ConversionError(f"No PDF files found in {source}")

    # Conservative across platforms: reject case-only name collisions even
    # on filesystems that permit them, before launching concurrent writers.
    names: dict[str, Path] = {}
    for pdf in pdf_files:
        key = pdf.with_suffix(".txt").name.casefold()
        if key in names:
            raise ConversionError(
                f"Conflicting output names for {names[key].name!r} "
                f"and {pdf.name!r}"
            )
        names[key] = pdf

    destination.mkdir(parents=True, exist_ok=True)
    result = BatchResult()
    executor = ThreadPoolExecutor(
        max_workers=min(workers, len(pdf_files))
    )

    try:
        futures = {
            executor.submit(
                process_pdf,
                pdf,
                destination,
                overwrite=overwrite,
                allow_empty=allow_empty,
            ): pdf
            for pdf in pdf_files
        }

        for future in as_completed(futures):
            pdf = futures[future]
            try:
                target = future.result()
            except Exception as exc:
                message = str(exc) or type(exc).__name__
                result.failed[pdf] = message
                LOGGER.error(
                    "Failed %s: %s",
                    pdf.name,
                    message,
                    exc_info=LOGGER.isEnabledFor(logging.DEBUG),
                )
            else:
                result.written.append(target)
                LOGGER.info("Saved %s", target)

    finally:
        # Cancel queued work on interruption. Running threads cannot be
        # forcibly stopped safely, so wait for them before returning.
        executor.shutdown(wait=True, cancel_futures=True)

    result.written.sort(key=lambda path: str(path))
    return result


def _normalize_exit_code(value: object) -> int:
    """Normalize legacy main() returns and SystemExit values."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value

    LOGGER.error("Legacy command returned a non-integer exit status: %s", value)
    return 1


def _run_legacy(command: str, arguments: Sequence[str]) -> int:
    """Run a legacy entry point and restore process-global import/CLI state.

    This adapter is intended for single-threaded CLI dispatch.
    Legacy code may have other process-global side effects.
    """
    original_argv = sys.argv
    original_path = sys.path[:]

    try:
        sys.argv = [f"{original_argv[0]} {command}", *arguments]

        if str(_ROOT) not in sys.path:
            sys.path.insert(0, str(_ROOT))

        module = importlib.import_module(MEDIA_COMMANDS[command])
        entry_point = getattr(module, "main", None)

        if not callable(entry_point):
            raise ConversionError(
                f"Legacy module {module.__name__} has no callable main()"
            )

        return _normalize_exit_code(entry_point())

    except SystemExit as exc:
        return _normalize_exit_code(exc.code)
    finally:
        sys.argv = original_argv
        sys.path[:] = original_path


def _positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "must be a positive integer"
        ) from exc

    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified file conversion utility for HueyOS.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "command",
        choices=[*MEDIA_COMMANDS, "pdf2txt"],
        help="Conversion type",
    )
    return parser


def build_pdf_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=f"{Path(sys.argv[0]).name} pdf2txt",
        description="Extract text from PDFs in a directory (non-recursive).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        allow_abbrev=False,
    )
    parser.add_argument(
        "-i", "--input", type=Path, default=Path("pdf-input"),
        help="Input directory",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=Path("pdf-output"),
        help="Output directory",
    )
    parser.add_argument(
        "--workers", type=_positive_integer, default=4,
        help="Maximum concurrent conversions",
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Replace existing output files",
    )
    parser.add_argument(
        "--allow-empty", action="store_true",
        help="Allow PDFs with no extractable text",
    )

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show progress and debug tracebacks",
    )
    verbosity.add_argument(
        "-q", "--quiet", action="store_true",
        help="Show errors only",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Return 0 on success, 1 on failure, 2 on CLI errors, 130 on interrupt."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    try:
        # Parse just the command. Forward every remaining legacy argument
        # unchanged, including --help; parse PDF arguments strictly.
        command = build_parser().parse_args(arguments[:1]).command
        remaining = arguments[1:]

        if command in MEDIA_COMMANDS:
            return _run_legacy(command, remaining)

        args = build_pdf_parser().parse_args(remaining)
        logging.getLogger().setLevel(
            logging.DEBUG if args.verbose
            else logging.ERROR if args.quiet
            else logging.WARNING
        )

        result = process_pdfs_in_directory(
            args.input,
            args.output,
            workers=args.workers,
            overwrite=args.overwrite,
            allow_empty=args.allow_empty,
        )

        if not args.quiet:
            print(
                f"Converted {len(result.written)} PDF(s); "
                f"failed {len(result.failed)}."
            )

        return 0 if result.ok else 1

    except SystemExit as exc:
        # argparse uses SystemExit for help and invalid arguments.
        return _normalize_exit_code(exc.code)
    except KeyboardInterrupt:
        LOGGER.error(
            "Interrupted. Some output files may already have been saved."
        )
        return 130
    except (ConversionError, OSError, ValueError, ImportError) as exc:
        LOGGER.error(
            "%s",
            exc,
            exc_info=LOGGER.isEnabledFor(logging.DEBUG),
        )
        return 1
    except Exception:
        # Last-resort CLI boundary: preserve a traceback for unexpected bugs.
        LOGGER.exception("Unexpected conversion failure")
        return 1


if __name__ == "__main__":
    sys.exit(main())