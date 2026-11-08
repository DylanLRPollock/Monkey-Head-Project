# Release artifact audit (2026-11-08)

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

## Python release bundle

The release workflow builds one wheel and one sdist, verifies package files
and the wheel version, installs both into fresh environments, and performs
import/console-script smoke checks. It now also emits a reproducible CycloneDX
1.6 JSON SBOM for the installed wheel environment, generates a SHA-256 manifest
after the full release artifact set is assembled, verifies that manifest in
the build job, and verifies it again after artifact download in the publish
job. The package publisher continues to create PyPI provenance attestations.

## Residual decisions

- Keep platform and legacy binary payloads until owners confirm their consumer,
  license/NOTICE, upstream origin, retention, and replacement path.
- The repository-wide inventory is not itself an SBOM; only the Python release
  runtime receives a CycloneDX dependency bill of materials in this change.
- Artifact hashes establish byte identity, not authenticity. Release provenance
  is provided by the existing PyPI Trusted Publishing attestation; GitHub
  release assets are checksum-verified but do not yet have a separate signed
  attestation.
- No binary/archive payload was removed based only on size or extension.

## Reproduction

Run the `artifact-scan` workflow on a commit and download
`artifact-risk-scan-results/tracked-artifact-inventory.json`. For package
releases, inspect the attached `hueyos-<version>.cdx.json` and `SHA256SUMS`;
the publish job checks the latter before publishing.
