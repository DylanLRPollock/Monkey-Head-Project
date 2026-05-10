# Repository Restructure Inventory (Move / Rename / Fix)

This is the concrete inventory requested for the next restructuring pass.

## 1) Move (path relocations)

### Platform + release artifacts → `platform/` and `archives/`
- `boot/` → `platform/boot/grub/`
- `EFI/` + `efi.img` → `platform/boot/efi/`
- `isolinux/` + `live/` → `platform/boot/legacy/`
- `dists/` → `platform/packaging/dists/`
- `pool/` → `platform/packaging/pool/`
- `pool-udeb/` → `platform/packaging/pool-udeb/`
- `firmware/` → `platform/packaging/firmware/`
- `6.18.5-hueyos/` → `archives/releases/6.18.5-hueyos/`
- `md5sum.txt` + `sha256sum.txt` → `archives/releases/checksums/`

### Installers + setup scripts → `platform/installers/`
- `setup/Debian/` → `platform/installers/debian/`
- `setup/macOS/` → `platform/installers/macos/`
- `setup/Windows/` → `platform/installers/windows/`
- `install/gtk/` → `platform/installers/linux/gtk/`
- `scripts/installers/` → `platform/installers/shared/`

### Runtime/app code boundaries
- `src/huey/scripts/` → `apps/huey-core/scripts/`
- `src/huey/prompts/OLD/` → `archives/prompts/legacy/`
- `gui/` → `apps/huey_gui/` (if still active) or `archives/gui-prototypes/` (if deprecated)
- `docker/` + `Dockerfile` + `Dockerfile.vnc` + `docker-compose.yml` → `infra/docker/`
- `repo/pygpt-MHP/` + `repo/py-gpt/` → `vendor/pygpt/`

### Assets + docs separation
- `HueyOS-background.png` → `assets/images/HueyOS-background.png`
- `secrets/` → `infra/secrets/` (templates only)
- `sources.list` → `platform/installers/debian/sources.list`

## 2) Rename / Consolidate (naming + duplication cleanup)

- `setup/` and `install/` should become one canonical tree: `platform/installers/`.
- `repo/py-gpt` and `repo/pygpt-MHP` should be consolidated under a single naming scheme (`vendor/pygpt/`).
- Pick one canonical runtime package namespace between `src/huey/` and `src/hueyos/`; deprecate the other with import shims for one release.
- `src/huey/pygpt_net` naming should be aligned with integration folder naming (`pygpt_net` vs `pygpt`).
- Remove or repurpose top-level empty `huey/` directory to avoid confusion with `src/huey/`.
- Rename release folder `6.18.5-hueyos/` to a consistent archive format (`archives/releases/hueyos-6.18.5/`).

## 3) Fix (docs, metadata, and project hygiene)

### README structure table drift
The current README "Repository Structure" table references paths that do not exist (or no longer exist) and should be corrected:
- `master-plan-v16.json` (missing)
- `reports/` (missing)
- `shared-host/` (missing)

### Packaging + source clarity
- Ensure root-level `pyproject.toml` and dependency files point only to canonical source roots after consolidation.
- Add explicit deprecation notices for any transitional compatibility paths.

### Ignore + generated artifacts policy
- Ensure generated caches and binaries remain out of source review paths.
- Confirm `.gitignore` keeps build/runtime caches excluded and preserve only intentional release artifacts under `archives/`.

### Ownership + onboarding
- Add a `docs/repo-map.md` with owner boundaries (runtime, installers, packaging, integrations, docs).
- Add CI checks for forbidden top-level path additions outside approved roots.

## 4) Suggested execution order

1. Move platform/installer/release artifacts first (low risk to Python imports).
2. Consolidate `repo/*` integrations and container definitions.
3. Resolve runtime package duplication (`src/huey` vs `src/hueyos`).
4. Apply README/doc/CI cleanup once paths are stable.

## 5) Done criteria for this inventory

- Every top-level directory has a canonical destination.
- Every duplicated naming pattern has a single target convention.
- Every missing/outdated README entry is corrected.
- CI and contributor docs enforce the new structure.
