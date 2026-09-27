# Operating System Debloating

For best performance, the Monkey Head Project encourages minimizing unnecessary programs and services before installing Huey. Removing bloat reduces memory and CPU overhead, ensuring that the AI/OS runs smoothly even on older hardware.

## Windows 10 & 11

A complete optimization script is provided at `setup/Windows10/windows-remove-tool.bat`. Run this batch file as **Administrator** after installation to remove default applications, disable telemetry, clean temporary files, and set the High Performance power profile. The script is compatible with both Windows 10 and Windows 11 and can be executed as follows:

```cmd
setup\Windows10\windows-remove-tool.bat
```

This debloating step is optional but recommended for systems dedicated to the project.

## Debian Forky

While no automatic script is supplied for Linux, you can achieve a lightweight Forky installation by uninstalling packages you do not require and disabling unused services:

```bash
sudo apt-get purge libreoffice-* games-* thunderbird
sudo systemctl disable cups.service
```

After cleaning up, update the system and install only the packages listed in `platform/installers/debian/Debian/install-deb.sh`.

## macOS

On macOS, disable resource-heavy animations and remove unnecessary startup items via **System Settings**. Tools like **CleanMyMac** can help remove unneeded applications. Keeping the system lean ensures Huey runs efficiently on Apple hardware.

---

Trimming excess applications and services lets Huey allocate resources where they matter most. For a full walkthrough, see the installation instructions in this repository's `README.md`.
