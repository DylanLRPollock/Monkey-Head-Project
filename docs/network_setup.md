# Network and Remote Access Setup (Phase 1)

This document records the execution of the Phase 1 networking tasks requested for the
"Network & remote access" phase.

## Firmware and networking packages

* `sudo apt update`
* Attempted to install firmware packages:
  * `sudo apt install -y firmware-linux firmware-misc-nonfree firmware-amd-graphics firmware-iwlwifi network-manager`
  * Result: the firmware packages (`firmware-linux`, `firmware-misc-nonfree`, `firmware-amd-graphics`, `firmware-iwlwifi`) are not available in the Ubuntu 24.04 repositories that are configured in this environment. Installation failed for those packages.
* Installed `network-manager` and related dependencies:
  * `sudo apt install -y network-manager`
  * Result: package installation succeeded, though NetworkManager emitted warnings during post-install due to the container environment lacking a running D-Bus/systemd instance.

## Bonded Ethernet configuration via nmcli

* `nmcli con add type bond ifname bond0 mode 802.3ad`
* `nmcli con add type ethernet ifname enp193s0f0 master bond0`
* `nmcli con add type ethernet ifname enp193s0f1 master bond0`
* `nmcli con mod bond0 ipv4.method auto`
* `nmcli con up bond0`
* Result: all `nmcli` commands failed with `Error: Could not create NMClient object: Could not connect: No such file or directory.` because NetworkManager is not running inside this containerized environment.

## TigerVNC service setup

* Ensured the unit directory exists:
  * `sudo install -d -m 0755 /etc/systemd/system`
* Created `/etc/systemd/system/tigervnc@.service` with the provided configuration.
* Attempted to enable and restart the service:
  * `sudo systemctl enable tigervnc@${USER}.service`
  * `sudo systemctl restart tigervnc@${USER}.service`
* Result: enabling the templated service failed (`multi-user.target is a non-template unit`) and restarting failed because the container does not run `systemd` as PID 1, so `systemctl` cannot communicate with the init system.

## Summary

* Firmware packages requested are unavailable in the configured apt repositories.
* NetworkManager was installed, but it cannot operate without a running systemd/D-Bus environment.
* NMCLI bonding commands cannot complete without NetworkManager running.
* The TigerVNC service unit file was created, but enabling/restarting it is not possible in this container because systemd is not active.

