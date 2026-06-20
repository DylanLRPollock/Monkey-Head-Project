#!/usr/bin/env python3
"""Audit the exposed API surface for duplicates and documentation gaps."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
VENDOR = ROOT / "vendor"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from fastapi.routing import APIRoute


def _load_app():
    os.environ.setdefault("HUEY_ENV", "development")
    module = importlib.import_module("huey.api")
    return module.app


def _route_signature(route: APIRoute) -> tuple[str, tuple[str, ...]]:
    methods = tuple(
        sorted(
            method
            for method in (route.methods or set())
            if method not in {"HEAD", "OPTIONS"}
        )
    )
    return route.path, methods


def main() -> int:
    app = _load_app()
    seen: set[tuple[str, tuple[str, ...]]] = set()
    duplicates: list[str] = []
    undocumented: list[str] = []
    orphaned: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        signature = _route_signature(route)
        if signature in seen:
            duplicates.append(f"{route.path} {sorted(route.methods or set())}")
        else:
            seen.add(signature)
        if not (
            route.summary or route.description or (route.endpoint.__doc__ or "").strip()
        ):
            undocumented.append(route.path)
        if not route.tags:
            orphaned.append(route.path)

    if duplicates or undocumented or orphaned:
        if duplicates:
            print("Duplicate endpoints:")
            for item in duplicates:
                print(f"  - {item}")
        if undocumented:
            print("Undocumented endpoints:")
            for item in undocumented:
                print(f"  - {item}")
        if orphaned:
            print("Orphan endpoints without tags:")
            for item in orphaned:
                print(f"  - {item}")
        return 1

    print("API surface check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
