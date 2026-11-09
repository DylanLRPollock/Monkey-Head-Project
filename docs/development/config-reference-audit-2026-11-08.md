# Configuration reference audit (reviewed 2026-11-09)

## Canonical entrypoints

| Concern | Canonical file | Alternate file | Resolution |
| --- | --- | --- | --- |
| Python packaging, tests, coverage, Black, isort, Ruff, mypy, Bandit | `pyproject.toml` | `pytest.ini` | `pytest.ini` was removed in PR #867. |
| EditorConfig | `.editorconfig` | `editorconfig` | Alternate is stale and is not auto-loaded by EditorConfig. Retain as historical for this change. |
| flake8 | `.flake8` | `flake8.ini` | Alternate is stale and not auto-loaded; no explicit `-c flake8.ini` reference found. |
| pre-commit | `.pre-commit-config.yaml` | `pre-commit.yaml` | Alternate contains a reduced older hook set; no explicit `-c pre-commit.yaml` reference found. |
| developer commands / CI | `Makefile`, `.github/workflows/ci.yml` | None | CI calls `make lint`; flake8 covers `src`, `tests`, `scripts`, root entrypoints, and `infra`; Black/isort/Ruff keep the existing `LINT_PATHS` scope. |
| Python support policy | `pyproject.toml`, `.python-version` | None | Python 3.13 primary, 3.12 legacy, 3.14 testing. |

The three alternate files are not byte-identical copies of their canonical
files. The editor settings, flake8 exclusions/options, and pre-commit hook sets
differ. Therefore the alternates could change behavior if a developer selects
them explicitly; their contents are not silently substituted for the canonical
settings.

## Reference-search result

Searched all tracked repository files, including hidden files and workflow
definitions, for alternate config names and explicit `-c`/`--config` selection.
No build, test, lint, or CI command selects one of the alternate files. Matches
for their names occur in the alternate/canonical config files themselves,
repository metadata (including `.gitattributes` and `CODEOWNERS`), and audit or
tooling documentation. The workflow references found are path filters for the
canonical `.editorconfig`; no active command uses an alternate. `make lint` is
the CI lint entrypoint; it uses the canonical configuration and does not call
pre-commit. Standard automatic discovery therefore selects the canonical
dotfiles documented above.

The default `.flake8` scan excludes vendored code and the separately maintained
legacy connector/API compatibility trees. The CI flake8 target additionally
covers root `run.py`/`setup.py` and `infra/`; vendored files are not rewritten
as part of the project lint cleanup.

## Disposition

The in-repository reference audit is complete: no active consumer was found.
Keep the three alternates as historical reference until maintainers check
local editor, shell, and hook automation that is outside the repository; those
systems cannot be inspected here. Treat that external-consumer check as the
remaining removal gate. When alternates are removed, update `.gitattributes`
and this record in the same change.

The previous tooling map remains at
[`tooling-config-map.md`](tooling-config-map.md).
