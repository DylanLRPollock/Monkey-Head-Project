"""Static boot-chain tests for the HueyOS 7.3.4 VMD + Optane root."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_LIST = ROOT / "kernel" / "huey-linux" / "initramfs" / "modules.list"


def _requested() -> list[str]:
    assert MODULE_LIST.is_file()
    return [
        line.split()[0]
        for line in MODULE_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_all_boot_critical_modules_requested() -> None:
    modules = _requested()
    assert {"vmd", "nvme", "raid10", "btrfs"} <= set(modules)
    assert len(modules) == len(set(modules)), "duplicates obscure module policy"


def test_amd_fallback_preserved_in_testing1() -> None:
    assert "amdgpu" in _requested()


def test_nouveau_is_not_requested() -> None:
    assert "nouveau" not in _requested()
