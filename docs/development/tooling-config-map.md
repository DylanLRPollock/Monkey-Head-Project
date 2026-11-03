# Tooling configuration ownership (2026-11-03)

This map records entrypoints. It deliberately does not delete historical or
alternate files without dependency and reference auditing.

| Tool | Canonical entrypoint | Alternate / disposition |
| --- | --- | --- |
| Python packaging, Black, isort, Ruff, coverage, pytest, mypy, Bandit | `pyproject.toml` | `pytest.ini` previously shadowed pytest settings in pyproject; remove after confirming equivalent options. |
| EditorConfig | `.editorconfig` | `editorconfig` remains as an alternate historical file, not the automatic entrypoint. |
| flake8 | `.flake8` (flake8 does not load pyproject) | `flake8.ini` is not automatically applied when .flake8 exists; retain for reference until migrated. |
| Pre-commit | `.pre-commit-config.yaml` | `pre-commit.yaml` is not the automatic filename; do not run with `-c pre-commit.yaml` unless intentionally testing the alternate. |
| CI tasks and developer commands | `Makefile`, `.github/workflows/ci.yml` | CI uses `make lint`, **not** `pre-commit run --all-files`. Avoid claiming parity between them without running both. |
| Python interpreter policy | `pyproject.toml` and `.python-version` when present | 3.13 supported, 3.12 legacy, 3.14 experimental. |

### Reference audit before removal

Repository code search for `pytest.ini`, `flake8.ini`, `pre-commit.yaml`,
`editorconfig`, `.flake8` and `.pre-commit-config.yaml` on November 3
found references in `docs/audits/v101.1-style-tooling.md`, `.gitattributes`,
`.github/CODEOWNERS`, historical docs and configuration comments. Preserve
historical descriptions or update links rather than deleting files by
similar name. Audit external scripts and local developer tooling before
removing the three noncanonical alternates.

### Change policy

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
