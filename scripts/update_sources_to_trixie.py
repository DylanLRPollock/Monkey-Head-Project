#!/usr/bin/env python3
# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated:   06.09.2025
# ==================================================
"""Utility to update /etc/apt/sources.list to a specified Debian release.

By default the script switches all repository entries to ``trixie`` but a
different release codename (e.g. ``testing``) may be supplied as the first
command line argument.
"""

import os
import re
import shutil
import sys

SOURCE_FILE = "/etc/apt/sources.list"
BACKUP_FILE = SOURCE_FILE + ".bak"

DEFAULT_RELEASE = "trixie"

APT_LINE_RE = re.compile(r"^(\s*deb(?:-src)?(?:\s+\[.*?\])?\s+\S+\s+)(\S+)(.*)$")


def convert_line(line: str, release: str) -> str:
    """Replace the distribution name in a sources.list line with ``release``."""
    if line.lstrip().startswith("#"):
        return line
    m = APT_LINE_RE.match(line)
    if not m:
        return line
    prefix, dist, rest = m.groups()
    if dist.startswith(release):
        return line
    if "-" in dist:
        _, suffix = dist.split("-", 1)
        new_dist = f"{release}-{suffix}"
    else:
        new_dist = release
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

    release = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RELEASE

    with open(SOURCE_FILE, "r", encoding="utf-8") as fh:
        lines = [convert_line(line, release) for line in fh]

    with open(SOURCE_FILE, "w", encoding="utf-8") as fh:
        fh.writelines(lines)

    print(f"sources.list updated to {release}")


if __name__ == "__main__":
    main()
