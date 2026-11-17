"""Guard the third, NVIDIA-free, strictly offline testing2 initramfs."""
from pathlib import Path
import subprocess

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts/kernel/huey-734-testing2-private-no-nvidia.sh"
)


def source() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_bash_syntax() -> None:
    assert subprocess.run(
        ["bash", "-n", str(SCRIPT)], check=False, capture_output=True
    ).returncode == 0


def test_input_pinned_and_output_is_distinct() -> None:
    s = source()
    assert "8bce591f673c74d3eeadfc53f8563aa7d20c6f22af2ac7adff4744bcfc6a05b7" in s
    assert 'WORK="$STAGE/work/no-nvidia-test1"' in s
    assert 'POLICY2="$STAGE/work/fakeroot-policy2"' in s
    assert '[[ ! -e "$p" ]]' in s
    assert '[[ ! -e "/boot/vmlinuz-$KR" && ! -e "/lib/modules/$KR" ]]' in s


def test_no_nvidia_early_modules_and_fail_closed_inspection() -> None:
    s = source()
    assert "vmd nvme nvme_core md_mod raid10 raid1 raid0 btrfs amdgpu" in s
    assert '"$CONF/modules"' in s
    assert '"$LIST"' in s
    assert "NVIDIA module is present in the supposed no-NVIDIA initramfs" in s
    assert "Nouveau unexpectedly present" in s
    assert "NVIDIA early preload still configured" in s
    assert "NVIDIA module dependency or alias leaked into extracted image" in s


def test_raid_and_resume_policies_verified_inside_new_archive() -> None:
    s = source()
    for uuid in (
        "f3c8b907:d3b5a85f:a2578548:157bf1d2",
        "a3068941:490dcc7f:ce9dedcc:6ef270e0",
        "646adf0e:63c18bd3:053728a3:66c836b5",
        "38a8dd4b:f15c5eca:fafe213a:2962ac03",
    ):
        assert uuid in s
    assert 'grep -Exq \'RESUME=none\' "$RESUME"' in s
    assert "Embedded initrd contains stale md3" in s
    assert "Embedded initrd has wrong MD array count" in s
    assert "Root init cpio permissions or ownership are incorrect" in s


def test_bubblewrap_keeps_live_system_read_only() -> None:
    s = source()
    assert "Run as normal user WITHOUT sudo." in s
    assert "--ro-bind / /" in s
    assert '--ro-bind "$MODTREE" "/lib/modules/$KR"' in s
    assert '--bind "$WORK" "$WORK"' in s
    assert '--ro-bind "$POLICY2/mdadm.conf" /etc/mdadm/mdadm.conf' in s
    assert "--unshare-net" in s
    assert "fakeroot -- /usr/sbin/mkinitramfs" in s
    assert "module_blacklist=nvidia,nvidia_uvm,nvidia_modeset,nvidia_drm" in s
    for line in s.splitlines():
        line = line.lstrip()
        if not line or line.startswith("#"):
            continue
        assert not line.startswith(
            ("sudo ", "dpkg -i", "apt ", "update-grub ", "grub-install ",
             "update-initramfs ", "modprobe ", "insmod ", "reboot ",
             "mount ", "umount ", "mdadm --assemble", "mdadm --create",
             "mkfs", "wipefs", "rm -rf")
        )
