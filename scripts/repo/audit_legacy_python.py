#!/usr/bin/env python3
"""Statically inventory legacy Huey Python without executing the modules.

Results identify possible consumers, not proof that a module is used or unused.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

LEGACY = Path("src/huey/memory/PY")
ROOTS = ("src/huey", "scripts", "tests")
PREFIX = "huey.memory.PY"


def _dynamic_dependency(node: ast.Call, dotted: str) -> str | None:
    func = node.func
    label = (
        func.attr
        if isinstance(func, ast.Attribute)
        else func.id if isinstance(func, ast.Name) else ""
    )
    if label not in {"import_module", "find_spec", "__import__"} or not node.args:
        return None
    value = node.args[0]
    if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
        return None
    if not value.value.startswith(dotted):
        return None
    return value.value[len(dotted) :].split(".", 1)[0]


def dependencies(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    dotted = PREFIX + "."
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(
                item.name[len(dotted) :].split(".", 1)[0]
                for item in node.names
                if item.name.startswith(dotted)
            )
        elif isinstance(node, ast.ImportFrom):
            if node.module == PREFIX:
                found.update(n.name for n in node.names if n.name != "*")
            elif node.module and node.module.startswith(dotted):
                found.add(node.module[len(dotted) :].split(".", 1)[0])
        elif isinstance(node, ast.Call):
            dependency = _dynamic_dependency(node, dotted)
            if dependency:
                found.add(dependency)
    return found


def category(name: str) -> str:
    if name.startswith("test_") or name == "conftest.py":
        return "tests/"
    if name.startswith("example_") or name.endswith("_demo.py"):
        return "examples/"
    if name.startswith(("check_", "generate_repo_map", "add_project_headers")):
        return "scripts/repo/"
    if name.startswith(("honeycomb_", "backup_restore", "storage_", "integrity")):
        return "huey.honeycomb-or-storage"
    if name.startswith(
        (
            "media_",
            "audio_",
            "speech_",
            "video_",
            "ffmpeg_",
            "probe_media",
            "prepare_audio",
            "silence_",
            "waveform_",
        )
    ):
        return "huey.media"
    if name.startswith(
        ("fixture_registry", "proof_loop", "response_bridge", "structured_run_log")
    ):
        return "huey.v1"
    if name.startswith(("pygpt_", "tool_manifest")):
        return "huey.connectors.pyhuey"
    if name.startswith(("main_ui", "ai_tools_gui", "dashboard", "huey_tkinter")):
        return "huey.gui-or-apps"
    if name.startswith(("install", "uninstall", "repair", "update_sources_")):
        return "huey.platform"
    return "review"


def _consumer_paths(root: Path, source: Path) -> set[Path]:
    all_files: set[Path] = set()
    for folder in ROOTS:
        directory = root / folder
        if directory.is_dir():
            all_files.update(directory.rglob("*.py"))
    for name in ("run.py", "setup.py", "conftest.py"):
        if (root / name).is_file():
            all_files.add(root / name)
    return {path for path in all_files if not path.is_relative_to(source)}


def _legacy_record(
    path: Path,
    root: Path,
    consumers: dict[str, set[str]],
    same_name: dict[str, list[str]],
    errors: list[dict[str, str]],
) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    error = None
    body = path.read_text(encoding="utf-8-sig")
    try:
        tree = ast.parse(body, filename=relative)
        has_main = any(
            isinstance(n, ast.If) and "__main__" in ast.unparse(n.test)
            for n in tree.body
        )
    except SyntaxError as exc:
        error = str(exc)
        errors.append({"file": relative, "error": error})
        has_main = False
    return {
        "name": path.name,
        "path": relative,
        "bytes": path.stat().st_size,
        "target_family": category(path.name),
        "static_consumers": sorted(consumers.get(path.stem, ())),
        "same_named_candidates": same_name.get(path.name, []),
        "main_guard": has_main,
        "syntax_error": error,
    }


def build_inventory(root: Path) -> dict[str, Any]:
    root = root.resolve()
    source = root / LEGACY
    if not source.is_dir():
        raise FileNotFoundError(source)
    consumers: dict[str, set[str]] = {}
    same_name: dict[str, list[str]] = {}
    errors: list[dict[str, str]] = []
    scanned = sorted(_consumer_paths(root, source))
    for path in scanned:
        relative = path.relative_to(root).as_posix()
        same_name.setdefault(path.name, []).append(relative)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=relative)
        except (SyntaxError, UnicodeError) as exc:
            errors.append({"file": relative, "error": str(exc)})
            continue
        for name in dependencies(tree):
            consumers.setdefault(name, set()).add(relative)

    files = [
        _legacy_record(path, root, consumers, same_name, errors)
        for path in sorted(source.glob("*.py"))
    ]
    return {
        "schema": "huey.legacy_python_inventory.v1",
        "method": "static AST lower-bound; no runtime execution",
        "legacy_count": len(files),
        "scanned_count": len(scanned),
        "errors": errors,
        "files": files,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--fail-on-syntax", action="store_true")
    args = parser.parse_args(argv)
    report = build_inventory(args.root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        referenced = sum(bool(f["static_consumers"]) for f in report["files"])
        print(
            f"{report['legacy_count']} legacy Python files; "
            f"{referenced} with direct static consumers; "
            f"{len(report['errors'])} syntax failures"
        )
        for item in report["files"]:
            print(
                f"{item['name']:<42} {item['target_family']:<30} "
                f"refs={len(item['static_consumers'])}"
            )
    return 1 if args.fail_on_syntax and report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
