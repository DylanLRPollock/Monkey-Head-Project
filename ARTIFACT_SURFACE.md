# Artifact Surface Report

This report identifies committed binary/large artifacts, focused on:
- `platform/packaging`
- `platform/boot`
- GRUB modules/assets
- large binary files
- vendored archives
- generated build outputs

Method: scanned tracked files (`git ls-files`), measured file sizes from working tree, and classified type primarily by extension/path conventions.

## Largest Artifact Summary (Top items)

| Path | File type | Approx size | Why present | Recommendation |
|---|---:|---:|---|---|
| `platform/installers/linux/gtk/initrd.gz` | Compressed initramfs image (`.gz`) | 63.4 MB | Installer/runtime boot image for GTK installer | Move to release artifact |
| `src/huey/memory/ZIP/dlrp-ca-v84.3.zip` | ZIP archive | 38.1 MB | Vendored/reference archive under project memory assets | Needs review |
| `platform/installers/linux/initrd.gz` | Compressed initramfs image (`.gz`) | 23.2 MB | Non-GTK installer boot image | Move to release artifact |
| `archives/releases/hueyos-6.18.5 (Test Kernel)/linux-image-6.18.5-hueyos_6.18.5-4_amd64.deb` | Debian package (`.deb`) | 17.8 MB | Archived kernel release payload | Move to release artifact |
| `platform/boot/legacy/live/vmlinuz-6.18.5-hueyos` | Linux kernel binary | 12.2 MB | Bootable live kernel (versioned) | Keep in git (if reproducible source references exist), otherwise move to release artifact |
| `platform/boot/legacy/live/vmlinuz` | Linux kernel binary | 12.2 MB | Bootable live kernel (default path) | Needs review (duplicate of versioned image likely) |
| `platform/installers/linux/vmlinuz` | Linux kernel binary | 11.5 MB | Installer kernel | Move to release artifact |
| `platform/installers/linux/gtk/vmlinuz` | Linux kernel binary | 11.5 MB | GTK installer kernel | Move to release artifact |
| `src/huey/memory/MP4/TEST.mp4` | MP4 video | 11.1 MB | Media asset / reference content | Needs review |
| `platform/packaging/pool-udeb/main/f/fonts-noto/fonts-noto-unhinted-udeb_20201225-2_all.udeb` | Debian installer micro-package (`.udeb`) | 10.0 MB | Offline installer package pool content | Keep in git (if repository is intended to be self-contained installer mirror), otherwise move |
| `archives/releases/hueyos-6.18.5 (Test Kernel)/linux-headers-6.18.5-hueyos_6.18.5-4_amd64.deb` | Debian package (`.deb`) | 8.9 MB | Archived kernel headers for release | Move to release artifact |
| `platform/packaging/pool-udeb/main/e/espeak-ng/espeak-ng-data-udeb_1.52.0+dfsg-5+b1_amd64.udeb` | `.udeb` | 8.2 MB | Installer package pool content | Keep in git or move as a full pool snapshot (decision at repository policy level) |

## Focus Area Findings

### 1) Platform packaging (`platform/packaging`)

- `pool-udeb` appears to be a vendored installer dependency pool.
- Observed surface:
  - **232 `.udeb` files totaling ~55.1 MB**.
  - Representative large entries include GTK, fonts, crypto, libc, and installer utilities.
- Interpretation: likely intentional for fully offline/reproducible installer builds.
- Recommendation:
  - If this repo is intended to serve as a source+payload monorepo: **keep in git**.
  - If not required for every clone: **move entire pool snapshots to release artifacts/object storage** and keep manifest indices in git.

### 2) Platform boot (`platform/boot`)

- Contains boot-critical binary artifacts:
  - Kernel images (`vmlinuz*`)
  - EFI binaries (`bootx64.efi`, `grubx64.efi`)
  - EFI image containers (`efi.img`, GRUB `efi.img`)
  - GRUB font/resources (`unicode.pf2`, splash)
- Recommendation:
  - Keep only minimal boot configuration + build scripts in git where possible.
  - Publish generated boot images/kernels as **release artifacts** unless strict source-tree bootability is required.

### 3) GRUB modules (`platform/boot/grub/grub/x86_64-efi`)

- Observed surface:
  - **279 module/list files totaling ~2.9 MB**.
- These look like a prebuilt GRUB module set used by EFI boot media.
- Recommendation:
  - Usually acceptable to **keep in git** when packaging boot media directly from repository.
  - If build pipeline can regenerate deterministically from pinned GRUB version, consider moving compiled modules to release artifacts and keeping only module list + generation recipe.

### 4) Vendored archives and release payloads

- `archives/releases/.../*.deb` and `src/huey/memory/ZIP/*.zip` are classic vendored artifacts.
- Recommendation:
  - Kernel/package release binaries: **move to release artifacts**.
  - Reference/media ZIPs: **needs review** (depends whether it is source-of-truth content or distributable output).

### 5) Generated build outputs (likely)

Likely generated outputs include:
- `initrd.gz`, `vmlinuz`, `.efi`, `.img`, `.udeb`, `.deb`

Recommendation:
- Prefer storing build instructions, provenance metadata, and hashes in git.
- Store heavy generated binaries in release channels.

## Checksum-based Tracking Recommendation (if artifacts are moved)

If artifacts are externalized later, adopt checksum-based tracking:

1. Create `ARTIFACT_MANIFEST.sha256` in git containing:
   - `sha256`, `size`, `artifact logical name`, `source URL/object path`, `version/tag`.
2. Enforce CI verification:
   - Download artifact
   - Verify `sha256sum -c ARTIFACT_MANIFEST.sha256`
   - Fail build on mismatch.
3. Add optional signature provenance:
   - Sign manifest with `minisign`, `cosign`, or GPG for tamper evidence.
4. Version manifests with release tags to preserve historical reproducibility.

## Notes

- This report does **not** classify files as malicious; it only describes artifact surface and repository hygiene tradeoffs.
- No files were moved or modified besides creating this report.
