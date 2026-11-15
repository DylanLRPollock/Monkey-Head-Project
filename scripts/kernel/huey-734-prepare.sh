#!/usr/bin/env bash
# HueyOS 7.3.4 source authentication and Kconfig migration only.
# Not a kernel compile, install, initramfs replacement, BIOS change, or reboot.
set -Eeuo pipefail
umask 077

KVER='7.3.4'
EXPECTED_SHA='b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f'
EXPECTED_BASE_SHA='1d9e4bc522860e2a358bb40f03c56fa4f17d4b0f7f3d6e24cac62fb543a843ed'
GREG_PRIMARY_FPR='647F28654894E3BD457199BE38DBBDC86092693E'
# Immutable repo revision containing the reviewed V100 profile and guard.
REPO_REF='01a8ca7ab2507ab3505302f4fe1269ac542a75bd'
RAW="https://raw.githubusercontent.com/DylanLRPollock/Monkey-Head-Project/${REPO_REF}"
ROOT="$HOME/huey-kernel-734"
DL="$ROOT/downloads"
KEYS="$ROOT/verify-keyring"
SRC="$ROOT/sources/linux-$KVER"
OUT="$ROOT/output/testing1"
REPORT="$ROOT/reports"
AR="$DL/linux-$KVER.tar.xz"
SIG="$DL/linux-$KVER.tar.sign"
SIGNED_INDEX="$DL/sha256sums.asc"
BASE="$HOME/huey-kernel-audit/current-kernel.config"
PROFILE="$DL/v100-workstation.config"
GUARD="$DL/validate_i9_kconfig.py"

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
trap 'printf "Stopped at line %s. Existing Debian boot configuration was NOT modified.\n" "$LINENO" >&2' ERR
[[ "$(id -u)" != 0 ]] || fail 'Do not run as root or via sudo.'
[[ -r "$BASE" ]] || fail "Missing verified base config at $BASE"
for tool in bash curl gpg sha256sum xz tar make gcc-16 python3 awk flex bison; do
  command -v "$tool" >/dev/null 2>&1 || fail "Missing tool: $tool (report this; do not install random packages)"
done
[[ "$(sha256sum "$BASE" | awk '{print $1}')" == "$EXPECTED_BASE_SHA" ]] || \
  fail 'Base .config differs from reviewed Debian 7.2.15 config; do not proceed.'

mkdir -p "$DL" "$ROOT/sources" "$OUT" "$REPORT"
install -d -m 700 "$KEYS"

fetch() {
  local url="$1" dest="$2"
  if [[ ! -s "$dest" ]]; then
    printf 'Downloading %s\n' "${url##*/}"
    curl --fail --location --show-error --retry 3 --proto '=https' \
      --tlsv1.2 --output "$dest.part" "$url"
    mv "$dest.part" "$dest"
  else
    printf 'Using existing %s (will verify)\n' "${dest##*/}"
  fi
}

printf '%s\n' 'STEP 1 — Fetch official release and review inputs'
BASE_URL='https://cdn.kernel.org/pub/linux/kernel/v7.x'
fetch "$BASE_URL/linux-$KVER.tar.xz" "$AR"
fetch "$BASE_URL/linux-$KVER.tar.sign" "$SIG"
fetch "$BASE_URL/sha256sums.asc" "$SIGNED_INDEX"
fetch "$RAW/kernel/huey-linux/profiles/v100-workstation.config" "$PROFILE"
fetch "$RAW/scripts/kernel/validate_i9_kconfig.py" "$GUARD"

printf '%s\n' 'STEP 2 — Verify upstream SHA-256 and its published checksum entry'
actual="$(sha256sum "$AR" | awk '{print $1}')"
[[ "$actual" == "$EXPECTED_SHA" ]] || fail 'Kernel tarball SHA-256 mismatch!'
index_hash="$(awk '$2 == "linux-7.3.4.tar.xz" {print $1}' "$SIGNED_INDEX")"
[[ "$index_hash" == "$EXPECTED_SHA" ]] || fail 'Kernel.org checksum index does not match the expected digest.'
printf 'SHA-256: %s  linux-%s.tar.xz [OK]\n' "$actual" "$KVER"

printf '%s\n' 'STEP 3 — Verify detached tar signature using separate GPG keyring'
if ! gpg --homedir "$KEYS" --batch --no-tty --list-keys gregkh@kernel.org \
  >/dev/null 2>&1; then
  printf '%s\n' 'Locating Greg Kroah-Hartman public key via kernel.org WKD...'
  gpg --homedir "$KEYS" --batch --auto-key-locate wkd \
    --locate-keys gregkh@kernel.org >"$REPORT/gpg-key-fetch.log" 2>&1 || \
    fail "Could not find the official signing key; inspect $REPORT/gpg-key-fetch.log"
