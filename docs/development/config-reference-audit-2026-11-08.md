# Configuration reference audit (2026-11-08)

## Canonical entrypoints

| Concern | Canonical file | Alternate file | Resolution |
| --- | --- | --- | --- |
| Python packaging, tests, coverage, Black, isort, Ruff, mypy, Bandit | `pyproject.toml` | `pytest.ini` | `pytest.ini` was removed in PR #867. |
| EditorConfig | `.editorconfig` | `editorconfig` | Alternate is stale and is not auto-loaded by EditorConfig. Retain as historical for this change. |
| flake8 | `.flake8` | `flake8.ini` | Alternate is stale and not auto-loaded; no explicit `-c flake8.ini` reference found. |
| pre-commit | `.pre-commit-config.yaml` | `pre-commit.yaml` | Alternate contains a reduced older hook set; no explicit `-c pre-commit.yaml` reference found. |
| developer commands / CI | `Makefile`, `.github/workflows/ci.yml` | None | CI calls `make lint`; flake8 covers `src`, `tests`, `scripts`, root entrypoints, and `infra`; Black/isort/Ruff keep the existing `LINT_PATHS` scope. |
| Python support policy | `pyproject.toml`, `.python-version` | None | Python 3.13 primary, 3.12 legacy, 3.14 testing. |

## Reference-search result

Searched tracked and hidden repository files, excluding `.git`, `.venv`, and
vendor trees, for alternate config filenames and explicit `-c`/`--config`
selection. The only matches are the tooling map, workflow ownership references,
and historical audit text. No build, test, lint, or CI script selects one of the
alternate files. Standard automatic discovery therefore selects the canonical
dotfiles documented above.

The default `.flake8` scan excludes vendored code and the separately maintained
legacy connector/API compatibility trees. The CI flake8 target additionally
covers root `run.py`/`setup.py` and `infra/`; vendored files are not rewritten
as part of the project lint cleanup.

## Disposition

Keep the three alternates for now because the audit found no active consumer,
but do not present them as active configuration. Before deleting them, check
maintainer-local tooling and any external automation outside this repository;
those systems cannot be observed by a repository search. When they are
removed, update `.gitattributes` and this record in the same change.

The previous tooling map remains at
[`tooling-config-map.md`](tooling-config-map.md).
