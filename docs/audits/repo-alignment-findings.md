# Repository Alignment Findings

## Purpose

This document summarizes the first repository alignment scan. It replaces the raw grep output with a curated list of file groups that need review.

## High-level finding

Docker is still present in the repository and should not be deleted blindly. It appears in active infrastructure, security documentation, installer options, tests, archived memory, generated documentation, and vendored/upstream-derived PyGPT material.

Kubernetes appears mostly historical or legacy, but there are still active-looking references that need review before removal.

## Active or likely-active areas

These should be reviewed carefully before changing:

- `infra/docker/`
- `docs/security/docker-image-policy.md`
- `docs/security/security-hardening-status.md`
- `docs/security/security-maintenance-audit.md`
- `docs/security/threat-model-v101.1.md`
- `docs/audits/v101.1-docker-alignment.md`
- `docs/audits/v101.1-dependency-source-of-truth.md`
- `README.md`
- `SECURITY.md`
- `pyproject.toml`
- `requirements.txt`
- `audit-requirements.txt`
- `src/huey/services/container_management.py`
- `src/hueyos/cli/commands/runtime.py`
- `tests/test_cli.py`
- `tests/test_container_management_new.py`
- `tests/test_hostos_module.py`
- `tests/test_run_container_opts.py`

## Optional installer/tooling areas

These should be updated only if the installer strategy changes:

- `platform/installers/debian/Debian/install-deb.sh`
- `platform/installers/debian/Debian/uninstall-deb.sh`
- `platform/installers/macos/macOS/install-mac.sh`
- `platform/installers/macos/macOS/update-mac.sh`
- `platform/installers/windows/Windows/install-win.ps1`
- `platform/installers/windows/Windows/install-win.bat`
- `platform/installers/windows/Windows/update-win.ps1`
- `platform/installers/windows/Windows/update-win.bat`
- `platform/installers/windows/Windows/uninstall-win.ps1`
- `platform/installers/windows/Windows/uninstall-win.bat`

## Historical or archive areas

These should generally be left alone unless the project decides to purge historical memory:

- `src/huey/memory/`
- `src/huey/prompts/OLD/`
- `src/huey/memory/ARCHIVE/`
- `.migration/inventory/`

## Generated or derived areas

These should not usually be edited directly:

- `docs/_build/`
- `.security/bandit-baseline.json`
- `vendor/`

## Current alignment stance

- Docker remains optional development, sandbox, testing, or reproducible-service infrastructure.
- Docker should not be presented as the primary HueyOS runtime unless a current deployment document explicitly promotes it.
- Kubernetes is not active project infrastructure unless a live manifest, installer, CLI path, or deployment document proves otherwise.
- PyHuey remains interface/cockpit/tooling, not the core HueyOS runtime.
- Historical memory and archived prompts should preserve old wording rather than being rewritten as current architecture.

## Recommended next passes

1. Update active documentation to clarify Docker as optional infrastructure.
2. Review `src/hueyos/cli/commands/runtime.py` and decide whether Kubernetes should remain an exposed deploy mode.
3. Review installer flags that install Docker Desktop, Docker CLI, Colima, or Docker Compose.
4. Review tests that encode Docker/Compose assumptions.
5. Leave archive, memory, generated docs, and vendored code untouched unless there is a dedicated archive cleanup pass.
