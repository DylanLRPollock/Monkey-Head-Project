# Bandit baseline policy

## Purpose

This repository carries inherited Bandit findings that are treated as **security debt**, not accepted risk. The committed baseline file (`.security/bandit-baseline.json`) only records the current inherited state so CI can detect regressions.

A baseline does **not** mean the project is secure.

## CI enforcement

CI must run Bandit against `src` with the committed baseline:

```bash
bandit -r src -b .security/bandit-baseline.json -ll -ii
```

Policy behavior:

- Findings already present in `.security/bandit-baseline.json` are recorded as inherited debt.
- **New** Bandit findings at medium/high severity and medium/high confidence fail CI.
- Baseline output is still published as an artifact so debt can be tracked over time.

## Burn-down priority

Inherited findings must be burned down incrementally. Fixes should start with Tier 1 surfaces first:

1. tool/process execution paths (subprocess, shell, dynamic command execution)
2. file mutation paths (write/delete/move/import/export)
3. provider/API and credential handling
4. plugin/tool manager and extension loading

After Tier 1, continue reducing remaining inherited findings until the baseline is empty.

## Maintenance

- Update the baseline only after reviewed security changes.
- Do not blanket-suppress findings (for example, broad `# nosec` usage).
- Every baseline refresh should be accompanied by a short changelog note describing what was fixed vs. what debt remains.
