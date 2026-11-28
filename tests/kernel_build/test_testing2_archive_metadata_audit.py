"""Static safety gate for checking the uninstalled testing2 initramfs archive."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-archive-metadata-audit.sh"


def _source() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_archive_sha_and_no_overwrite() -> None:
    source = _source()
    assert "ddcc9e6c238a3c744adca38903c5d4ffcf8c4393ee1517576860a85812cb5bdd" in source
    assert '[[ ! -e "$SUMMARY" && ! -e "$VERBOSE" ]]' in source
    assert "Run as normal user, without sudo." in source


def test_lsinitramfs_verbose_and_metadata_gate() -> None:
    source = _source()
    assert 'lsinitramfs -l "$ARCHIVE"' in source
    assert 'awk -v p="$p"' in source
    for important in (
        "init",
        "etc/mdadm/mdadm.conf",
        "scripts/local-block/mdadm",
        "scripts/local-bottom/mdadm",
        "scripts/local-premount/btrfs",
        "usr/bin/btrfs",
        "usr/sbin/mdadm",
        "nvidia-uvm.ko",
    ):
        assert important in source
    assert "libfakeroot" in source
    assert "resume from" in source


def test_no_runtime_or_host_modification() -> None:
    source = _source()
    forbidden = (
        "sudo ",
        "apt ",
        "dpkg -i",
        "mkinitramfs ",
        "update-initramfs ",
        "update-grub ",
        "grub-install ",
        "unmkinitramfs ",
        "reboot",
        "modprobe ",
        "insmod ",
        "rmmod ",
        "mount ",
        "umount ",
        "rm -rf",
        "mdadm --assemble",
    )
    for line in source.splitlines():
        line = line.lstrip()
        if not line or line.startswith("#"):
            continue
        assert not line.startswith(forbidden)
