# Linux 6.18.2 Upgrade Runbook (DKMS-Free)

This guide walks through building and deploying a DKMS-free Linux 6.18.2 kernel with
Apple CS8409 audio support tuned for HueyOS hosts (for example, iMac18,3). It closely
follows the proven playbook used during validation.

## 0. Install build dependencies (one-time)

```bash
sudo apt update
sudo apt install -y build-essential bc bison flex libelf-dev libssl-dev \
  libncurses-dev dwarves pahole rsync xz-utils cpio kmod python3 fakeroot \
  git wget
```

## 1. Fetch 6.18.2 sources and seed configuration

```bash
mkdir -p ~/kernels && cd ~/kernels
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.18.2.tar.xz
tar -xf linux-6.18.2.tar.xz
cd linux-6.18.2

# use the working kernel config as base
cp -v /boot/config-$(uname -r) .config || zcat /proc/config.gz > .config
yes "" | make olddefconfig
```

## 2. Enable required audio modules

Keep HDA as the primary path and retain SOF modules as a fallback.

```bash
# HDA core + codecs
./scripts/config --module CONFIG_SND_HDA_INTEL
./scripts/config --module CONFIG_SND_HDA_GENERIC
./scripts/config --module CONFIG_SND_HDA_CODEC_HDMI
./scripts/config --module CONFIG_SND_HDA_CODEC_CIRRUS
./scripts/config --module CONFIG_SND_HDA_CODEC_CS8409

# helper scodecs (names may be absent)
./scripts/config --module CONFIG_SND_HDA_SCODEC_CIRRUS 2>/dev/null || true
./scripts/config --module CONFIG_SND_HDA_SCODEC_CS35L41 2>/dev/null || true

# SOF modules kept available (blacklist initially)
./scripts/config --module CONFIG_SND_SOC_SOF
./scripts/config --module CONFIG_SND_SOC_SOF_INTEL_PCI
./scripts/config --module CONFIG_SND_SOC_SOF_HDA_COMMON

yes "" | make olddefconfig
```

> Quick check: run `make menuconfig`, press `/`, search for `CS8409` — it should be set to `M`.

## 3. Optional: Secure Boot module signing

Skip if Secure Boot is disabled. This avoids unsigned module issues after reboot.

```bash
mkdir -p ~/keys && cd ~/keys
openssl req -new -x509 -newkey rsa:2048 -keyout MOK.priv -out MOK.pem \
  -nodes -days 36500 -subj "/CN=Huey Kernel Module Key/"
openssl x509 -outform der -in MOK.pem -out MOK.der
sudo mokutil --import MOK.der   # enroll at the next reboot (blue MOK screen)

cd ~/kernels/linux-6.18.2
./scripts/config --enable CONFIG_MODULE_SIG
./scripts/config --enable CONFIG_MODULE_SIG_ALL
./scripts/config --set-str CONFIG_MODULE_SIG_KEY "$(readlink -f ~/keys/MOK.pem)"
yes "" | make olddefconfig
```

## 4. Build and install the kernel

```bash
export LOCALVERSION=-hueyos-v1
make -j"$(nproc)"
sudo make modules_install INSTALL_MOD_STRIP=1
sudo make install

KV=$(make kernelrelease)          # expected: 6.18.2-hueyos-v1
sudo update-initramfs -c -k "$KV"
sudo update-grub
```

## 5. First boot with HDA-only audio (recommended)

Blacklist SOF modules so the in-kernel CS8409 HDA path claims the device cleanly.

```bash
sudo tee /etc/modprobe.d/90-hda-preferred.conf >/dev/null <<'EOF'
blacklist snd_soc_avs
blacklist snd_sof_pci_intel_skl
blacklist snd_sof_pci
blacklist snd_sof
# Apple quirks—disable DMIC, no power-save pops
options snd_hda_intel dmic_detect=0 power_save=0
EOF

sudo update-initramfs -u -k "$KV"
sudo reboot
```

At the GRUB prompt select **6.18.2-hueyos-v1**.

## 6. Verify audio stack after boot

```bash
uname -r
lsmod | egrep 'cs8409|cirrus|snd_hda'
sudo dmesg -T | egrep -i 'cs8409|cirrus|hdaudio|fixup|quirk' | tail -n 200

cat /proc/asound/cards
aplay -l
systemctl --user restart wireplumber pipewire pipewire-pulse
sleep 2
pactl list short cards
pactl list short sinks
pactl set-default-sink 0
amixer -c 0 sset Master 80% unmute 2>/dev/null || true
amixer -c 0 sset Speaker 80% unmute 2>/dev/null || true
amixer -c 0 sset Headphone 80% unmute 2>/dev/null || true
amixer -c 0 sset 'Auto-Mute Mode' Disabled 2>/dev/null || true

speaker-test -c 2 -t pink -l 1
```

If PulseAudio still reports **Dummy Output**, flip to the SOF path:

```bash
sudo rm -f /etc/modprobe.d/90-hda-preferred.conf
sudo apt install -y sof-firmware alsa-ucm-conf
sudo update-initramfs -u -k "$(uname -r)"
sudo reboot

sudo dmesg -T | egrep -i 'sof|cs8409|hdaudio|fixup|quirk' | tail -n 200
aplay -l
pactl list short sinks
speaker-test -c 2 -t pink -l 1
```

## 7. Broadcom Wi-Fi firmware sanity (if needed)

```bash
echo 'deb http://deb.debian.org/debian trixie main contrib non-free-firmware' | \
  sudo tee /etc/apt/sources.list.d/firmware.list
sudo apt update
sudo apt install -y firmware-brcm80211

cd /lib/firmware/brcm
sudo ln -sf brcmfmac43602-pcie.bin        "brcmfmac43602-pcie.Apple Inc.-iMac18,3.bin"
sudo ln -sf brcmfmac43602-pcie.txt        "brcmfmac43602-pcie.Apple Inc.-iMac18,3.txt"
sudo ln -sf brcmfmac43602-pcie.clm_blob   "brcmfmac43602-pcie.Apple Inc.-iMac18,3.clm_blob"
sudo ln -sf brcmfmac43602-pcie.txcap_blob "brcmfmac43602-pcie.Apple Inc.-iMac18,3.txcap_blob"
sudo update-initramfs -u -k "$(uname -r)"
sudo modprobe -r brcmfmac brcmutil
sudo modprobe brcmfmac
```

## 8. Quality-of-life and safeguards

```bash
# keep previous kernel selectable as default
sudo sed -i 's/^GRUB_DEFAULT=.*/GRUB_DEFAULT=saved/' /etc/default/grub
echo 'GRUB_SAVEDEFAULT=true' | sudo tee -a /etc/default/grub
sudo update-grub

# quieter boot logs
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3 splash /' /etc/default/grub
sudo update-grub

# eliminate idle HDA clicks
echo 'options snd_hda_intel power_save=0 power_save_controller=N' | \
  sudo tee /etc/modprobe.d/disable-hda-powersave.conf
sudo update-initramfs -u -k "$(uname -r)"
```

## 9. Troubleshooting checklist

If audio still fails after the first boot, collect the following diagnostics and share them for quirk tuning:

```bash
uname -r
lsmod | egrep 'cs8409|cirrus|snd_hda|sof'
sudo dmesg -T | egrep -i 'cs8409|cirrus|sof|hdaudio|fixup|quirk' | tail -n 300
aplay -l
pactl list short sinks
```

Following this runbook yields a predictable, DKMS-free upgrade to **6.18.2-hueyos-v1** with an in-kernel CS8409 path and a clean fallback to SOF when required.
