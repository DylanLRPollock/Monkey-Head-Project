# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Example Web Search module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Perform a simple DuckDuckGo search and print the title of the first result."""

from __future__ import annotations

import argparse
import re
import requests


def search(query: str) -> str:
    """Return the title of the first search result."""

    url = "https://duckduckgo.com/html/"
    try:
        resp = requests.get(url, params={"q": query}, timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover - network failures
        return f"Search failed: {exc}"
    m = re.search(r"<a[^>]+class=\"result__a\"[^>]*>(.*?)</a>", resp.text)
    return m.group(1) if m else "No results"


def main() -> None:
    parser = argparse.ArgumentParser(description="DuckDuckGo search")
    parser.add_argument("query", type=str)
    args = parser.parse_args()
    title = search(args.query)
    print(title)


if __name__ == "__main__":  # pragma: no cover - example script
    main()

