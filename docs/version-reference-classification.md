# Version Reference Classification Report

Date: 2026-04-10

## Purpose

This report classifies remaining `6.18.2` and `hueyos-v1` references so repository
usage is unambiguous:

- **Kernel 7.0.x is the active line** for current guidance and operations.
- **6.18.2-era content is legacy or immutable context only**.

## Classification policy

### Active guidance

References that define current runbooks, release guidance, and role-based naming.
These should prefer `7.0.0-hueyos-core`, `7.0.0-hueyos-pulse`, and
`7.0.0-rc7-hueyos-lab` examples.

### Legacy archive

Historical migration notes kept for provenance and post-mortem context. Legacy
artifacts must be labeled as archive/historical and must not be treated as
current deployment guidance.

### Compatibility fixtures

References used by tests to assert parser behavior and downgrade/error handling.
These are intentionally retained.

### Immutable packaging/checksum artifacts

Generated or externally constrained content that should not be rewritten during
terminology sweeps unless regenerated through the canonical release process.

## Sweep results

- `docs/index.md` now labels the Linux 6.18.2 runbook as a **legacy archive** and
  promotes the 7.0 Phase 2 runbook as **active guidance**.
- Prompt JSON documents now use role-based 7.0 kernel examples and include
  explicit legacy-context notes.
- Historical mentions in release and hardware documents were rewritten to
  migration-era language rather than `hueyos-v1` naming where active interpretation
  could be ambiguous.
- `6.18.2` references in `tests/` remain intentionally preserved as compatibility
  fixtures.

## Ongoing guardrails

1. New operational docs must use 7.0 role-based naming.
2. If a `6.18.2` reference is added outside tests/archives, it must include a
   clear legacy label.
3. Sweeps should avoid changing immutable package/checksum artifacts unless they
   are being regenerated as part of a release.
