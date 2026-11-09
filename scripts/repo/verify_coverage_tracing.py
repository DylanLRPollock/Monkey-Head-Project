"""Verify that coverage traces executed function *bodies* on this interpreter.

Run independently of pytest-cov to avoid nested tracing and pytest plugin
interactions. Fails on source aliases or tracer failures, not on percentage.
"""

from __future__ import annotations

import importlib
import inspect
import subprocess
import sys
import tempfile
from pathlib import Path

from coverage import Coverage

from huey.memory import indexing


def main() -> int:
    if importlib.import_module("huey.memory.PY.indexing") is not indexing:
        raise RuntimeError("Legacy and canonical indexing imports are not identical.")

    update_lines, update_start = inspect.getsourcelines(indexing.update_index)
    update_lineno = next(
        (
            update_start + index
            for index, line in enumerate(update_lines)
            if "records = _load_index(index_path)" in line
        ),
        None,
    )
    search_lines, search_start = inspect.getsourcelines(indexing.search_index)
    search_lineno = next(
        (
            search_start + index
            for index, line in enumerate(search_lines)
            if "needle = query.strip().lower()" in line
        ),
        None,
    )
    if update_lineno is None or search_lineno is None:
        raise RuntimeError("Cannot locate indexing function body lines.")

    with tempfile.TemporaryDirectory(prefix="huey-cov-probe-") as directory:
        work_dir = Path(directory)
        index_path = work_dir / "probe.json"
        coverage = Coverage(
            data_file=str(work_dir / ".coverage"),
        )
        coverage.start()
        try:
            indexing.update_index(
                {"path": "probe.txt", "content": "coverage probe"},
                index_path=index_path,
            )
            child_code = (
                "import importlib, sys; from pathlib import Path; "
                "indexing = importlib.import_module('huey.memory.PY.indexing'); "
                "assert indexing is importlib.import_module('huey.memory.indexing'); "
                "assert indexing.search_index('coverage probe', "
                "index_path=Path(sys.argv[1]))"
            )
            subprocess.run(
                [sys.executable, "-c", child_code, str(index_path)],
                check=True,
                capture_output=True,
                text=True,
            )
        finally:
            coverage.stop()
            coverage.save()
            coverage.combine()

        source = str(Path(indexing.__file__).resolve())
        hit_lines = set(coverage.get_data().lines(source) or ())
        if update_lineno not in hit_lines:
            raise RuntimeError(
                "Coverage did not record an executed update_index body line. "
                "Check coverage tracers, source aliases and instrumentation."
            )
        if search_lineno not in hit_lines:
            raise RuntimeError(
                "Coverage did not record a Python subprocess search_index body line. "
                "Check subprocess coverage and source path identity."
            )
    print(
        "coverage tracing verified: "
        f"{source}:{update_lineno} and subprocess body line {search_lineno}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
