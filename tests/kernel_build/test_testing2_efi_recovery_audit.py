"""Ensure EFI and mdadm recovery inventory cannot change the live host."""

from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts/kernel/huey-734-testing2-efi-recovery-audit.sh"
)


def _source() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_efi_boot_entry_and_grub_fallback_inspection() -> None:
    source = _source()
    assert "PARTUUID" in source
    assert "sudo blkid -p /dev/sdc1 /dev/sdd1" in source
    assert "sudo wipefs -n /dev/sdd1" in source
    assert "sudo efibootmgr -v" in source
    assert "/boot/efi/EFI/debian/grub.cfg" in source
    assert "/boot/grub/grub.cfg" in source


def test_raid_metadata_inspection_is_read_only() -> None:
    source = _source()
    assert "sudo mdadm --detail --scan" in source
    assert "sudo wipefs -n" in source
    assert "sudo btrfs filesystem show /10TB" in source


def test_no_mutations_or_reboots() -> None:
    source = _source()
    assert '[[ ! -e "$REPORT" ]]' in source
    assert "Run as your normal user, not sudo." in source
    forbidden = (
        "sudo wipefs -a",
        "sudo wipefs -o",
        "sudo mdadm --create",
        "sudo mdadm --assemble",
        "sudo mdadm --stop",
        "sudo efibootmgr -c",
        "sudo efibootmgr -b",
        "sudo grub-install",
        "sudo update-grub",
        "sudo update-initramfs",
        "sudo dpkg -i",
        "sudo mount",
        "sudo umount",
        "reboot",
        "sudo mkfs",
    )
    for line in source.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            assert not any(line.startswith(cmd) for cmd in forbidden)
