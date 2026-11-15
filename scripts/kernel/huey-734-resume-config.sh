#!/usr/bin/env bash
# Resume HueyOS 7.3.4 Kconfig migration after a missing-host-tool failure.
# Intentionally does NOT redo merge_config.sh, download, compile, install,
# update an initramfs, change GRUB, or reboot.
set -Eeuo pipefail
umask 077

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" != 0 ]] || fail "Run as your normal user, not sudo."

ROOT="$HOME/huey-kernel-734"
SRC="$ROOT/sources/linux-7.3.4"
OUT="$ROOT/output/testing1"
REPORT="$ROOT/reports"
AR="$ROOT/downloads/linux-7.3.4.tar.xz"
SIG="$ROOT/downloads/linux-7.3.4.tar.sign"
KEYS="$ROOT/verify-keyring"
GUARD="$ROOT/downloads/validate_i9_kconfig.py"
BASE="$HOME/huey-kernel-audit/current-kernel.config"
EXPECTED_SOURCE_SHA='b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f'
EXPECTED_BASE_SHA='1d9e4bc522860e2a358bb40f03c56fa4f17d4b0f7f3d6e24cac62fb543a843ed'
EXPECTED_FPR='647F28654894E3BD457199BE38DBBDC86092693E'

for command_name in flex bison make gcc-16 sha256sum awk xz gpg python3; do
  command -v "$command_name" >/dev/null 2>&1 || \
    fail "Missing prerequisite: $command_name. For flex/bison: sudo apt install flex bison"
done

for file in "$SRC/Makefile" "$SRC/scripts/kconfig/merge_config.sh" \
            "$OUT/.config" "$GUARD" "$BASE" "$AR" "$SIG"; do
  [[ -r "$file" ]] || fail "Expected file missing: $file"
done

[[ "$(sha256sum "$AR" | awk '{print $1}')" == "$EXPECTED_SOURCE_SHA" ]] || \
  fail "Source archive hash mismatch: do not proceed"
[[ "$(sha256sum "$BASE" | awk '{print $1}')" == "$EXPECTED_BASE_SHA" ]] || \
  fail "Debian base kernel configuration hash mismatch: do not proceed"

fingerprint="$(gpg --homedir "$KEYS" --batch --with-colons --fingerprint \
  gregkh@kernel.org 2>/dev/null | awk -F: '$1=="fpr" {print $10; exit}')"
[[ "$fingerprint" == "$EXPECTED_FPR" ]] || \
  fail "Release signing-key fingerprint mismatch: do not proceed"
mkdir -p "$REPORT"
if ! (set -o pipefail; xz -dc "$AR" | \
      gpg --homedir "$KEYS" --batch --no-tty --verify "$SIG" - \
      >"$REPORT/tar-signature-resume.log" 2>&1); then
  fail "Release source signature did not verify: see tar-signature-resume.log"
fi

export ARCH=x86_64
printf '%s\n' 'Resuming Linux 7.3.4 olddefconfig after preflight...'
# Preserve original error log from prior failed attempt.
if [[ -s "$REPORT/olddefconfig.log" && ! -e "$REPORT/olddefconfig.first-attempt.log" ]]; then
  cp -p "$REPORT/olddefconfig.log" "$REPORT/olddefconfig.first-attempt.log"
fi
if ! make -C "$SRC" O="$OUT" CC=gcc-16 HOSTCC=gcc-16 \
       LOCALVERSION=-huey-testing1 olddefconfig \
       >"$REPORT/olddefconfig.log" 2>&1; then
  tail -n 20 "$REPORT/olddefconfig.log" >&2
  fail "olddefconfig failed: upload $REPORT/olddefconfig.log"
fi

printf '%s\n' 'Checking candidate kernel release and boot chain...'
if ! make -s -C "$SRC" O="$OUT" CC=gcc-16 HOSTCC=gcc-16 \
      LOCALVERSION=-huey-testing1 kernelrelease \
      >"$REPORT/kernelrelease.txt" 2>&1; then
  fail "kernelrelease check failed: upload $REPORT/kernelrelease.txt"
fi
release="$(tail -n 1 "$REPORT/kernelrelease.txt")"
[[ "$release" == '7.3.4-huey-testing1' ]] || \
  fail "Wrong KERNELRELEASE: '$release'; expected 7.3.4-huey-testing1"

if ! python3 "$GUARD" "$OUT/.config" --stage testing1 \
       >"$REPORT/kconfig-guard.txt" 2>&1; then
  cat "$REPORT/kconfig-guard.txt" >&2
  fail "Kconfig safety guard failed: do not compile"
fi

printf '%s\n' 'Writing full Kconfig delta report...'
python3 - "$BASE" "$OUT/.config" "$REPORT/kconfig-delta.txt" <<'PY'
from pathlib import Path
import re
import sys

set_re = re.compile(r"^(CONFIG_[A-Z0-9_]+)=(.*)$")
unset_re = re.compile(r"^# (CONFIG_[A-Z0-9_]+) is not set$")


def load(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        set_match = set_re.match(line)
        unset_match = unset_re.match(line)
        if set_match:
            values[set_match.group(1)] = set_match.group(2)
        elif unset_match:
            values[unset_match.group(1)] = "n"
    return values


old, new = load(sys.argv[1]), load(sys.argv[2])
out = [f"BASELINE: {len(old)} symbols; TARGET: {len(new)} symbols", ""]
for title, symbols in [
    ("NEW", new.keys() - old.keys()),
    ("REMOVED", old.keys() - new.keys()),
    ("CHANGED", {k for k in old.keys() & new.keys() if old[k] != new[k]}),
]:
    sorted_symbols = sorted(symbols)
    out.append(f"{title}: {len(sorted_symbols)}")
    for symbol in sorted_symbols:
        out.append(
            f"{symbol}: {old.get(symbol, '<absent>')} -> "
            f"{new.get(symbol, '<absent>')}"
        )
    out.append("")
Path(sys.argv[3]).write_text("\n".join(out) + "\n", encoding="utf-8")
print("; ".join(line for line in out if line.startswith(("NEW:", "REMOVED:", "CHANGED:"))))
PY
sha256sum "$BASE" "$OUT/.config" "$AR" >"$REPORT/artifact-hashes.txt"

printf '%s\n' 'PASS: Source and signing key verified; candidate Kconfig resolved and guarded.'
printf 'Candidate release: %s\n' "$release"
printf 'Upload the reports in: %s\n' "$REPORT"
printf '%s\n' 'No kernel compiled, installed or booted.'
