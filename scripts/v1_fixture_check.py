#!/usr/bin/env python3
"""Verify registered V1 fixture checksums without running models or audio tools."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __name__ == "__main__":
    src = Path(__file__).resolve().parents[1] / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))

from huey.v1.fixture_registry import list_fixtures, verify_fixture


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--id", dest="fixture_id", help="Check one fixture ID")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        entries = list_fixtures(registry_path=args.registry)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Fixture registry error: {exc}\n")
    if args.fixture_id is not None:
        entries = [entry for entry in entries if entry.get("id") == args.fixture_id]
        if not entries:
            parser.exit(2, f"Unknown fixture ID: {args.fixture_id}\n")

    results: list[dict[str, object]] = []
    for entry in entries:
        try:
            verify_fixture(entry)
            results.append({"id": entry.get("id"), "ok": True, "error": None})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            results.append({"id": entry.get("id"), "ok": False, "error": str(exc)})

    payload = {
        "checked": len(results),
        "passed": sum(item["ok"] is True for item in results),
        "failed": sum(item["ok"] is False for item in results),
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        print(
            f"Verified {payload['checked']} fixtures: "
            f"{payload['passed']} passed, {payload['failed']} failed"
        )
        for entry in results:
            if not entry["ok"]:
                print(f"{entry['id']}: {entry['error']}")
    return 1 if payload["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
