"""Private extraction audit must not change the live kernel or RAID."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-initramfs-content-audit.sh"


def _script() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_pinned_artifact_and_raid_uuids() -> None:
    src = _script()
    assert "ddcc9e6c238a3c744adca38903c5d4ffcf8c4393ee1517576860a85812cb5bdd" in src
    assert "f3c8b907:d3b5a85f:a2578548:157bf1d2" in src
    assert "dddebb01-4f58-4782-82b3-0e77209afc8c" in src
    assert "38a8dd4b:f15c5eca:fafe213a:2962ac03" in src
    assert "subvol=@rootfs" in src


def test_trusted_private_extraction_and_no_overwrite() -> None:
    src = _script()
    assert '[[ "$actual" == "$EXPECTED_IMAGE_SHA" ]]' in src
    assert '[[ ! -e "$p" ]]' in src
    assert 'install -d -m 0700 "$EXTRACT"' in src
    assert "--ro-bind / /" in src
    assert '--bind "$EXTRACT" "$EXTRACT"' in src
    assert '"$UNPACK" "$IMAGE" "$EXTRACT"' in src
    assert '"$EXTRACT/main/init"' in src


def test_reads_embedded_mdadm_resume_and_btrfs_hooks() -> None:
    src = _script()
    for value in (
        "etc/mdadm/mdadm.conf",
        "scripts/local-block/mdadm",
        "scripts/local-bottom/mdadm",
        "scripts/local-premount/btrfs",
        "conf/conf.d/zz-resume-auto",
        "conf/initramfs.conf",
        "conf/modules",
        "/proc/cmdline",
    ):
        assert value in src


def test_no_privileged_system_changes() -> None:
    src = _script()
    banned = (
        "sudo ", "dpkg -i", "mkinitramfs ", "update-initramfs ",
        "update-grub ", "grub-install ", "reboot", "modprobe ",
        "insmod ", "rmmod ", "mount ", "umount ", "mdadm --assemble",
        "mdadm --create", "rm -rf", "mkfs", "wipefs",
    )
    for line in src.splitlines():
        line = line.lstrip()
        if not line or line.startswith("#"):
            continue
        assert not line.startswith(banned)
