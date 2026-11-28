"""Static invariants for safely creating an isolated testing2 initramfs."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-initramfs-offline.sh"


def _script() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_pinned_kernel_config_and_vendor_hashes() -> None:
    s = _script()
    for digest in (
        "25a047a9ab044dce4fad765476c51f1c4aa0b37ffcb6c9b759143f0a887692e0",
        "db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3",
        "31113cef510d54e51b593c8a84780342bf8bfadb346dd09d93f2baa893c24c60",
        "49e7714072c73035db08736f2848bf180938614a3c5aee3dd56740bf4e3c7995",
        "076c6b14554a929ced396323574ef6b23edfc79142de0128f5f439ca359ae72a",
        "bcd7b35e78231d36bee6a95c9a40adfd0ca8ca0bc0db52b9f4b02da18fba00e7",
    ):
        assert digest in s


def test_live_modules_and_boot_partition_are_untouched() -> None:
    s = _script()
    assert '[[ ! -e "/lib/modules/$KR" && ! -e "/boot/vmlinuz-$KR" ]]' in s
    assert "--ro-bind / /" in s
    assert "--tmpfs /lib/modules" in s
    assert '--ro-bind "$MODTREE" "/lib/modules/$KR"' in s
    assert '--bind "$WORK" "$WORK"' in s
    assert "--unshare-net" in s
    assert "dpkg-deb --extract" in s
    assert '"$DEPMOD" -a -b "$EXTRACT" "$KR"' in s
    assert "mkinitramfs -d" in s
    assert 'mkinitramfs -d "$CONF" -o "$ARCHIVE" "$KR"' in s


def test_required_configuration_and_md_raid_checks() -> None:
    s = _script()
    assert '"$CONF/scripts"' in s
    assert '"$MODTREE/config-$KR"' in s
    assert "MODULES=list" in s
    for module in (
        "vmd",
        "nvme",
        "nvme_core",
        "md_mod",
        "raid10",
        "btrfs",
        "amdgpu",
        "nvidia",
        "nvidia_uvm",
    ):
        assert module in s
    for path in ("usr/sbin/mdadm", "etc/mdadm/mdadm.conf", "scripts/local-block/mdadm"):
        assert path in s
    assert "nouveau" in s


def test_rejects_overwrites_and_privileged_installation() -> None:
    s = _script()
    assert '[[ ! -e "$p" ]]' in s
    assert "Run without sudo." in s
    forbidden = (
        "sudo ",
        "apt ",
        "dpkg -i",
        "dkms ",
        "make modules_install",
        "update-initramfs ",
        "update-grub ",
        "grub-install ",
        "reboot",
        "modprobe ",
        "insmod ",
        "rmmod ",
        "mount ",
        "umount ",
    )
    for line in s.splitlines():
        line = line.lstrip()
        if not line or line.startswith("#"):
            continue
        assert not line.startswith(forbidden)
