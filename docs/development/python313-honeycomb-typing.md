# Python 3.13 Honeycomb / memory typing modernization

This is a narrow, behavior-preserving pass across the canonical memory and
Honeycomb implementations. It replaces deprecated `typing.Dict`,
`typing.List`, and `typing.Optional` annotations with Python 3.13's native
generics and `T | None` unions; collection interfaces now come from
`collections.abc`. It also sorts package exports, uses `datetime.UTC`, and
removes two unnecessary `.keys()` calls.

Files:
- `src/huey/memory/__init__.py`
- `src/huey/v1/proof_loop.py`
- `src/huey/agents/memory.py`
- `src/huey/honeycomb_storage.py`
- `src/huey/honeycomb_index.py`
- `src/huey/honeycomb_monitor.py`

## Invariants

- JSON payloads, storage paths, Honeycomb record keys, registry schemas and
  serialization remain unchanged.
- The existing `huey.os.honeycomb.*` compatibility bridges remain unchanged.
- Python 3.13 is supported; 3.14 is a testing lane; 3.12 is legacy.
- Existing V1 fixture/proof loops and PyHuey integration keep their contracts.
- No production memory directory is accessed by the new tests.

## Validation

Run `python -m pytest tests/test_honeycomb_python313.py -q`, followed by the
full repository tests, static analysis, and security scanning. Tests cover
runtime resolution of the public annotations, per-agent topic separation,
conversation metadata copying, storage/index/monitor integration, and
closed-storage rejection.

This is one incremental reduction of the Ruff backlog documented in issue
#848. It does **not** lower Ruff severity, add blanket ignores, or reduce the
80% coverage gate tracked in issue #847. The remaining diagnostics require
their own focused modernization passes.
