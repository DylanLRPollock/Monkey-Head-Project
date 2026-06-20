# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Example Llm module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
"""Demonstration of using :class:`~huey.os.ai_processor.AIProcessor`."""

from __future__ import annotations

import argparse

from huey.os.ai_processor import AIProcessor


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple AIProcessor demo")
    parser.add_argument("text", type=str, help="Input text to process")
    args = parser.parse_args()

    proc = AIProcessor()
    processed = proc.process_data(args.text)
    stats = proc.analyze_data(args.text)
    print(f"Processed: {processed}")
    print(f"Length: {stats['length']}")


if __name__ == "__main__":  # pragma: no cover - example script
    main()
