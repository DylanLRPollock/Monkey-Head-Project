#!/usr/bin/env bash
# HueyOS testing2: build proprietary NVIDIA 580.196.07 modules OFFLINE.
# No sudo, vendor installer, DKMS, module load/install or reboot.
set -Eeuo pipefail
umask 077

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
pass() { printf 'PASS: %s\n' "$*"; }
[[ "$(id -u)" -ne 0 ]] || fail 'Run without sudo.'

ROOT="$HOME/huey-kernel-734"
SRC="$ROOT/sources/linux-7.3.4"
OBJ="$ROOT/output/testing2-compile"
REPORT="$ROOT/reports/testing2"
STAGE="$ROOT/output/testing2-nvidia-r580"
VENDOR_DIR="$STAGE/NVIDIA-Linux-x86_64-580.196.07"
RUNFILE="$HOME/Downloads/NVIDIA-R580/NVIDIA-Linux-x86_64-580.196.07.run"
BUILD_LOG="$REPORT/nvidia-580.196.07-offline-build.log"
EXTRACT_LOG="$REPORT/nvidia-580.196.07-extract.log"
MANIFEST="$REPORT/nvidia-580.196.07-offline-manifest.txt"
HASHES="$REPORT/nvidia-580.196.07-offline-hashes.txt"
KR='7.3.4-huey-testing2'
DRIVER='580.196.07'

for cmd in sha256sum awk grep find make gcc-16 sh; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing command $cmd"
done
if command -v modinfo >/dev/null 2>&1; then
  MODINFO="$(command -v modinfo)"
elif [[ -x /usr/sbin/modinfo ]]; then
  MODINFO=/usr/sbin/modinfo
else
  fail 'modinfo unavailable; check Debian kmod.'
fi
for file in "$RUNFILE" "$SRC/Makefile" "$OBJ/.config" \
            "$OBJ/include/config/kernel.release" "$OBJ/Module.symvers" \
            "$OBJ/arch/x86/boot/bzImage"; do
  [[ -s "$file" ]] || fail "Required file missing: $file"
done
[[ -d "$REPORT" ]] || fail "Missing report directory: $REPORT"
for path in "$STAGE" "$BUILD_LOG" "$EXTRACT_LOG" "$MANIFEST" "$HASHES"; do
  [[ ! -e "$path" ]] || fail "Already exists: $path. Preserve previous results."
done

hash_is() {
  local current
  current="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$current" == "$2" ]] || fail "Unexpected SHA-256 for $1 ($current)"
}
# The vendor SHA256 is from NVIDIA's own 580.196.07 .sha256sum endpoint.
hash_is "$RUNFILE" 0aab0518db53cf73c412dc7f32bbc850ca95e839d8923d0de4bff42c1c9169ce
hash_is "$OBJ/.config" db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3
hash_is "$OBJ/Module.symvers" 961b5025fe9b1f85c7ac8db166c9b5d16062ce5739af308fe6e0d23fcdf60367
hash_is "$OBJ/arch/x86/boot/bzImage" d020954408a3f70d8f7c630abcf6b5da95583e969a9730e65e59aeed28899855
[[ "$(cat "$OBJ/include/config/kernel.release")" == "$KR" ]] || \
  fail 'Build object kernelrelease does not match expected testing2.'
pass 'Verified NVIDIA vendor SHA256 and exact compiled HueyOS config, symbols and image.'

# NVIDIA .run self-check does not invoke the installer or install driver files.
if ! sh "$RUNFILE" --check >/dev/null 2>&1; then
  fail 'NVIDIA vendor .run --check failed.'
fi
pass 'NVIDIA .run archive integrity check passed.'

install -d -m 700 "$STAGE"
printf '%s\n' 'STEP 1 — Extract proprietary NVIDIA source only (no installer)'
if (cd "$STAGE" && sh "$RUNFILE" --extract-only) >"$EXTRACT_LOG" 2>&1; then
  pass 'Vendor archive extracted to private staging directory.'
else
  tail -n 30 "$EXTRACT_LOG" >&2
  fail 'Vendor extraction failed; preserve staging directory for diagnosis.'
fi
MODULE_SRC="$VENDOR_DIR/kernel"
[[ -f "$MODULE_SRC/Makefile" ]] || fail 'Missing proprietary kernel Makefile in extracted vendor source.'
[[ -f "$MODULE_SRC/nvidia/nv-kernel.o_binary" ]] || \
  fail 'Missing NVIDIA proprietary binary component; do not fall back to kernel-open.'

printf '%s\n' 'STEP 2 — Build modules against the compiled, uninstalled HueyOS kernel'
printf 'Source: %s\nKernel source: %s\nKernel objects: %s\n' \
  "$MODULE_SRC" "$SRC" "$OBJ"
# The make target is modules, NEVER modules_install.
if make -C "$MODULE_SRC" -j4 \
      SYSSRC="$SRC" SYSOUT="$OBJ" KERNEL_UNAME="$KR" \
      CC=gcc-16 HOSTCC=gcc-16 modules >"$BUILD_LOG" 2>&1; then
  pass 'NVIDIA proprietary kernel module compilation command returned success.'
else
  rc=$?
  printf 'NVIDIA build exited %s. Last 60 lines:\n' "$rc" >&2
  tail -n 60 "$BUILD_LOG" >&2
  fail 'NVIDIA R580 may require separately reviewed Linux 7.3 compatibility work; no patch applied.'
fi

printf '%s\n' 'STEP 3 — Inspect produced NVIDIA modules (no install or module load)'
: >"$MANIFEST"
: >"$HASHES"
for name in nvidia nvidia-uvm nvidia-modeset nvidia-drm; do
  path="$(find "$MODULE_SRC" -type f -name "$name.ko" -print -quit)"
  [[ -n "$path" ]] || fail "Expected proprietary $name.ko not generated."
  vermagic="$("$MODINFO" -F vermagic "$path")"
  version="$("$MODINFO" -F version "$path")"
  license="$("$MODINFO" -F license "$path")"
  [[ "$vermagic" == "$KR "* ]] || fail "$name kernel vermagic mismatch: $vermagic"
  [[ "$version" == "$DRIVER" ]] || fail "$name driver version mismatch: $version"
  if [[ "$name" == nvidia ]]; then
    [[ "$license" == NVIDIA* ]] || fail "Core nvidia.ko is not proprietary: $license"
  fi
  printf '%s | version=%s | license=%s | vermagic=%s\n' \
    "$name.ko" "$version" "$license" "$vermagic" >>"$MANIFEST"
  sha256sum "$path" >>"$HASHES"
done
hash_is "$OBJ/.config" db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3
hash_is "$OBJ/Module.symvers" 961b5025fe9b1f85c7ac8db166c9b5d16062ce5739af308fe6e0d23fcdf60367
pass 'Four proprietary NVIDIA 580.196.07 modules match 7.3.4-huey-testing2.'
printf 'Build log: %s\nModule manifest: %s\nModule hashes: %s\n' \
  "$BUILD_LOG" "$MANIFEST" "$HASHES"
printf '%s\n' 'No kernel or NVIDIA modules were installed, signed, loaded or rebooted.'
