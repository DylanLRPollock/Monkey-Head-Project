"""Verify that coverage traces executed function *bodies* on this interpreter.

Run independently of pytest-cov to avoid nested tracing and pytest plugin
interactions. Fails on source aliases or tracer failures, not on percentage.
"""

from __future__ import annotations

import inspect
import tempfile
from pathlib import Path

from coverage import Coverage

from huey.memory import indexing


def main() -> int:
    body_lines, start = inspect.getsourcelines(indexing.update_index)
    needle = "records = _load_index(index_path)"
    body_lineno = next(
        (
            start + index
            for index, line in enumerate(body_lines)
            if needle in line
        ),
        None,
    )
    if body_lineno is None:
        raise RuntimeError("Cannot locate update_index body line.")

    with tempfile.TemporaryDirectory(prefix="huey-cov-probe-") as directory:
        index_path = Path(directory) / "probe.json"
        coverage = Coverage(
            config_file=False,
            branch=True,
            data_file=None,
            source=["huey.memory.indexing"],
        )
        coverage.start()
        try:
            indexing.update_index(
                {"path": "probe.txt", "content": "coverage probe"},
                index_path=index_path,
            )
            indexing.search_index("coverage probe", index_path=index_path)
        finally:
            coverage.stop()
            coverage.save()

        source = str(Path(indexing.__file__).resolve())
        hit_lines = set(coverage.get_data().lines(source) or ())
        if body_lineno not in hit_lines:
            raise RuntimeError(
                "Coverage did not record an executed update_index body line. "
                "Check coverage tracers, source aliases and instrumentation."
            )
    print(f"coverage tracing verified: {source}:{body_lineno}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
