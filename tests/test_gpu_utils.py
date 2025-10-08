import math

from monkey_head.utils.gpu import detect_accelerators, recommend_models_for_vram


def test_detect_accelerators_sysfs(tmp_path):
    sys_root = tmp_path / "drm"
    card_dir = sys_root / "card0" / "device"
    card_dir.mkdir(parents=True)
    (card_dir / "vendor").write_text("0x1002")
    (card_dir / "uevent").write_text("PCI_SLOT_NAME=0000:01:00.0\n")
    total = 8 * 1024**3
    used = 2 * 1024**3
    (card_dir / "mem_info_vram_total").write_text(str(total))
    (card_dir / "mem_info_vram_used").write_text(str(used))

    accelerators = detect_accelerators(sys_root=sys_root)
    assert len(accelerators) == 1
    info = accelerators[0]
    assert info.vendor == "AMD"
    assert info.backend in {"rocm", "unknown"}
    assert info.vram_total == total
    assert math.isclose(info.vram_free or 0, total - used, rel_tol=0, abs_tol=1)


def test_recommend_models_for_vram():
    small = recommend_models_for_vram(3 * 1024**3)
    medium = recommend_models_for_vram(12 * 1024**3)
    large = recommend_models_for_vram(48 * 1024**3)
    assert small
    assert medium != small
    assert large != medium
