"""Static inventory must not import or execute legacy scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/repo/audit_legacy_python.py"
spec = importlib.util.spec_from_file_location("legacy_inventory", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def create(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_static_consumers_do_not_execute_code(tmp_path: Path) -> None:
    create(
        tmp_path / "src/huey/memory/PY/foo.py", "raise RuntimeError('not executed')\n"
    )
    create(tmp_path / "src/huey/memory/PY/bar.py", "x = 1\n")
    create(tmp_path / "src/huey/app.py", "from huey.memory.PY import foo\n")
    create(tmp_path / "tests/test_app.py", "import huey.memory.PY.foo\n")
    create(tmp_path / "src/huey/other.py", "'huey.memory.PY.bar'\n")
    report = module.build_inventory(tmp_path)
    rows = {item["name"]: item for item in report["files"]}
    assert report["legacy_count"] == 2
    assert rows["foo.py"]["static_consumers"] == [
        "src/huey/app.py",
        "tests/test_app.py",
    ]
    assert rows["bar.py"]["static_consumers"] == []
    assert report["errors"] == []


def test_reports_invalid_syntax_without_import(tmp_path: Path) -> None:
    create(tmp_path / "src/huey/memory/PY/bad.py", "def broken(:\n")
    assert len(module.build_inventory(tmp_path)["errors"]) == 1


def test_recognizes_explicit_dynamic_import(tmp_path: Path) -> None:
    create(tmp_path / "src/huey/memory/PY/thing.py", "value = 1\n")
    create(
        tmp_path / "src/huey/app.py",
        "from importlib import import_module\n"
        'import_module("huey.memory.PY.thing")\n',
    )
    report = module.build_inventory(tmp_path)
    assert report["files"][0]["static_consumers"] == ["src/huey/app.py"]
