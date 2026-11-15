#!/usr/bin/env bash
# Generate an independent HueyOS Linux 7.3.4 testing2 candidate with Rust.
# This ONLY writes to ~/huey-kernel-734/output/testing2 and reports/testing2.
# Does not compile vmlinux/modules, install a kernel, change RAID, or reboot.
set -Eeuo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" != 0 ]] || fail 'Run as your normal user, not with sudo.'
ROOT="$HOME/huey-kernel-734"
SRC="$ROOT/sources/linux-7.3.4"
AR="$ROOT/downloads/linux-7.3.4.tar.xz"
TEST1="$ROOT/output/testing1/.config"
OUT="$ROOT/output/testing2"
REPORT="$ROOT/reports/testing2"
GUARD="$ROOT/downloads/validate_i9_kconfig.py"
EXPECTED_ARCHIVE_SHA='b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f'
EXPECTED_TEST1_SHA='1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762'
EXPECTED_RELEASE='7.3.4-huey-testing2'

for cmd in make gcc-16 rustc bindgen sha256sum awk python3; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Required tool missing: $cmd"
done
for file in "$SRC/Makefile" "$SRC/scripts/config" \
            "$TEST1" "$AR" "$GUARD"; do
  [[ -f "$file" ]] || fail "Expected input missing: $file"
done
[[ "$(sha256sum "$AR" | awk '{print $1}')" == "$EXPECTED_ARCHIVE_SHA" ]] || \
  fail 'Verified upstream Linux 7.3.4 source archive no longer matches SHA-256.'
[[ "$(sha256sum "$TEST1" | awk '{print $1}')" == "$EXPECTED_TEST1_SHA" ]] || \
  fail 'Original testing1 config changed: refuse to create testing2.'
[[ ! -e "$OUT" ]] || \
  fail "Testing2 output directory already exists: $OUT (do not overwrite it)."
[[ ! -e "$REPORT" ]] || \
  fail "Testing2 reports already exist: $REPORT (do not overwrite them)."

install -d -m 700 "$OUT" "$REPORT"
cp -- "$TEST1" "$OUT/.config"

export ARCH=x86_64
printf '%s\n' 'STEP 1 — Validate Rust tools (no kernel build)'
if ! make -C "$SRC" O="$OUT" CC=gcc-16 HOSTCC=gcc-16 \
      LOCALVERSION=-huey-testing2 rustavailable \
      >"$REPORT/rustavailable.log" 2>&1; then
  cat "$REPORT/rustavailable.log" >&2
  fail "Rust toolchain unavailable: inspect $REPORT/rustavailable.log"
fi

printf '%s\n' 'STEP 2 — Request CONFIG_RUST=y on a copy of testing1 config'
"$SRC/scripts/config" --file "$OUT/.config" --enable RUST
if ! make -C "$SRC" O="$OUT" CC=gcc-16 HOSTCC=gcc-16 \
      LOCALVERSION=-huey-testing2 olddefconfig \
      >"$REPORT/olddefconfig.log" 2>&1; then
  tail -n 30 "$REPORT/olddefconfig.log" >&2
  fail "Kconfig regeneration failed: inspect $REPORT/olddefconfig.log"
fi
grep -qx 'CONFIG_RUST=y' "$OUT/.config" || \
  fail "Linux 7.3.4 did not retain CONFIG_RUST=y. Inspect toolchain/Kconfig; do not compile."

printf '%s\n' 'STEP 3 — Exact target release and Optane/V100 safety checks'
if ! make -s -C "$SRC" O="$OUT" CC=gcc-16 HOSTCC=gcc-16 \
      LOCALVERSION=-huey-testing2 kernelrelease \
      >"$REPORT/kernelrelease.txt" 2>&1; then
  fail "Cannot resolve target kernelrelease: inspect $REPORT/kernelrelease.txt"
fi
release="$(tail -n 1 "$REPORT/kernelrelease.txt")"
[[ "$release" == "$EXPECTED_RELEASE" ]] || \
  fail "Unexpected kernelrelease '$release'; must equal $EXPECTED_RELEASE"
# Reuse the previously downloaded, pinned testing1-policy validator.
# Its RX 570/V100/Optane checks are identical for testing2; the label
# inside its output is 'testing1' and refers to the unchanged policy.
if ! python3 "$GUARD" "$OUT/.config" --stage testing1 \
      >"$REPORT/kconfig-guard.txt" 2>&1; then
  cat "$REPORT/kconfig-guard.txt" >&2
  fail 'Hardware config safety guard failed. Do not build.'
fi
grep -qx '# CONFIG_MODVERSIONS is not set' "$OUT/.config" || \
  fail 'CONFIG_MODVERSIONS changed from tested NVIDIA baseline; stop.'

printf '%s\n' 'STEP 4 — Compare the original and Rust-enabled candidates'
python3 - "$TEST1" "$OUT/.config" "$REPORT/testing1-to-testing2-delta.txt" <<'PY'
from pathlib import Path
import re
import sys

set_re = re.compile(r"^(CONFIG_[A-Z0-9_]+)=(.*)$")
unset_re = re.compile(r"^# (CONFIG_[A-Z0-9_]+) is not set$")


def load(path: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if m := set_re.match(line):
            result[m.group(1)] = m.group(2)
        elif m := unset_re.match(line):
            result[m.group(1)] = "n"
    return result


before, after = load(sys.argv[1]), load(sys.argv[2])
lines = [
    f"TESTING1: {len(before)} symbols, TESTING2: {len(after)} symbols",
    f"CONFIG_RUST: {before.get('CONFIG_RUST', 'absent')} -> "
    f"{after.get('CONFIG_RUST', 'absent')}",
    "",
]
for title, keys in (
    ("NEW", after.keys() - before.keys()),
    ("REMOVED", before.keys() - after.keys()),
    ("CHANGED", {k for k in before.keys() & after.keys() if before[k] != after[k]}),
):
    keys = sorted(keys)
    lines.append(f"{title}: {len(keys)}")
    for k in keys:
        lines.append(f"{k}: {before.get(k, '<absent>')} -> {after.get(k, '<absent>')}")
    lines.append("")

Path(sys.argv[3]).write_text("\n".join(lines) + "\n", encoding="utf-8")
print("; ".join(s for s in lines if s.startswith(("NEW:", "REMOVED:", "CHANGED:"))))
PY

sha256sum "$TEST1" "$OUT/.config" "$AR" >"$REPORT/artifact-hashes.txt"
[[ "$(sha256sum "$TEST1" | awk '{print $1}')" == "$EXPECTED_TEST1_SHA" ]] || \
  fail 'Original testing1 config changed unexpectedly during preparation!'
printf 'PASS: %s config created with CONFIG_RUST=y.\n' "$EXPECTED_RELEASE"
printf 'Reports: %s\n' "$REPORT"
printf '%s\n' 'No kernel or NVIDIA module compiled, installed or booted.'