fi
primary="$(gpg --homedir "$KEYS" --batch --with-colons --fingerprint \
  gregkh@kernel.org 2>/dev/null | awk -F: '$1=="fpr" {print $10; exit}')"
[[ "$primary" == "$GREG_PRIMARY_FPR" ]] || \
  fail "Unexpected signing-key fingerprint: $primary. Verify independently."
if ! ( set -o pipefail; xz -dc "$AR" | \
    gpg --homedir "$KEYS" --batch --no-tty --verify "$SIG" - \
    >"$REPORT/tar-signature.log" 2>&1 ); then
  fail "Tarball signature verification FAILED; see $REPORT/tar-signature.log"
fi
printf '%s\n' 'Detached PGP signature verified against pinned release-signing key.'

printf '%s\n' 'STEP 4 — Extract verified source, preserving original tarball'
if [[ ! -d "$SRC" ]]; then
  tar -xJf "$AR" -C "$ROOT/sources"
fi
[[ -f "$SRC/Makefile" && -f "$SRC/scripts/kconfig/merge_config.sh" ]] || \
  fail 'Missing expected files in extracted source.'

printf '%s\n' 'STEP 5 — Resolve actual 7.3.4 config (does NOT compile the kernel)'
# Fail closed on an existing .config; an interrupted run is recoverable
# using scripts/kernel/huey-734-resume-config.sh, never by deleting it.
[[ ! -e "$OUT/.config" ]] || \
  fail "Candidate .config exists at $OUT/.config. Use huey-734-resume-config.sh; do not delete or overwrite it."
export ARCH=x86_64
bash "$SRC/scripts/kconfig/merge_config.sh" -m -O "$OUT" "$BASE" "$PROFILE" \
  >"$REPORT/config-merge.log" 2>&1 || \
  fail "Kconfig fragment merge failed; see $REPORT/config-merge.log"
make -C "$SRC" O="$OUT" CC=gcc-16 HOSTCC=gcc-16 \
  LOCALVERSION=-huey-testing1 olddefconfig \
  >"$REPORT/olddefconfig.log" 2>&1 || \
  fail "make olddefconfig failed; see $REPORT/olddefconfig.log"

printf '%s\n' 'STEP 6 — Verify exact release and essential V100/Optane Kconfig'
release="$(make -s -C "$SRC" O="$OUT" CC=gcc-16 HOSTCC=gcc-16 \
  LOCALVERSION=-huey-testing1 kernelrelease)"
[[ "$release" == '7.3.4-huey-testing1' ]] || \
  fail "Unexpected kernelrelease '$release' (must equal 7.3.4-huey-testing1)"
python3 "$GUARD" "$OUT/.config" --stage testing1 \
  >"$REPORT/kconfig-guard.txt" 2>&1 || \
  fail "Critical Kconfig guard FAILED; see $REPORT/kconfig-guard.txt"

printf '%s\n' 'STEP 7 — Write full symbol-level delta report'
python3 - "$BASE" "$OUT/.config" "$REPORT/kconfig-delta.txt" <<'PY'
import re
import sys
from pathlib import Path

pattern_set = re.compile(r'^(CONFIG_[A-Z0-9_]+)=(.*)$')
pattern_unset = re.compile(r'^# (CONFIG_[A-Z0-9_]+) is not set$')
def load(path):
    result = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        a = pattern_set.match(line)
        b = pattern_unset.match(line)
        if a:
            result[a.group(1)] = a.group(2)
        elif b:
            result[b.group(1)] = 'n'
    return result
old, new = load(sys.argv[1]), load(sys.argv[2])
lines = [f'BASELINE: {len(old)} symbols; TARGET: {len(new)} symbols', '']
for category, keys in [
    ('NEW', sorted(new.keys() - old.keys())),
    ('REMOVED', sorted(old.keys() - new.keys())),
    ('CHANGED', sorted(k for k in new.keys() & old.keys() if new[k] != old[k]))
]:
    lines.append(f'{category}: {len(keys)}')
    for key in keys:
        lines.append(f'{key}: {old.get(key, "<absent>")} -> {new.get(key, "<absent>")}')
    lines.append('')
Path(sys.argv[3]).write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('; '.join(line for line in lines if line.startswith(('NEW:', 'REMOVED:', 'CHANGED:'))))
PY
sha256sum "$BASE" "$OUT/.config" "$AR" >"$REPORT/artifact-hashes.txt"
printf '%s\n' 'EXPECTED KERNELRELEASE: 7.3.4-huey-testing1'
printf 'Kconfig: %s\n' "$OUT/.config"
printf 'Reports: %s\n' "$REPORT"
printf '%s\n' 'No kernel compiled, installed, or booted. Upload the report files for review.'
