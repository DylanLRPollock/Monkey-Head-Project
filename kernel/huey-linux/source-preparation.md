# HueyOS 7.3.4 — source authentication and configuration migration

**Status:** Source version and digest established from kernel.org; local
artifact signature verification, source extraction and `olddefconfig` are
operator-run gates. **No kernel is built, installed or booted here.**

## Provenance

- Upstream release: Linux 7.3.4, released 2026-11-10.
- Download: https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.3.4.tar.xz
- Detached signature (covers the **uncompressed tar**, not `.tar.xz`):
  https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.3.4.tar.sign
- Kernel.org checksum index:
  https://cdn.kernel.org/pub/linux/kernel/v7.x/sha256sums.asc
- SHA-256 published for the compressed `linux-7.3.4.tar.xz`:
  `b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f`
- Expected release signer: Greg Kroah-Hartman
  `647F 2865 4894 E3BD 4571 99BE 38DB BDC8 6092 693E`, cross-check
  against https://www.kernel.org/signature.html.
- The kernel.org `sha256sums.asc` is signed by its archive autosigner,
  **not necessarily the release developer**; we verify the release
  developer's detached `.tar.sign` using a separate local GPG keyring.

## On the i9 (non-root)

The reviewed Debian 7.2.15 kernel configuration must be stored in
`~/huey-kernel-audit/current-kernel.config` with SHA-256
`1d9e4bc522860e2a358bb40f03c56fa4f17d4b0f7f3d6e24cac62fb543a843ed`.

Download the versioned preparation script from this development branch:

```bash
cd ~/huey-kernel-audit
curl -fL https://raw.githubusercontent.com/DylanLRPollock/Monkey-Head-Project/feature/huey-kernel-7.3.4/scripts/kernel/huey-734-prepare.sh -o huey-734-prepare.sh
bash -n huey-734-prepare.sh
bash huey-734-prepare.sh
```

The preparation script creates a private working directory
`~/huey-kernel-734` on the existing `/home` RAID0, downloads only the
specified kernel.org and immutable-revision GitHub inputs, verifies the
archive hash and developer PGP signature, extracts into the user home,
merges the reviewed V100 profile, executes `make olddefconfig` (not a
kernel build), checks exact `KERNELRELEASE`, runs the Kconfig boot guard,
and produces a full symbol delta and audit hashes.

## Recovery if `make olddefconfig` stopped because `flex` was missing

The verified 7.3.4 source tarball, GPG signature and profile merge were
already successful. The interrupted run leaves
`~/huey-kernel-734/output/testing1/.config` on disk, so **do not rerun
the original prepare script**: it intentionally rejects overwriting the
existing config. Do not delete it.

On Debian Forky, install the two lexer/parser generators:

```bash
sudo apt install flex bison
```

Then fetch the separate, read-only-to-host resume script and run it as
a normal user:

```bash
cd ~/huey-kernel-audit
curl -fL https://raw.githubusercontent.com/DylanLRPollock/Monkey-Head-Project/feature/huey-kernel-7.3.4/scripts/kernel/huey-734-resume-config.sh -o huey-734-resume-config.sh
bash -n huey-734-resume-config.sh
bash huey-734-resume-config.sh
```

The resume script verifies the pinned source archive and Greg
Kroah-Hartman's detached release signature again, checks the original
baseline config hash, re-runs only `olddefconfig`, verifies the exact
kernel release, runs the VMD/NVMe/RAID10/Btrfs + GPU safety guard, then
generates a Kconfig symbol delta. It preserves the original failed
`olddefconfig` log as `olddefconfig.first-attempt.log`.

An unsuccessful attempt may reveal another missing host-side dependency.
Report the error or upload the new `olddefconfig.log`; do not disable a
required Kconfig feature to mask a tool problem.

**Do not use sudo.** Errors are intentionally blocking. For example,
a missing PGP key, fingerprint mismatch, wrong SHA-256, unsupported
toolchain, missing VMD/RAID10/Btrfs symbol, unexpected release suffix
or already-created candidate config aborts without installing anything.
If it reports an error, share that error and its referenced report
instead of bypassing a safety gate.

On completion, share these three text reports:
- `~/huey-kernel-734/reports/olddefconfig.log`
- `~/huey-kernel-734/reports/kconfig-guard.txt`
- `~/huey-kernel-734/reports/kconfig-delta.txt`

Also share `config-merge.log` and `tar-signature.log` if a gate fails.
The complete candidate `~/huey-kernel-734/output/testing1/.config`
should be reviewed privately before the first compile.

The user has now independently downloaded and authenticated the Linux
7.3.4 source archive. `source.lock.json` is **pinned** to the SHA-256
recorded above, with kernel.org detached release-signature provenance.
This proves source authenticity, not build compatibility or approval.

**Important system constraints:** Do not touch Intel VMD, Optane RAID10,
Btrfs root `@rootfs`, existing GRUB/kernel entries, AMD RX 570 display
fallback, V100 R580 driver or CUDA 12.9 during this step. `/home` itself
is RAID0 and is not backed up automatically; save important reports to
durable storage before any later hardware or boot changes.
