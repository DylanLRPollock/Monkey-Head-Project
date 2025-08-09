# Monkey Head Project
# By: Dylan L.R. Pollock
# Contributing to HueyOS

## Environment
- Python **3.12–3.13** (3.13 supported; some libs are 3.13-only like audioop-lts)
- Install `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

## Workflow
1. Branch naming: `feat/<area>-<summary>` or `fix/<area>-<summary>`
2. Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
3. Hygiene & tests:
   ```bash
   pre-commit install
   pre-commit run --all-files
   pytest -q
   ```
4. Run locally:
   ```bash
   python -m uvicorn huey.api:app --host 0.0.0.0 --port 5151
   ```
5. Keep PRs focused; update `README.md`/`docs/` if behavior changes.

## Submodules
- `repo/pygpt-MHP` tracks `main` in development.
- For releases, lock to a commit:
  ```bash
  git submodule update --init --recursive
  (cd repo/pygpt-MHP && git fetch && git checkout <commit>)
  git add repo/pygpt-MHP
  git commit -m "chore(submodule): lock pygpt-MHP to <shortsha>"
  ```

## Security
- No secrets in git. Use environment variables or `.env` (ignored).
- Report vulnerabilities privately to the maintainer.