#!/usr/bin/env python3
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.09.2025
# ==================================================
"""Utility to update /etc/apt/sources.list to Debian Trixie."""

import os
import re
import shutil
import sys

SOURCE_FILE = "/etc/apt/sources.list"
BACKUP_FILE = SOURCE_FILE + ".bak"

APT_LINE_RE = re.compile(r'^(\s*deb(?:-src)?(?:\s+\[.*?\])?\s+\S+\s+)(\S+)(.*)$')


def convert_line(line: str) -> str:
    """Replace the distribution name in a sources.list line with 'trixie'."""
    if line.lstrip().startswith("#"):
        return line
    m = APT_LINE_RE.match(line)
    if not m:
        return line
    prefix, dist, rest = m.groups()
    if dist.startswith("trixie"):
        return line
    if "-" in dist:
        _, suffix = dist.split("-", 1)
        new_dist = f"trixie-{suffix}"
    else:
        new_dist = "trixie"
    return f"{prefix}{new_dist}{rest}"


def main() -> None:
    if os.geteuid() != 0:
        print("This script must be run as root.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(SOURCE_FILE):
        print(f"{SOURCE_FILE} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Creating backup: {BACKUP_FILE}")
    shutil.copyfile(SOURCE_FILE, BACKUP_FILE)

    with open(SOURCE_FILE, "r", encoding="utf-8") as fh:
        lines = [convert_line(line) for line in fh]

    with open(SOURCE_FILE, "w", encoding="utf-8") as fh:
        fh.writelines(lines)

    print("sources.list updated to Trixie")


if __name__ == "__main__":
    main()
