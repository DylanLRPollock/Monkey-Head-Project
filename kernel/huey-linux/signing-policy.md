# HueyOS Secure Boot Signing Policy

This document records the operator-facing policy for signing the HueyOS
custom kernel, its modules, and its initramfs under UEFI Secure Boot. It is
the prose counterpart to the enforced rules in
`src/huey/kernel_build/signing.py` (Step 18 of the handoff) and
`src/huey/kernel_build/policy.py` (Step 5).

If the two ever disagree, **the code wins** and this document is corrected.
Nothing in this document relaxes a check enforced by the code.

---

## 1. Scope

This policy applies to:

- the custom kernel image produced by `kernel_builder.py` (Step 12);
- the NVIDIA proprietary modules staged by `nvidia_builder.py` (Step 14);
- the target-version initramfs produced by `initramfs_builder.py` (Step 17);
- every other kernel module that a target host might need to load under
  Secure Boot on the HueyOS kernel.

It does **not** apply to:

- the running Debian installation's own kernel or modules (these are signed
  by Debian's signing infrastructure and are trusted by the shim);
- user-space binaries, which are not signed by the kernel's module-signing
  mechanism;
- firmware blobs, which have a separate provenance chain.

---

## 2. Key material: never in Git

The signing key (`MOK.priv`) and the signing certificate (`MOK.der` or
`MOK.pem`) **must never be committed to the repository**, uploaded to a
GitHub release, embedded in CI artifacts, pasted into issue trackers, or
stored in any location that a `git clone` or `git log` can reach.

This is enforced by:

- `policy.py::check_signing_readiness` — refuses to proceed if signing is
  required and no key/cert path is supplied;
- `signing.py::Signer._validate_material` — checks that the supplied paths
  exist but **never reads, hashes, logs, or copies the private key**;
- `release.py::_build_plan` — refuses to include any file with a
  secret-bearing filename (`.priv`, `.p12`, `.pfx`, `id_rsa`, …) or any file
  whose text-like contents match a PEM private-key block;
- `.gitignore` (Step 31) — includes `*.priv`, `*.p12`, `*.pfx`, `MOK.*`, and
  `id_*` so that accidental `git add` of a key file is caught locally.

### Recommended storage

Keys belong in an operator-controlled location **outside** the working tree,
for example:

```
~/huey-secureboot/MOK.priv   # 0400, root-owned or operator-owned
~/huey-secureboot/MOK.der    # 0444, public
~/huey-secureboot/README     # describes rotation and recovery
```

### Recommended ownership and mode

| File | Owner | Mode | Notes |
|---|---|---|---|
| `MOK.priv` | operator (or `root`) | `0400` | readable only by the signer |
| `MOK.der` | operator | `0444` | public certificate; can be distributed |
| `MOK.pem` | operator | `0444` | if PEM form is preferred for `mokutil` |
| `README` (local) | operator | `0600` | notes on rotation and recovery |

`signing.py` does not enforce the mode, but `test-hardware.sh` (Step 27)
and the runbook (Step 29) include a manual review step for the operator to
confirm that the private key is not world-readable.

### Passphrase handling

The signing key's passphrase is passed to `scripts/sign-file` through the
environment variable `KBUILD_SIGN_PIN` — **never** in argv, never in a
command-line log. `runner.py::redact_environment` (Step 4) masks any
environment variable whose name contains `PIN` so that `CommandResult`
records it as `<redacted>`.

The CLI (`sign` subcommand, Step 21) accepts `--use-env-pin` to read the
value from `$KBUILD_SIGN_PIN`, or forwards the pin via the environment
unmodified. The pin is **never** printed to stdout or stderr, and never
written to any file the framework controls.

---

## 3. Signature process

Signing happens in a discrete, auditable phase after `nvidia_builder.py`
(Step 14) has staged the modules and after `initramfs_builder.py` (Step 17)
has produced the initramfs, if the boot chain requires signing the initramfs
itself.

### 3.1 Module signing

Each module is copied to a private `signed-modules/` output directory
and that **copy** is signed using the kernel tree's `scripts/sign-file`:

```
scripts/sign-file sha256 MOK.priv MOK.der <module.ko>
```

The source `.ko` files under the caller-supplied staging directory remain
**unchanged**. Only their isolated signing copies are mutated. `signing.py`
recomputes the signed copies' SHA-256 and returns their `BuildArtifact`
records; the release manifest (Step 20) records the **signed** hashes.
The original DKMS/vendor sources remain untouched.

### 3.2 Kernel image signing

