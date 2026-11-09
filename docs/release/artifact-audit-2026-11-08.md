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

The refreshed tracked-tree inventory at main commit
`9066adf810ab659ed8a53a4cba5d9d64eee9c2f3` contained 1,998 files; ten were at
least 5 MiB. The largest were two initrds (64 and 23 MiB), the archived
`dlrp-old.zip` (23 MiB), kernel images (12 MiB each), a test MP4 (11 MiB), and
two Debian installer packages (10 and 8 MiB). The two duplicate kernel files
have matching SHA-256 values but occupy different boot-layout paths. No payload
was deleted based only on its size or duplicate content.

Names and repository metadata identify the `.udeb` files as Debian packages,
but the audit did not establish the upstream revision, license/NOTICE
obligations, or consumer for every image, initrd, archived ZIP, or test video.
Record those fields per payload before moving, replacing, or removing it. The
artifact scan workflow produces the complete per-file path/size/hash list.

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
rehash or attest. The tagged release workflow would attach `dist/*` after
building and verify `SHA256SUMS` before upload. PyPI provenance does not by
itself attest GitHub's copies of those files.

## Residual decisions

- Keep platform and legacy binary payloads until owners confirm their consumer,
  license/NOTICE, upstream origin, retention, and replacement path.
- The repository-wide inventory is not itself an SBOM; only the Python release
  runtime receives a CycloneDX dependency bill of materials in this change.
- Artifact hashes establish byte identity, not authenticity. Release provenance
  is provided by the existing PyPI Trusted Publishing attestation; future
  GitHub release assets would be checksum-verified but would not yet have a
  separate GitHub build attestation.
- Confirm the generated checksum, SBOM, and provenance records after the next
  package release; this read-only audit does not establish future release
  behavior.
- Ten tracked files over 5 MiB still need a maintainer-reviewed owner,
  upstream-origin, license/NOTICE, and consumer register. Checksums and package
  names alone do not answer those questions.
- No binary/archive payload was removed based only on size or extension.

## Reproduction

Run the `artifact-scan` workflow on a commit and download
`artifact-risk-scan-results/tracked-artifact-inventory.json`. For package
releases, inspect the attached `hueyos-<version>.cdx.json` and `SHA256SUMS`;
the publish job checks the latter before publishing.
