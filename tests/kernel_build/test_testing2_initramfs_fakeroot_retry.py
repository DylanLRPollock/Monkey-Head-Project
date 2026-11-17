"""Fail-closed static contract for testing2 rootless fakeroot initramfs retry."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-initramfs-fakeroot-retry.sh"


def _script() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_uses_existing_staging_and_new_reports_only() -> None:
    script = _script()
    assert "testing2-isolated-initramfs-build.log" in script
    assert "testing2-fakeroot-initramfs-build.log" in script
    assert "testing2-fakeroot-initramfs-audit.txt" in script
    assert '[[ ! -e "$f" ]]' in script
    assert '[[ -d "$MODTREE/kernel" && -s "$MODTREE/modules.dep" ]]' in script
    assert "dpkg-deb --extract" not in script
    assert "depmod -a" not in script


def test_fakeroot_and_ownership_probe_are_required_before_generation() -> None:
    script = _script()
    assert "--setenv FAKEROOTDONTTRYCHOWN 1" in script
    assert "sandbox fakeroot -- /bin/sh -c" in script
    assert "cp --reflink=auto --preserve=xattr -fLp" in script
    assert "fakeroot copy probe failed. Do not regenerate initramfs." in script
    assert 'sandbox fakeroot -- /usr/sbin/mkinitramfs' in script
    assert '-d "$CONF" -o "$ARCHIVE" "$KR"' in script


def test_live_host_is_readonly_and_old_modules_are_hidden() -> None:
    script = _script()
    assert "--ro-bind / /" in script
    assert "--unshare-net" in script
    assert "--tmpfs /lib/modules" in script
    assert '--ro-bind "$MODTREE" "/lib/modules/$KR"' in script
    assert '--bind "$RETRY" "$RETRY"' in script
    assert '[[ ! -e "/lib/modules/$KR" && ! -e "/boot/vmlinuz-$KR" ]]' in script
    assert "Run without sudo." in script


def test_checks_raid_hooks_and_no_grub_or_install_command() -> None:
    script = _script()
    for text in (
        "md-mod", "raid10", "btrfs", "vmd", "nvme-core",
        "amdgpu", "nvidia", "nvidia-uvm",
        "usr/sbin/mdadm", "etc/mdadm/mdadm.conf",
        "scripts/local-block/mdadm", "nouveau",
    ):
        assert text in script
    prohibited = (
        "sudo ", "dpkg -i", "make modules_install",
        "update-initramfs ", "update-grub ", "grub-install ",
        "reboot", "modprobe ", "insmod ", "rmmod ", "mount ", "umount ",
        "rm -rf", "mdadm --assemble", "mdadm --create",
    )
    for line in script.splitlines():
        line = line.lstrip()
        if not line or line.startswith("#"):
            continue
        assert not line.startswith(prohibited)
