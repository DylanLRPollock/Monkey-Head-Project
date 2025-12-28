#!/usr/bin/env bash
# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Build Huey Iso shell script (huey/memory/SH)

set -euo pipefail

# This script builds a UEFI-only amd64 ISO using Debian live-build
# and a custom Linux kernel version 6.18.2-hueyos-v1. It is adapted from the
# user‑provided instructions while being prepped for the Debian “Forky” /
# kernel 6.18.x migration (comments note the pending switch while earlier
# baselines remain the production floor). Because this container environment
# doesn't provide a Windows filesystem under /mnt/c, the output
# directory (OUTWIN) is pointed at the shared folder so that the ISO
# and its extracted contents can be accessed from outside the
# container. If you are running this on a real WSL system, you may
# wish to change OUTWIN to "/mnt/c/Users/admin/Desktop/${ISO_NAME}".

# --- config ---
ISO_NAME="huey-v1.0-amd64"
KVER="6.18.2"
LOCALVER="-hueyos-v1"
# Output directory set to shared folder rather than Windows desktop.
OUTWIN="${OUTWIN:-/home/oai/share/${ISO_NAME}}"
WORK="$HOME/huey-iso-build"
JOBS="$(nproc)"

echo "Using output directory: $OUTWIN"

# --- prerequisites ---
sudo true
sudo sed -i 's/main$/main contrib non-free non-free-firmware/' /etc/apt/sources.list || true
sudo apt-get update
sudo apt-get install -y \
  build-essential bc bison flex libssl-dev libelf-dev fakeroot dwarves rsync \
  xz-utils tar wget ca-certificates \
  live-build live-tools grub-efi-amd64-bin shim-signed \
  squashfs-tools xorriso mtools dosfstools gdisk

# --- workspace ---
rm -rf "$WORK" && mkdir -p "$WORK"
cd "$WORK"

# --- build kernel 6.18.2 → .debs ---
wget -q https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-${KVER}.tar.xz
tar -xf linux-${KVER}.tar.xz
cd linux-${KVER}
# seed config from running kernel if available
if [ -f "/boot/config-$(uname -r)" ]; then
  cp "/boot/config-$(uname -r)" .config
  yes "" | make olddefconfig
else
  make defconfig
fi
make -j"$JOBS" bindeb-pkg LOCALVERSION="${LOCALVER}" KDEB_PKGVERSION=1
cd ..

# produced in parent dir:
#  linux-image-${KVER}${LOCALVER}_1_amd64.deb
#  linux-headers-${KVER}${LOCALVER}_1_amd64.deb
#  linux-libc-dev_${KVER}-1_amd64.deb
IMG_DEB="linux-image-${KVER}${LOCALVER}_1_amd64.deb"
HDR_DEB="linux-headers-${KVER}${LOCALVER}_1_amd64.deb"
LIBC_DEB="linux-libc-dev_${KVER}-1_amd64.deb"

# --- live-build config (UEFI-only, amd64, Debian 13 “trixie”) ---
BUILD="$WORK/live"
mkdir -p "$BUILD"
cd "$BUILD"

lb config \
  --architectures amd64 \
  --distribution trixie \
  --binary-images iso \
  --bootloader grub-efi \
  --debian-installer live \
  --iso-application "HueyOS" \
  --iso-publisher "Monkey-Head-Project" \
  --iso-volume "${ISO_NAME}" \
  --firmware-binary true \
  --apt-recommends true

# include our kernel packages (installed inside chroot + present on ISO)
mkdir -p config/packages.chroot config/packages.binary
cp "../${IMG_DEB}" "../${HDR_DEB}" "../${LIBC_DEB}" config/packages.chroot/
cp "../${IMG_DEB}" "../${HDR_DEB}" "../${LIBC_DEB}" config/packages.binary/

# ensure our kernel is selected first at boot
mkdir -p config/hooks/normal
cat > config/hooks/normal/90-grub-default.chroot <<'EOF_HOOK'
#!/bin/sh
set -e
update-grub || true
EOF_HOOK
chmod +x config/hooks/normal/90-grub-default.chroot

# put requested top-level folders/files on the ISO root
INC="config/includes.binary"
mkdir -p "${INC}"/{boot,dists,doc,EFI,firmware,huey,install,install.amd,iso,isolinux,live,monkey-head-project,pics,pool,secrets}
# minimal README on the ISO root
cat > "${INC}/README.md" <<'EOF_README'
# Huey ISO
UEFI-only, amd64. Kernel 6.18.2-hueyos-v1. Custom Debian 13 (Trixie) live + installer image for Monkey-Head-Project.
EOF_README

# build
sudo lb clean
sudo lb build

# result filename is usually 'live-image-amd64.hybrid.iso' (even for UEFI-only)
ISO_BUILT="$(ls -1t *.iso | head -n1)"

# --- export to output directory and lay out tree exactly as requested ---
sudo mkdir -p "$OUTWIN"
sudo cp -f "$ISO_BUILT" "${OUTWIN}/${ISO_NAME}.iso"

# extract the ISO contents into the same folder
sudo xorriso -osirrox on -indev "$ISO_BUILT" -extract / "$OUTWIN"

# also place kernel debs at the root with the exact names you want
sudo cp -f "../${HDR_DEB}" "${OUTWIN}/linux-headers-${KVER}_${KVER}-1_amd64.deb"
sudo cp -f "../${IMG_DEB}" "${OUTWIN}/linux-image-${KVER}_${KVER}-1_amd64.deb"
sudo cp -f "../${LIBC_DEB}" "${OUTWIN}/linux-libc-dev_${KVER}-1_amd64.deb"

echo "Wrote: ${OUTWIN}"
ls -la "${OUTWIN}" | sed -n '1,200p'
