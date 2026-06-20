# Phase 9 — Rollback Hooks Report

## [R-01] Preserve prior kernel & GRUB entries
- Command: `ls -1 /boot/vmlinuz-* /boot/initrd.img-* | sed 's|^|OK: |'`
- Result: `/boot` is empty in this container image, so the command returned `No such file or directory` errors for both glob patterns. No kernel artifacts were available to archive.

## [R-02] Restore APT sources
- Command sequence: `rsync` from `/root/apt-backup-*` to `/etc/apt` followed by `apt update` and `apt -y full-upgrade`.
- Result: The rsync step exited with code 23 because no `/root/apt-backup-*` directories exist in this environment. `apt update` completed successfully and `apt -y full-upgrade` refreshed 45 packages (systemd, libc, OpenSSL, openssh-client, etc.) to the latest repository revisions available for Ubuntu 24.04 inside the container.

## [R-03] Rebuild the Python virtual environment
- Command sequence: remove `.venv`, create a new virtual environment with `python3.13 -m venv .venv`, activate it, and install `hueyos` with extras `ml`, `data`, and `cloud`.
- Result: Python 3.13.3 was selected via `pyenv`, the virtual environment was created successfully, and activation succeeded. `pip install -e . '.[ml,data,cloud]'` failed with `ResolutionImpossible` because the extras have mutually incompatible pinned dependencies in this repository revision.

