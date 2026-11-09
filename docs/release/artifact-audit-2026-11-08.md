# Release artifact audit (reviewed 2026-11-09)

## Inventory

The tracked repository contains large boot/install images, Debian `.udeb`
packages, Windows installer binaries, kernel/initrd payloads, archives,
documentation, and media. The largest tracked files include Linux initrd and
kernel images, the legacy `src/huey/memory/ZIP/dlrp-old.zip` archive, GRUB EFI
images, the Windows launcher installer, PDFs, and test media. These are
distribution or platform payloads rather than normal Python package modules.

The `Artifact & Filesystem Security Scan` workflow now emits a complete
tracked-file inventory containing path, size, extension classification, and
SHA-256, tied to the scanned commit. The report remains a review aid: binary
extension and checksum do not prove license, origin, or build reproducibility.

The latest completed Artifact & filesystem scan workflow
([run 42558916250](https://github.com/DylanLRPollock/Monkey-Head-Project/actions/runs/42558916250))
inventoried 2,010 tracked files at merge-ref commit
`78df2f698cb6e3bab9c65e9ca0958f80dcd1d835`; ten were at least 5 MiB. The
workflow artifact `artifact-risk-scan-results` contains the complete
path/size/SHA-256 inventory. Its report was generated 2026-11-09 at 03:55 UTC.

### Files at least 5 MiB

| Size | Tracked path | SHA-256 |
| ---: | --- | --- |
| 63.40 MiB | `src/huey/platform/installers/linux/gtk/initrd.gz` | `37ecc4117ed848d782b70bffd21e18799dc311816f07941e67da857bff3037fb` |
| 23.21 MiB | `src/huey/platform/installers/linux/initrd.gz` | `ccd0eab9333579fde4cec9309de0e3f3d480ccb2e190a292ec8b3b650d8ce40b` |
| 23.06 MiB | `src/huey/memory/ZIP/dlrp-old.zip` | `d689fc416b560c60e3ccee6e4025e72d41aac840725ef445e2802547f0177483` |
| 12.16 MiB | `src/huey/platform/boot/legacy/live/vmlinuz` | `4dc574614936db013ec05c80da52bfb46131f350efdea7bacaf75054d7df79a5` |
| 12.16 MiB | `src/huey/platform/boot/legacy/live/vmlinuz-6.18.5-hueyos` | `4dc574614936db013ec05c80da52bfb46131f350efdea7bacaf75054d7df79a5` |
| 11.54 MiB | `src/huey/platform/installers/linux/gtk/vmlinuz` | `123e30d376f800b70848505a1193d0fce03359052677ed4e068eb60231a4bb02` |
| 11.54 MiB | `src/huey/platform/installers/linux/vmlinuz` | `123e30d376f800b70848505a1193d0fce03359052677ed4e068eb60231a4bb02` |
| 11.12 MiB | `src/huey/memory/MP4/TEST.mp4` | `a6d54b6196edf477a266d79a010616f3ace0addd21798753479d7d9466f5d09d` |
| 9.99 MiB | `src/huey/platform/packaging/pool-udeb/main/f/fonts-noto/fonts-noto-unhinted-udeb_20201225-2_all.udeb` | `74da175792c6ad710c92eabca3657a8b05388f64fed95ca587165a086d564088` |
| 8.23 MiB | `src/huey/platform/packaging/pool-udeb/main/e/espeak-ng/espeak-ng-data-udeb_1.52.0+dfsg-5+b1_amd64.udeb` | `22d5801f18ff5685541219e4a62542aa5937e15538c05d8a0a3b926381ec7c99` |

The two kernel-content duplicate pairs have matching hashes but occupy distinct
boot/installer paths; the copies may be required by the corresponding layout.
Do not remove them based only on hash equality. The table identifies tracked
bytes and content identity, not ownership or provenance.

The filenames identify two Debian `.udeb` packages and include package
versions, but this scan does not establish the upstream source revision,
license/NOTICE obligations, owning component, intended consumer, or
reproducible build recipe for any row. Those fields remain open for maintainer
review before moving, replacing, redistributing, or removing a payload.
No payload was deleted based only on size or duplicate content.

## Python release bundle

The release workflow builds one wheel and one sdist, verifies package files
and the wheel version, installs both into fresh environments, and performs
import/console-script smoke checks. It now also emits a reproducible CycloneDX
1.6 JSON SBOM for the installed wheel environment, generates a SHA-256 manifest
after the full release artifact set is assembled, verifies that manifest in
the build job, and verifies it again after artifact download in the publish
job. The package publisher continues to create PyPI provenance attestations.

## Published GitHub releases checked

The GitHub Releases API was checked on 2026-11-09. The repository has four
published pre-releases (`Pre-Release-#1` through `Pre-Release-#4`, latest
published 2026-07-17); none has attached assets. No `v*` package release was
present in that listing. There are no current GitHub release assets to
rehash or verify. The tagged release workflow is configured to create
repository artifact attestations for the wheel, sdist, CycloneDX SBOM, and
`SHA256SUMS` before publishing, then attach the checksummed `dist/*` files.
The attest action is pinned by full commit SHA. PyPI provenance and GitHub
artifact attestations cover separate publication channels. The workflow
configuration has not yet been exercised by a tagged release.

## Residual decisions

- Keep platform and legacy binary payloads until owners confirm their consumer,
  license/NOTICE, upstream origin, retention, and replacement path.
- The repository-wide inventory is not itself an SBOM; only the Python release
  runtime receives a CycloneDX dependency bill of materials in this change.
- SHA-256 hashes establish byte identity; artifact attestations bind release
  file digests to the repository workflow that produced them.
- The release workflow is configured to attest its wheel, sdist, SBOM, and
  checksum manifest using GitHub artifact attestations. Verify each attached
  file with `gh attestation verify <file> --repo
  DylanLRPollock/Monkey-Head-Project` after the next tagged release, and
  confirm the PyPI provenance and SBOM as well.
- This audit records configuration only; it does not claim that a release
  attestation has already been generated or verified.
- Ten tracked files over 5 MiB still need a maintainer-reviewed owner,
  upstream-origin, license/NOTICE, and consumer register. Checksums and package
  names alone do not answer those questions.
- No binary/archive payload was removed based only on size or extension.

## Reproduction

Run the `artifact-scan` workflow on a commit and download
`artifact-risk-scan-results/tracked-artifact-inventory.json`. For package
releases, inspect the attached `hueyos-<version>.cdx.json` and `SHA256SUMS`;
the publish job verifies the latter and creates GitHub artifact attestations
for the release files. After download, verify each release asset with
`gh attestation verify <file> --repo DylanLRPollock/Monkey-Head-Project`.