If the boot chain requires a signed kernel EFI image, `signing.py` invokes
`sbsign` into a signed copy under the caller's output directory. The
original image is not modified.

### 3.3 Verification

Every signature is verified before being accepted:

- module: `modinfo <module.ko>` must report a `signer:` field and a
  `sig_key:` field, and the `sig_key` fingerprint must match the SHA-256
  fingerprint of the supplied certificate. A mismatch is a **CRITICAL**
  finding;
- kernel image: `sbverify --cert MOK.der <vmlinuz.signed>` must succeed;
- when a required tool is unavailable (`modinfo`, `openssl`, `sbverify`),
  the verification records a finding instead of silently passing.

`signing.py::evaluate_readiness` combines these checks into a single
`boot_ready` boolean. Under Secure Boot, `boot_ready=True` requires every
required module to be signed by the expected certificate. Any missing or
wrong signature forces `boot_ready=False`.

---

## 4. MOK enrollment: manual and human-run

Enrollment of the signing certificate into the target machine's MOK
database is **never** automated by the build framework. It is performed
manually by the operator as part of the human-run install procedure
(Step 29).

`signing.py` provides `plan_mok_enrollment(cert_path)` which returns a
`MokEnrollmentPlan` describing the exact `mokutil --import` command and the
reboot flow. It does **not** run that command. The structural proof is in
`tests/kernel_build/test_signing.py::test_signer_never_calls_mokutil_import`.

### 4.1 Enrollment procedure

The operator runs, on the target workstation, with the certificate available:

```
mokutil --import ~/huey-secureboot/MOK.der
```

`mokutil --import` **queues** the request; it does not enroll the key
immediately. The operator is prompted for a one-time password. That password
is used **at the next reboot**, in the MOK Manager screen. Record it
somewhere safe; it is not needed again after successful enrollment.

At the next reboot:

1. The firmware shows the blue MOK Manager screen.
2. Choose **Enroll MOK** → **Continue** → **Yes**.
3. Enter the one-time password recorded above.
4. Choose **Reboot**.

Until enrollment completes, the target kernel will refuse to load modules
signed with this certificate under Secure Boot — the modules will load as
unsigned (which `CONFIG_MODULE_SIG_FORCE` would reject) or fail with
`Key was rejected by service`.

### 4.2 Verification after enrollment

After enrollment, on the target:

```
mokutil --list-enrolled | grep -A2 "SHA256 Fingerprint"
```

The fingerprint listed must match the SHA-256 fingerprint of `MOK.der`. The
Fingerprint format used by `mokutil` (colon-separated uppercase hex) matches
what `signing.py::Signer._certificate_fingerprint` computes from the public
certificate.

---

## 5. Secure Boot and GRUB caveats

### 5.1 What Secure Boot trusts

Under Secure Boot, the firmware validates:

- the bootloader chain (shim → GRUB → kernel);
- kernel modules when `CONFIG_MODULE_SIG_FORCE=y` is set, or when the
  module's signature chains to a key in the target's trust database.

The HueyOS custom kernel is **not** signed by Microsoft's UEFI CA and is
**not** signed by Debian's UEFI CA. For it to boot, one of the following
must be true:

1. The operator has enrolled a MOK key that signs the kernel EFI image
   (the default path described in §4); **or**
2. The boot chain is configured to boot the custom kernel via a trusted
   chain (e.g. shim → GRUB → kernel with `shim_lock` disabled) — this is
   outside the default HueyOS flow and requires separate review.

The default HueyOS flow uses **option 1**.

### 5.2 GRUB entries

Adding a GRUB entry for the custom kernel is done by the runbook
(Step 29), never by a build step. The entry must:

- reference the signed kernel image path;
- leave the existing Debian kernel entry intact as a fallback;
- not modify the default boot entry without operator confirmation.

The build framework never touches `/etc/grub.d/`, `/boot/grub/grub.cfg`, or
the `grubenv` file.

### 5.3 shim and `mokutil` versions

The `shim` and `mokutil` packages must be recent enough to support the
enrollment flow above. This is a target-host prerequisite; the runbook
(Step 29) includes a preflight check.

### 5.4 Firmware-specific caveats

Some firmware implementations handle MOK enrollment differently or not at
all. If the target workstation's firmware does not show the MOK Manager
screen after `mokutil --import`, the operator should:

- confirm Secure Boot is enabled (`mokutil --sb-state` reports
  `SecureBoot enabled`);
- confirm the `shim` chain is being booted (not the firmware's default
  direct-boot path for the kernel);
- fall back to a firmware-mediated key enrollment (vendor-specific;
  outside the scope of this policy).

