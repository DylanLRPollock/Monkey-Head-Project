# Repository Restructure Recommendation

This document proposes a practical reorganization so the repository is easier to navigate, safer to maintain, and clearer for contributors.

> For the concrete path-by-path checklist, see `docs/repository-restructure-inventory.md`.

## Goals

- Separate **source code** from **generated artifacts** and **release payloads**.
- Make ownership boundaries obvious (runtime code, packaging, docs, operations).
- Keep historical and large binary assets available, but out of day-to-day developer paths.
- Reduce ambiguity caused by duplicate folders (`setup/` and `install/`, multiple app copies, etc.).

## Recommended Top-Level Layout

```text
.
├── apps/                    # runnable applications and entry points
│   ├── huey-core/           # primary Python runtime (from src/huey + src/monkey_head)
│   └── hueyos-tools/        # CLI/utilities currently spread across scripts/tools
├── integrations/
│   ├── pyhuey/              # live PyHuey submodule / adapter work
│   └── command-center/      # optional companion dashboard / prototype submodule
├── platform/
│   ├── boot/                # boot/grub, EFI, isolinux, live
│   ├── packaging/           # dists, pool, pool-udeb, firmware metadata
│   └── installers/          # setup + install scripts by OS
├── infra/
│   ├── docker/              # all docker definitions and orchestration helpers
│   └── ci/                  # workflow support files/scripts
├── docs/                    # architecture, governance, release notes, runbooks
├── tests/                   # automated tests
├── assets/                  # static media (images, diagrams, UI assets)
├── archives/                # frozen historical snapshots, old release payloads
└── vendor/                  # vendored third-party dependencies and PyGPT mirrors
```

## What to Move First (Low-Risk Phase)

1. Consolidate installer-related content:
   - Merge `setup/` and `install/` into `platform/installers/`.
2. Group boot/distribution artifacts:
   - Move `boot/`, `EFI/`, `isolinux/`, `live/`, `dists/`, `pool/`, `pool-udeb/` under `platform/`.
3. Isolate generated release outputs:
   - Move versioned release blobs (e.g., `6.18.5-hueyos/`, ISO artifacts) into `archives/releases/`.
4. Clarify app code location:
   - Keep active Python runtime in one place and mark duplicates as deprecated with README pointers.

## Guardrails for the Migration

- Perform moves in **small batches** with a path-mapping changelog.
- Add temporary compatibility shims for scripts expecting old paths.
- Update CI/workflows and Makefile targets immediately after each batch.
- Keep binary-heavy directories excluded from frequent lint/test loops.

## Suggested Naming Rules

- Use lowercase kebab-case for directories (`huey-core`, `release-artifacts`).
- Reserve `src/` for Python package code only.
- Reserve `docs/` for human-readable specs and runbooks only.
- Keep generated/package outputs under `platform/packaging` or `archives/`, never mixed with app source.

## Success Criteria

- A new contributor can identify runtime code, installers, packaging, and docs in under 2 minutes.
- CI paths no longer depend on duplicated folder semantics.
- Release artifacts are preserved but do not obscure active development files.

## Rollout Plan

- **Phase 1:** Move installer and platform artifacts; preserve compatibility shims.
- **Phase 2:** Consolidate active runtime/app code and integrations.
- **Phase 3:** Archive legacy snapshots and remove temporary shims.
- **Phase 4:** Update contributor docs + enforce structure checks in CI.
