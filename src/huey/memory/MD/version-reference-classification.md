# Version Reference Classification Report

Date: 2026-04-10

## Purpose

This report classifies all remaining `6.18.2` and `hueyos-v1` references so repository
usage is unambiguous:

- **Kernel 7.0.x is the active line** for current guidance and operations.
- **6.18.2-era content is legacy, compatibility-fixture, or immutable artifact context only**.

## Classification policy

### Active guidance

References that define current runbooks, release guidance, and role-based naming.
These should prefer `7.0.0-hueyos-core`, `7.0.0-hueyos-pulse`, and
`7.0.0-rc7-hueyos-lab` examples.

### Legacy archive

Historical migration notes kept for provenance and post-mortem context. Legacy
artifacts must be labeled archive/historical and must not be treated as current
deployment guidance.

### Compatibility fixtures

References used by tests to assert parser behavior and downgrade/error handling.
These are intentionally retained.

### Immutable packaging/checksum artifacts

Generated or externally constrained content that should not be rewritten during
terminology sweeps unless regenerated through the canonical release process.

### Non-semantic search-hit collisions

Raw binary/checksum/hash data where `6.18.2` appears as part of a longer token
(e.g., SHA digest substring) and does **not** represent kernel-version guidance.

## Sweep inventory (repository-wide)

| Path | Classification | Action |
| --- | --- | --- |
| `docs/index.md` | Active index + legacy pointer | Keep the 7.0 Phase 2 runbook as active and label 6.18.2 runbook as legacy archive. |
| `docs/kernel-6.18.2-runbook.md` | Legacy archive | Preserve as historical migration note only. |
| `docs/releases/2025-10-31-changeover.md` | Active release guidance with historical context | Keep historical references explicitly framed as superseded by 7.0 active line. |
| `src/huey/memory/MD/HARDWARE.md` | Active platform guidance with historical context | Keep hardware baseline on 7.0 line and frame 6.18.2 line as historical-only context. |
| `tests/test_system_checks_module.py` | Compatibility fixtures | Retain 6.18.2 release strings for parser/behavior coverage. |
| `platform/packaging/dists/forky/main/binary-amd64/Packages` | Non-semantic search-hit collision | No edit; values are SHA512 digest data, not version policy text. |
| `platform/packaging/dists/forky/main/debian-installer/binary-amd64/Packages` | Non-semantic search-hit collision | No edit; values are SHA512 digest data, not version policy text. |
| `archives/releases/checksums/sha256sum.txt` | Non-semantic search-hit collision | No edit; checksum corpus only. |

## Outcome summary

- 7.0 is reaffirmed as the only active guidance line across index, release, and
  platform docs.
- 6.18.2 references are now constrained to one of four explicit buckets:
  **legacy archive**, **historical context in active docs**, **test fixtures**,
  or **non-semantic artifact collisions**.
- No remaining 6.18.2 reference currently reads as authoritative active
  deployment guidance.

## Ongoing guardrails

1. New operational docs must use 7.0 role-based naming.
2. If a `6.18.2` reference is added outside tests/archives, it must include a
   clear legacy label.
3. Sweeps should avoid changing immutable package/checksum artifacts unless they
   are being regenerated as part of a release.
4. Any repo-wide search report should separate semantic version references from
   checksum/hash collisions before opening cleanup tickets.
