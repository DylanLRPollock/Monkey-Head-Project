"""Regression tests for in-tree NVIDIA-named versus proprietary R580 modules."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "scripts/kernel/huey-734-testing2-private-no-nvidia.sh"
AUDIT = ROOT / "scripts/kernel/huey-734-testing2-no-nvidia-postcheck.sh"


def _text(path: Path) -> str:
    assert path.is_file()
    assert subprocess.run(
        ["bash", "-n", str(path)], capture_output=True, check=False
    ).returncode == 0
    return path.read_text(encoding="utf-8")


def test_both_scripts_syntax_and_postcheck_immutable_existing_archive() -> None:
    b = _text(BUILDER)
    s = _text(AUDIT)
    assert 'WORK="$STAGE/work/no-nvidia-test1"' in b
    assert 'WORK="$STAGE/work/no-nvidia-test1"' in s
    assert 'ARCHIVE="$WORK/initrd.img-$KR"' in s
    assert '[[ ! -e "$AUDIT" ]]' in s
    assert "cmp -s" in s
    assert "sha256sum" in s
    assert "mkinitramfs" not in "\n".join(
        line for line in s.splitlines() if not line.lstrip().startswith("#")
    )
    for line in s.splitlines():
        line = line.lstrip()
        if not line or line.startswith("#"):
            continue
        assert not line.startswith(
            ("sudo ", "reboot", "mount ", "umount ", "mdadm --assemble",
             "mkfs", "wipefs", "grub-install", "update-initramfs", "rm -rf")
        )


def test_only_exact_proprietary_filenames_match_metadata_gate() -> None:
    # modules.order is a Kbuild index, not the set of initrd files.
    exact = r"(^|/)(nvidia|nvidia-uvm|nvidia-modeset|nvidia-drm)[.]ko([.](xz|gz|zst))?([:[:space:]]|$)"
    benign = (
        "kernel/drivers/usb/typec/altmodes/typec_nvidia.ko\n"
        "kernel/drivers/platform/x86/nvidia-wmi-ec-backlight.ko\n"
    )
    vendor = (
        "updates/nvidia.ko: kernel/drivers/pci/pci.ko\n"
        "updates/nvidia-uvm.ko\n"
        "updates/nvidia-modeset.ko\n"
        "updates/nvidia-drm.ko\n"
    )
    def grep(src: str) -> int:
        return subprocess.run(
            ["grep", "-Ei", exact], input=src, text=True,
            capture_output=True, check=False
        ).returncode
    assert grep(benign) == 1
    assert grep(vendor) == 0
    for s in (_text(BUILDER), _text(AUDIT)):
        assert "nvidia-wmi-ec-backlight" in s
        assert "modules.order" in s
        assert "Proprietary" in s


def test_postcheck_preserves_uuid_and_resume_requirements() -> None:
    s = _text(AUDIT)
    assert "8bce591f673c74d3eeadfc53f8563aa7d20c6f22af2ac7adff4744bcfc6a05b7" in s
    for uuid in (
        "f3c8b907:d3b5a85f:a2578548:157bf1d2",
        "a3068941:490dcc7f:ce9dedcc:6ef270e0",
        "646adf0e:63c18bd3:053728a3:66c836b5",
        "38a8dd4b:f15c5eca:fafe213a:2962ac03",
    ):
        assert uuid in s
    assert "RESUME=none" in s
    assert "nouveau" in s
    assert "VMD" in s
