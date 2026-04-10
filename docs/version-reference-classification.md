# 6.18.2 Reference Classification Sweep (7.0 Active Line)

**Date:** 2026-04-10  
**Outcome:** `7.0` is the current active line across runbooks and platform guidance.  
**Policy:** `6.18.2` references are retained only where they represent legacy history, compatibility tests, or immutable artifacts.

## Classification buckets

### 1) Active docs and index pages (updated/relabelled)
- `docs/index.md` now labels `kernel-6.18.2-runbook.md` as a **legacy archive** and points readers to the 7.0 active-line runbook naming.

### 2) Historical archive docs (kept as legacy context)
- `docs/kernel-6.18.2-runbook.md` remains a historical note by design.
- `docs/releases/2025-10-31-changeover.md` keeps `6.18.2-hueyos-v1` mentions only to document the governance transition to `7.0`.

### 3) Active platform guidance (already 7.0; no baseline rollback)
- `src/huey/memory/MD/HARDWARE.md` already states `7.0` kernel family as current and marks `6.18.2` migration as historical.

### 4) Planning/prompts (updated to 7.0 current line)
- Updated kernel examples/series in:
  - `src/huey/prompts/master-plan-v2-final.json`
  - `src/huey/prompts/master-plan-v3.json`
  - `src/huey/prompts/master-plan-v5.json`
- Added explicit legacy-context notes so `6.18.2` is not interpreted as current target guidance.

### 5) Tests and compatibility fixtures (intentionally retained)
- `tests/test_system_checks_module.py` keeps `6.18.2-*` release strings to verify legacy detection and warning paths.

### 6) Immutable/generated package metadata and unrelated hash collisions (no action)
- `platform/packaging/.../Packages` and `archives/releases/checksums/sha256sum.txt` hits are checksum/hash content, not version policy statements.

## Current policy summary
- **Current line:** `7.0.x` (core/pulse stable tracks; `7.0.0-rc7` lab gateway only).
- **Legacy line:** `6.18.2-*` references are archival or test-fixture context only.
