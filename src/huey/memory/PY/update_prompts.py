# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Update Prompts module (huey/memory/PY)

from __future__ import annotations

import argparse
import csv
import re
import shutil
from pathlib import Path

DEFAULT_PROMPTS_FILE = Path("prompts") / "pygpt_prompts.csv"


def _rewrite_prompt(act: str, prompt: str) -> str:
    prompt_clean = re.sub(
        r"^I want you to act as an?[^\.]*\.\s*", "", prompt, flags=re.IGNORECASE
    )
    prompt_clean = re.sub(
        r"^I want you to act as[^\.]*\.\s*", "", prompt_clean, flags=re.IGNORECASE
    )
    prompt_clean = re.sub(
        r"\bI want you to\b", "You should", prompt_clean, flags=re.IGNORECASE
    )
    prefix = "You are "
    prefix += "an " if act and act[0].lower() in "aeiou" else "a "
    return prefix + act + ". " + " ".join(prompt_clean.split())


def rewrite_prompts(
    input_file: str | Path = DEFAULT_PROMPTS_FILE,
    output_file: str | Path | None = None,
    *,
    dry_run: bool = False,
    backup: bool = True,
) -> list[tuple[str, str, str]]:
    source_path = Path(input_file)
    target_path = Path(output_file) if output_file is not None else source_path

    with source_path.open(newline="", encoding="utf-8") as handle:
        lines = handle.readlines()

    if len(lines) < 2:
        raise ValueError("Prompt CSV must contain a comment line and a header row.")

    comment = lines[0].rstrip("\n")
    header = next(csv.reader([lines[1].strip()]))
    rows: list[tuple[str, str, str]] = []
    for raw_line in lines[2:]:
        line = raw_line.strip()
        if not line:
            continue
        row = next(csv.reader([line]))
        if len(row) < 3:
            continue
        act, prompt, for_devs = row[0], row[1], row[2]
        rows.append((act, _rewrite_prompt(act, prompt), for_devs))

    if dry_run:
        return rows

    if backup and target_path.resolve() == source_path.resolve():
        backup_path = source_path.with_suffix(source_path.suffix + ".bak")
        shutil.copy2(source_path, backup_path)

    with target_path.open("w", newline="", encoding="utf-8") as handle:
        handle.write(comment + "\n")
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)

    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rewrite prompt CSV records safely.")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_PROMPTS_FILE),
        help="Source CSV file to rewrite.",
    )
    parser.add_argument(
        "--output",
        help="Optional destination CSV file. Defaults to rewriting the input file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview the rewritten rows without modifying any files.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a .bak file when overwriting the source CSV.",
    )
    args = parser.parse_args(argv)

    rows = rewrite_prompts(
        args.input,
        args.output,
        dry_run=args.dry_run,
        backup=not args.no_backup,
    )
    print(f"Processed {len(rows)} prompt rows.")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual invocation
    raise SystemExit(main())