**The HueyOS framework does not provide, endorse, or document a way to
disable Secure Boot.** If a target cannot boot signed modules through MOK,
the operator must resolve the firmware/shim configuration. The framework
does not add a "disable Secure Boot to make the build pass" option, and
`policy.py::check_signing_readiness` fails closed if signing is required and
material is missing.

---

## 6. Unsigned-module failure policy

The framework treats unsigned required modules as a **blocking** condition
whenever Secure Boot is enabled or `signing.required_policy = required`:

| Condition | `boot_ready` | Enforced by |
|---|---|---|
| Secure Boot enabled + unsigned required module | `False` | `signing.py::evaluate_readiness` |
| Secure Boot enabled + module signed by wrong key | `False` (CRITICAL) | `signing.py::verify_module_signature` |
| Secure Boot enabled + required kernel image unsigned | `False` | `signing.py::evaluate_readiness` |
| Secure Boot enabled + signing material absent | `False` | `signing.py::evaluate_readiness` |
| `signing.required_policy = required` + material absent | `False` | `policy.py::check_signing_readiness` |
| Secure Boot state unknown | `False` + WARNING | `policy.py` / `verifier.py` |

`verifier.py` (Step 19) enforces the same rules on the assembled release
directory. `release.py` (Step 20) refuses to package a release when the
`VerificationResult` reports `boot_ready=False`.

The operator can inspect the specific finding via:

```
python3.13 -m huey.kernel_build.cli verify --release-dir <release> --json
```

Findings include the exact reason (e.g. `REQUIRED_MODULE_UNSIGNED`,
`MODULE_SIGNED_BY_WRONG_KEY`) and the affected module name.

---

## 7. Rotation and revocation

### 7.1 Rotating the signing key

1. Generate a new keypair **outside** the repository. Keep the old one until
   the new one is enrolled and verified.
2. Sign new builds with the new key. The manifest's `cert_fingerprint` will
   change; the runbook (Step 29) documents how to update any operator-side
   expectations.
3. Enroll the new MOK certificate on each target as described in §4.
4. Sign a test build and confirm it boots under Secure Boot on the target.
5. Only then remove the old MOK enrollment (`mokutil --delete`).

Rotation does **not** require touching previously signed artifacts; the
signatures chain to the certificate that was valid at signing time, and the
target's MOK database decides which certificates it trusts.

### 7.2 Revoking a compromised key

If a private key is compromised:

1. Immediately remove the corresponding MOK enrollment from every target:
   `mokutil --delete MOK.der` (queues removal, effective after reboot).
2. Rotate to a new key as in §7.1.
3. Re-sign every artifact that was signed with the compromised key.
4. Rebuild the affected releases. `release.py` will record new signatures
   and the new certificate fingerprint in the manifest.

The build framework does not provide automatic revocation; it is a manual
operation because it affects live targets.

---

## 8. What the framework never does

To make the boundary between automation and human action explicit:

- **Never** reads, hashes, logs, or copies `MOK.priv`.
- **Never** writes a pin, key, or certificate to a file the framework
  controls.
- **Never** runs `mokutil --import` or `mokutil --delete`.
- **Never** modifies the target's MOK database as a side effect.
- **Never** modifies `/etc/grub.d/`, `/boot/grub/grub.cfg`, or the default
  boot entry.
- **Never** disables Secure Boot.
- **Never** proceeds with a release when a required module is unsigned
  under Secure Boot.
- **Never** claims `boot_ready=True` on the basis of a signed module whose
  signature was not verified against the expected certificate.

Every one of these commitments is mirrored by a test in
`tests/kernel_build/test_signing.py` (Step 18), `test_verifier.py`
(Step 19), `test_release.py` (Step 20), or `test_signing_policy_doc.py`
(this step).

---

## 9. References

- Handoff: `HueyOS_Custom_Kernel_Agent_Handoff.md` §Phase C, Step 18.
- Step 5 policy module: `src/huey/kernel_build/policy.py`.
- Step 18 signing module: `src/huey/kernel_build/signing.py`.
- Step 19 verifier: `src/huey/kernel_build/verifier.py`.
- Step 20 release assembler: `src/huey/kernel_build/release.py`.
- Step 21 CLI: `src/huey/kernel_build/cli.py`.
- Debian wiki, Secure Boot: https://wiki.debian.org/SecureBoot
- Debian wiki, DKMS and Secure Boot: https://wiki.debian.org/DkmsPackaging
- Linux kernel documentation, module signing:
  `Documentation/admin-guide/module-signing.rst` in the pinned source.
- `mokutil(1)` man page on the target host.
