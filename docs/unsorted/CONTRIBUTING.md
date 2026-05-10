# Monkey Head Project
# By: Dylan L.R. Pollock
# Contributing to HueyOS

Thank you for your interest in contributing. This document explains the workflow, tooling, and quality bars for changes to **HueyOS** and related components.

> TL;DR checklist
> - Use Python **3.13.x** as the day-to-day baseline (3.14 remains a supported migration target, but not the default toolchain here).
> - Create an isolated environment and install dependencies.  
> - Enable `pre-commit` hooks.  
> - Follow **Conventional Commits** and branch naming.  
> - Add tests and docs for any behavior changes.  
> - Keep PRs focused and pass CI.

---

## Table of contents

1. [Scope](#scope)
2. [Prerequisites](#prerequisites)
3. [Environment setup](#environment-setup)
4. [Local development](#local-development)
5. [Quality gates](#quality-gates)
6. [Git workflow](#git-workflow)
7. [Pull requests](#pull-requests)
8. [Submodules](#submodules)
9. [Documentation](#documentation)
10. [Release notes and versioning](#release-notes-and-versioning)
11. [Security and secrets](#security-and-secrets)
12. [Code of Conduct](#code-of-conduct)
13. [Licensing](#licensing)
14. [Support and questions](#support-and-questions)

---

## Scope

HueyOS is a Python-centric codebase that may include a FastAPI service, CLI tools, and internal libraries. Contributions span:
- Features, bug fixes, and refactors
- Documentation and examples
- Tests and CI/CD improvements
- Developer tooling and DX

If your change meaningfully alters public behavior or APIs, it **must** include tests and docs updates.

---

## Prerequisites

- Python **3.13.x** installed and available on PATH
  - If you use `pyenv`: `pyenv install 3.13.12 && pyenv local 3.13.12`
- Git ≥ 2.40
- Make (optional but convenient)
- Docker (optional) if you run sandboxed plugins or containers during tests
- Node.js (optional) only if you are touching any web UI assets

---

## Environment setup

Choose one method.

### Option A: `venv` + pip
```bash
python3 -m venv .venv
. ./.venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # if present
```

### Option B: `uv` (fast Python package manager)
```bash
# install uv if needed: https://github.com/astral-sh/uv
uv venv
. .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt  # if present
```

### Tooling bootstrap
```bash
# install and activate git hooks
pre-commit install
# run once on the entire tree
pre-commit run --all-files
```

> Notes  
> - Some optional extras may be defined in `pyproject.toml`. Install with:  
>   `pip install .[dev,test]`  
> - If your system OpenSSL is old, build Python with `--with-openssl` or update system packages.

---

## Local development

### Run the API locally
If the repository includes a FastAPI app at `huey/api.py`:
```bash
python -m uvicorn huey.api:app --host 0.0.0.0 --port 1995 --reload
```

### Configuration
- Use environment variables or a local `.env` file (git‑ignored).  
- Provide a minimal `.env.example` when adding new config keys.

### Useful commands
```bash
# run tests
pytest -q

# run with coverage
pytest --maxfail=1 --disable-warnings -q --cov --cov-report=term-missing

# type checks (if mypy is configured)
mypy src/ huey/ || true

# format and lint
ruff check .
ruff format .
black .  # if the project uses Black

# full local gate
pre-commit run --all-files && pytest -q
```

---

## Quality gates

Your change should meet these bars:

1. **Style and lint**: no new warnings from `ruff` or configured linters.
2. **Formatting**: run `ruff format` or `black` as applicable.
3. **Types**: no new `mypy` errors where typing is enforced.
4. **Tests**: unit tests for logic; integration tests if touching IO, network, or persistence.
5. **Docs**: README and `docs/` updated when behavior or flags change.
6. **Performance**: avoid regressions. Add micro-benchmarks when optimizing hot paths.

---

## Git workflow

### Branching
Use short, descriptive branches:
```
feat/<area>-<summary>
fix/<area>-<summary>
chore/<area>-<summary>
docs/<area>-<summary>
refactor/<area>-<summary>
test/<area>-<summary>
```
Examples:
- `feat/api-job-queue`
- `fix/io-timeout`
- `docs/setup-forky`

### Conventional Commits
Prefix messages with a type and optional scope. Examples:
- `feat(api): add /healthz endpoint`
- `fix(storage): handle ENOSPC on rotate`
- `docs(readme): clarify local setup`
- `refactor(core): split config loader`
- `test(api): add integration tests for /jobs`
- `chore(ci): cache uv wheels`

Avoid multi-topic commits. Prefer a stack of small commits.

---

## Pull requests

1. **Keep PRs focused.** One concern per PR.  
2. **Link issues.** Use `Fixes #123` or `Refs #123`.  
3. **Describe behavior changes.** Include before/after, migration notes, screenshots if relevant.  
4. **Update docs.** If users will notice the change, update `README.md` and `docs/`.  
5. **Add tests.** New code without tests is unlikely to be merged.  
6. **Pass CI.** Lint, type check, tests must be green.  
7. **Review-ready.** No commented-out code, no stray prints, no TODOs without issue links.

**PR template checklist**
- [ ] Title uses Conventional Commit format  
- [ ] Description explains what/why/how, risks, and testing  
- [ ] Added/updated tests  
- [ ] Updated docs and changelog (if user-facing)  
- [ ] No secrets in diffs

---

## Submodules

The repository may vendor dependencies as Git submodules.

### Initialize / update
```bash
git submodule update --init --recursive
git submodule update --remote --recursive   # update to tracked branch tips
```

### Track development vs. releases
- Development: `integrations/pyhuey` tracks the full PyHuey source; `vendor/pygpt/pygpt-mhp` holds the lightweight mirror.
- Release: lock submodules to a specific commit and record it.

```bash
# lock to a commit for release
(cd integrations/pyhuey && git fetch && git checkout <commit>)
git add integrations/pyhuey
git commit -m "chore(submodule): lock pyhuey to <shortsha>"
```

> Tip: capture the upstream URL and commit in `RELEASE_NOTES.md` for traceability.

---

## Documentation

- **Docstrings** for all public functions and classes.
- **README.md** covers quick start and high-level architecture.
- **docs/** contains deeper guides, ADRs, and runbooks. If you add a new feature, ship a short guide or example.
- **OpenAPI**: if API contracts change, update the schema and examples.

---

## Release notes and versioning

- Follow [Keep a Changelog](https://keepachangelog.com/) style in `CHANGELOG.md`.
- Use semantic versioning if the project ships published artifacts.
- Tag releases: `git tag -s vX.Y.Z -m "Release vX.Y.Z"` and push tags.

---

## Security and secrets

- **No secrets in git.** Never commit tokens, keys, or credentials.  
- Use environment variables, a local `.env`, or your platform secret store.  
- Provide `.env.example` for non-sensitive keys.

**Vulnerability disclosure:**  
Report security issues privately via GitHub Security Advisories (Repository → Security → Advisories → Report a vulnerability). Do not open public issues for vulnerabilities.

---

## Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) (v2.1). See `CODE_OF_CONDUCT.md`. By participating, you agree to uphold these standards.

---

## Licensing

Unless stated otherwise, contributions are licensed under the repository’s license (e.g., **GPLv3** as noted in the README). By submitting a PR you certify you have the right to contribute the code under that license.

---

## Support and questions

- Use GitHub Issues for bugs and feature requests.
- Use GitHub Discussions or the project’s chat (if available) for Q&A and design proposals.
- For security-related matters, use Security Advisories as noted above.

Thank you for helping improve HueyOS!!
