# Debian "Forky" Upgrade Helper

This repository includes a helper script for aligning APT sources with the upcoming Debian 14 ("Forky") suite and refreshing the Microsoft Edge signing key.

## Usage

```bash
sudo tools/upgrade_to_forky.sh
```

The script performs the following tasks:

1. Updates `/etc/apt/sources.list` and any `*.list` files in `/etc/apt/sources.list.d/` to reference the `forky` suite.
2. Installs the Microsoft signing key in `/etc/apt/keyrings/microsoft.gpg` and configures the Microsoft Edge Beta repository (`/etc/apt/sources.list.d/microsoft-edge-beta.list`).
3. Runs `apt update` followed by `apt -y full-upgrade` to bring the system up to date.

The script must be executed as `root` to modify system APT configuration and install packages.
