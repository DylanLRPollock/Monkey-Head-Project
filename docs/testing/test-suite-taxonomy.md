# HueyOS test taxonomy (2026-11-03)

Python 3.13 is the supported release target. The 3.14 CI lane is
experimental and non-gating; both must report actual failures and skips.

| Tier | Location / examples | Isolation and gate |
| --- | --- | --- |
| Unit | `tests/test_memory_indexing_behaviors.py`, `tests/test_privileged_operations.py`, data/model validation tests | `tmp_path`, monkeypatched subprocess/network/hardware; must never modify physical hardware or call the network. Run on every PR. |
| Integration | FastAPI `tests/test_api_routes.py`, storage and persistence integration tests, CLI/service boundary tests | ASGI in-process client, temporary DBs and fake processes. HTTP auth and privilege-boundary negatives required. |
| Hardware / platform / offline | Sensors, GPU, audio, installer path tests, Linux/macOS/Windows command builders | Mock hardware by default. Hardware-required tests must carry explicit `pytest.mark.hardware` and an environment opt-in; CI skips are documented rather than silently bypassed. Offline tests must block external network by default. |
| End-to-end | Deployment smoke, `package-smoke.yml`, platform installer rehearsal, API exercised through an isolated runtime | Container/VM or dedicated lab host. Never run destructive end-to-end operations on an ordinary developer machine or unattended CI runner. |

## Coverage contract

- `pyproject.toml`: `[tool.coverage.run]` measures source under
  `src/huey` with branches. The allowed legacy/vendor exclusions are
  explicit. Maintained runtime modules may not be removed to inflate metrics.
- `[tool.coverage.report].fail_under = 80` remains the enforced threshold.
- `scripts/repo/verify_coverage_tracing.py` independently checks that an
  executed `huey.memory.indexing.update_index` body line actually appears in
  the coverage trace. This catches tracer/source alias faults; it does not
  prove sufficient coverage by itself.
- Historic November 3 failing evidence (issue #847): 36% combined CI total;
  XML measured 4,228/9,989 source lines (42.33%) and 70/1,890 branches
  (3.70%). The combined figure is `(4,228 + 70) / (9,989 + 1,890) = 36.18%`:
  coverage.py combines covered statements and covered branches for its total.
  The 42.33% line rate and 3.70% branch rate are **different metrics**, not
  contradictory results.
  At PR #896 (2026-11-09), both Python 3.13 and 3.14 report 750 passed,
  16 skipped, and 56.45% combined coverage. Coverage tracing validation and
  static analysis pass; the only CI failure is the unchanged 80% threshold.
  Publish this as the current full-suite baseline until a later CI run replaces it.
- Coverage enables subprocess tracing because fixture and CLI tests execute
  Python children. This does not trace external programs such as FFmpeg.
- Every coverage PR should report full and module-level line/branch deltas,
  missed paths, and the exact CI run/coverage artifact. Report core runtime,
  optional hardware, vendor, and legacy areas separately; do not omit a
  maintained module from the combined gate.

## Skip policy

Register custom pytest markers centrally when introduced, document
platform-dependent skip reasons, and keep negative tests mandatory.
A skip may reflect missing optional equipment; it may not hide a failure of
a supported Python 3.13 pure-software codepath. Check skip counts in CI.
