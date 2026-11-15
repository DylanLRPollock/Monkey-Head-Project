#!/usr/bin/env bash
# Read-only: reconcile original compiled hashes with current objects and
# packaged image and headers. NO build, install, kernel, RAID or NVIDIA actions.
set -Eeuo pipefail
umask 077

fail() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
[[ "$(id -u)" -ne 0 ]] || fail 'Run as a regular user, not sudo.'

ROOT="$HOME/huey-kernel-734"
OUT="$ROOT/output"
OBJ="$OUT/testing2-compile"
REPORT="$ROOT/reports/testing2"
ORIGINAL="$REPORT/kernel-compile-hashes.txt"
RESULT="$REPORT/post-package-artifact-reconciliation.txt"
KR="7.3.4-huey-testing2"
VERSION="7.3.4-huey-testing2-1"
IMAGE="$OUT/linux-image-${KR}_${VERSION}_amd64.deb"
HEADERS="$OUT/linux-headers-${KR}_${VERSION}_amd64.deb"

for cmd in awk sha256sum dpkg-deb tar stat grep; do
  command -v "$cmd" >/dev/null 2>&1 || fail "Missing required tool $cmd"
done
for file in "$ORIGINAL" "$OBJ/.config" "$OBJ/arch/x86/boot/bzImage" \
            "$OBJ/vmlinux" "$OBJ/Module.symvers" "$IMAGE" "$HEADERS"; do
  [[ -s "$file" ]] || fail "Required input missing or empty: $file"
done
[[ ! -e "$RESULT" ]] || fail "Existing report $RESULT; preserve before retrying."

# Verify previously audited image and headers package content identifiers.
hash_is() {
  local actual
  actual="$(sha256sum "$1" | awk '{print $1}')"
  [[ "$actual" == "$2" ]] || fail "Unexpected SHA-256 for $1: $actual"
}
hash_is "$IMAGE" 25a047a9ab044dce4fad765476c51f1c4aa0b37ffcb6c9b759143f0a887692e0
hash_is "$HEADERS" bcafa5d683b0f80a524685e281c789e662f72857226bad5a70e6104f6ce7a76a
hash_is "$OBJ/.config" db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3

sha() { sha256sum "$1" | awk '{print $1}'; }
embedded_sha() {
  # Pass --fsys-tarfile straight to tar: streams only, no extraction to host.
  dpkg-deb --fsys-tarfile "$1" | tar -xOf - "$2" | sha256sum | awk '{print $1}'
}

# Compare every original artifact recorded at end of first full compile.
{
  printf 'HueyOS testing2 post-packaging artifact reconciliation\n'
  printf 'Kernel release: %s\n' "$KR"
  printf 'Existing package contents only; no make/install invoked.\n\n'
  printf 'Original hash versus current build-object hash:\n'
  printf '%-17s %-64s %-64s %s\n' "ARTIFACT" "ORIGINAL" "CURRENT" "STATUS"
  drift=0
  for name in config bzImage vmlinux Module.symvers; do
    case "$name" in
      config) file="$OBJ/.config" ;;
      bzImage) file="$OBJ/arch/x86/boot/bzImage" ;;
      vmlinux) file="$OBJ/vmlinux" ;;
      Module.symvers) file="$OBJ/Module.symvers" ;;
    esac
    recorded="$(awk -v f="$file" '$2==f {print $1}' "$ORIGINAL")"
    [[ "$recorded" =~ ^[0-9a-f]{64}$ ]] || fail "No original hash for $name at $file"
    current="$(sha "$file")"
    if [[ "$recorded" == "$current" ]]; then status=SAME; else status=CHANGED; drift=$((drift+1)); fi
    printf '%-17s %-64s %-64s %s\n' "$name" "$recorded" "$current" "$status"
  done
  printf '\nCompiled object files whose SHA changed: %s\n' "$drift"

  printf '\nCompare packaged vmlinuz with current bzImage:\n'
  package_image_sha="$(embedded_sha "$IMAGE" "./boot/vmlinuz-$KR")"
  current_image_sha="$(sha "$OBJ/arch/x86/boot/bzImage")"
  printf 'package vmlinuz SHA: %s\n' "$package_image_sha"
  printf 'object bzImage SHA:   %s\n' "$current_image_sha"
  [[ "$package_image_sha" == "$current_image_sha" ]] || \
    fail 'Packaged kernel image does NOT match current object bzImage.'

  printf '\nCompare packaged headers Module.symvers with current build object:\n'
  package_symvers_sha="$(embedded_sha "$HEADERS" "./usr/src/linux-headers-$KR/Module.symvers")"
  current_symvers_sha="$(sha "$OBJ/Module.symvers")"
  printf 'package Module.symvers SHA: %s\n' "$package_symvers_sha"
  printf 'object Module.symvers SHA:  %s\n' "$current_symvers_sha"
  [[ "$package_symvers_sha" == "$current_symvers_sha" ]] || \
    fail 'Packaged Module.symvers does NOT match the current build object.'

  printf '\nCurrent file timestamps and sizes:\n'
  stat -c '%y | %s bytes | %n' "$OBJ/.config" \
    "$OBJ/arch/x86/boot/bzImage" "$OBJ/vmlinux" "$OBJ/Module.symvers"

  printf '\nPASS: package image and headers symbols match current compiled object tree.\n'
  if ((drift > 0)); then
    printf 'REVIEW: the original post-compile digests changed in %s object(s).\n' "$drift"
    printf 'Do NOT yet build or install NVIDIA; review which object(s) changed.\n'
  else
    printf 'PASS: all original compiled-object hashes are unchanged.\n'
  fi
} > "$RESULT"

cat "$RESULT"
printf '\nReport saved: %s\n' "$RESULT"
