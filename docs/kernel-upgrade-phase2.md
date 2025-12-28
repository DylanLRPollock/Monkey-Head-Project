# Kernel Upgrade Phase 2 (6.18.x Jump)

This record captures the requested Phase 2 kernel upgrade activities. The work was
performed inside the kata container, which limits kernel management features (no
bootloader access, no running systemd instance, and no audio stack).

## K-01 — Install distro kernel 6.18.x (baseline)

* `sudo apt update`
  * Completed successfully; the package lists refreshed without error.
* `sudo apt install -y linux-image-amd64 linux-headers-amd64`
  * Failed because the Ubuntu 24.04 mirrors in this environment do not publish
    the `linux-image-amd64` or `linux-headers-amd64` meta-packages yet. Apt
    reports "no installation candidate" for both packages, so no kernel was
    installed.
* `uname -r`
  * Still reports `6.12.13`, confirming that the runtime kernel remained
    unchanged after the failed installation attempt.

## K-02 — Install packaged 6.18.2-hueyos-v1 build

Custom Huey kernel packages are not available in this environment. As a result the
`dpkg -i` and `update-initramfs` steps were not executed.

## K-03 — iMac 5K audio mitigation (post-boot)

The container does not provide PulseAudio/PipeWire services or expose iMac audio
hardware. Creating and testing the proposed `huey-audio-setup.sh` autostart script
was therefore skipped.

## K-04 — iio-sensor-proxy service masking

* `sudo install -d -m 0755 /etc/systemd/system`
  * Directory already exists; command completed with no changes.
* `sudo systemctl mask iio-sensor-proxy.service`
  * `systemctl` created the `/etc/systemd/system/iio-sensor-proxy.service ->
    /dev/null` symlink. The container lacks a running systemd instance, so this
    only records the mask on disk; it cannot be exercised within the kata.
