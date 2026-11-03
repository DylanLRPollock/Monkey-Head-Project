"""Report Ruff diagnostics without changing the lint enforcement gate."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    command = [
        "ruff",
        "check",
        "--output-format",
        "json",
        "src",
        "tests",
        "scripts",
        "conftest.py",
    ]
    result = subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=180
    )
    if result.returncode not in (0, 1):
        print("Ruff could not produce diagnostics:", result.stderr, file=sys.stderr)
        return result.returncode or 1

    data = json.loads(result.stdout)
    if not isinstance(data, list):
        print("Unexpected Ruff JSON output", file=sys.stderr)
        return 2

    Path("ruff-diagnostics.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    counts = Counter(str(item.get("code")) for item in data)
    print(f"Remaining Ruff diagnostics: {len(data)}")
    for rule, count in counts.most_common():
        print(f"  {rule}: {count}")
    # Reporting never changes the enforcement result: make lint remains a gate.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
