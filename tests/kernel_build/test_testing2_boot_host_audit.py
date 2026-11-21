"""Host boot-readiness inventory must remain read-only and unprivileged."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-boot-host-audit.sh"


def _source() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_pinned_config_and_recovery_inventory() -> None:
    s = _source()
    assert "db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3" in s
    for term in (
        "/proc/mdstat", "mdadm --detail --scan", "lsinitramfs",
        "vmd nvme nvme-core md-mod raid0 raid1 raid10 btrfs i915 amdgpu",
        "/boot/vmlinuz-*", "/boot/initrd.img-*",
    ):
        assert term in s


def test_cpu_security_mitigations_and_display_state() -> None:
    s = _source()
    assert "CONFIG_(MITIGATION_RETHUNK|RETHUNK|OBJTOOL_WERROR" in s
    assert "retbleed spec_rstack_overflow spectre_v2" in s
    assert "mokutil --sb-state" in s
    assert "lsmod" in s


def test_no_host_changes() -> None:
    s = _source()
    assert "Run as a normal user, without sudo." in s
    assert '[[ ! -e "$OUT" ]]' in s
    assert "No initramfs generated" in s
    forbidden = (
        "sudo ", "apt ", "dpkg -i", "make ", "mkinitramfs ",
        "update-initramfs ", "update-grub ", "grub-install ",
        "reboot", "modprobe ", "insmod ", "rmmod ", "mdadm --assemble",
        "mdadm --create", "mount ", "umount ",
    )
    assert all(
        not line.lstrip().startswith(forbidden)
        for line in s.splitlines() if not line.lstrip().startswith("#")
    )
