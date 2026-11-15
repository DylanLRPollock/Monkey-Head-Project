"""Safeguards for read-only audits of previously built Debian artifacts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-audit-packages.sh"


def _script() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_accounts_for_all_four_expected_packages() -> None:
    source = _script()
    for name in (
        "linux-image-7.3.4-huey-testing2",
        "linux-headers-7.3.4-huey-testing2",
        "linux-image-7.3.4-huey-testing2-dbg",
        "linux-libc-dev",
    ):
        assert name in source
    assert '[[ "$all_count" -eq 4 ]]' in source
    assert '"$actual_version" == "$VERSION"' in source
    assert '"$arch" == amd64' in source


def test_pinned_hashes_and_hardware_modules() -> None:
    source = _script()
    assert "b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f" in source
    assert "db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3" in source
    for module in ("vmd.ko.xz", "nvme.ko.xz", "nvme-core.ko.xz",
                   "raid10.ko.xz", "btrfs.ko.xz",
                   "i915.ko.xz", "amdgpu.ko.xz"):
        assert module in source
    assert "Module.symvers" in source


def test_does_not_rebuild_install_or_overwrite_old_reports() -> None:
    source = _script()
    assert '[[ ! -e "$MANIFEST" && ! -e "$HASHES" ]]' in source
    assert "dpkg-deb --contents" in source
    assert "Suspicious key/certificate path" in source
    for line in source.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert not any(
            line.startswith(command)
            for command in ("make ", "sudo ", "apt ", "dpkg -i",
                            "update-initramfs", "update-grub", "reboot",
                            "grub-install", "modprobe")
        )
