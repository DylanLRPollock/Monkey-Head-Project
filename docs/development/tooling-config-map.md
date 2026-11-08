# Tooling configuration ownership (2026-11-08)

This map records entrypoints. It deliberately does not delete historical or
alternate files without dependency and reference auditing.

| Tool | Canonical entrypoint | Alternate / disposition |
| --- | --- | --- |
| Python packaging, Black, isort, Ruff, coverage, pytest, mypy, Bandit | `pyproject.toml` | `pytest.ini` has been removed; pytest settings live in `pyproject.toml`, including an explicit asyncio fixture loop scope. |
| EditorConfig | `.editorconfig` | `editorconfig` remains as an alternate historical file, not the automatic entrypoint. |
| flake8 | `.flake8` (flake8 does not load pyproject) | `flake8.ini` is not automatically applied when .flake8 exists; retain for reference until migrated. |
| Pre-commit | `.pre-commit-config.yaml` | `pre-commit.yaml` is not the automatic filename; do not run with `-c pre-commit.yaml` unless intentionally testing the alternate. |
| CI tasks and developer commands | `Makefile`, `.github/workflows/ci.yml` | CI uses `make lint`, **not** `pre-commit run --all-files`. Avoid claiming parity between them without running both. |
| Python interpreter policy | `pyproject.toml` and `.python-version` when present | 3.13 supported, 3.12 legacy, 3.14 experimental. |

## Reference audit before removal

The canonical automatic entrypoints are `pyproject.toml`, `.editorconfig`,
`.flake8` and `.pre-commit-config.yaml`. The root alternates `editorconfig`,
`flake8.ini` and `pre-commit.yaml` remain tracked as historical alternates.
The repository-wide reference audit found no active script or CI consumer and
no explicit `-c` / `--config` selection for them. External maintainer-local
automation cannot be searched from this checkout, so removal remains a
separate maintainer decision. See
[`config-reference-audit-2026-11-08.md`](config-reference-audit-2026-11-08.md).

## Change policy

1. Keep `black --check`, `isort --check-only`, `ruff check` and `flake8`
   enabled. They have differing roles; do not disable failures to green CI.
2. Run `make lint` and `make coverage` on supported Python 3.13. Run
   pre-commit explicitly if changing hook specifications.
3. Treat E402 bootstrap imports, serialized Enums and packaging imports as
   compatibility-sensitive. Autofix typing one maintained domain at a time,
   verify imports and tests, report Ruff diagnostic count changes in issue #848.
4. Confirm duplicate assertions cover the same behavior before removing any
   tests. Unit fixtures should not invoke hardware or launch privileged jobs.

See [current risk register](../security/current-risk-register-2026-11-03.md).
