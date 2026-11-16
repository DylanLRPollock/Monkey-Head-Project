"""Read-only preflight for privately staging the testing2 initramfs."""
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts/kernel/huey-734-testing2-initramfs-preflight.sh"
)


def _script() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_target_stays_uninstalled() -> None:
    script = _script()
    assert '[[ -e "/lib/modules/$KR" ]]' in script
    assert "No kernel installed" in script
    assert 'IMAGE="$ROOT/output/linux-image-${KR}_${KR}-1_amd64.deb"' in script
    assert "\\${" not in script
    assert '[[ ! -e "$REPORT" ]]' in script


def test_checks_mount_isolation_and_grub_bridge() -> None:
    script = _script()
    assert "unshare --user --map-root-user -- true" in script
    assert "bwrap --ro-bind / /" in script
    assert "mkinitramfs --supported-target-version=" in script
    assert "/boot/efi/EFI/debian/grub.cfg" in script
    assert "/boot/grub/grub.cfg" in script


def test_does_not_build_or_modify_live_host() -> None:
    script = _script()
    for line in script.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert not any(line.startswith(command) for command in (
            "sudo ", "apt ", "dpkg -i", "make ", "mkinitramfs -o",
            "update-initramfs ", "update-grub ", "grub-install ",
            "reboot", "modprobe ", "insmod ", "rmmod ", "mdadm --assemble",
            "mdadm --create", "mount ", "umount ", "rm -rf",
        ))
