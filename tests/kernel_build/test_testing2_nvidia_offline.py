"""Static safety contract for isolated NVIDIA 580.196.07 compatibility builds."""
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts/kernel/huey-734-testing2-nvidia-offline.sh"
)


def _source() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_pinned_vendor_archive_and_exact_target_artifacts() -> None:
    src = _source()
    assert "0aab0518db53cf73c412dc7f32bbc850ca95e839d8923d0de4bff42c1c9169ce" in src
    assert "db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3" in src
    assert "961b5025fe9b1f85c7ac8db166c9b5d16062ce5739af308fe6e0d23fcdf60367" in src
    assert "d020954408a3f70d8f7c630abcf6b5da95583e969a9730e65e59aeed28899855" in src
    assert "7.3.4-huey-testing2" in src


def test_extracts_only_proprietary_vendor_kernel_sources() -> None:
    src = _source()
    assert 'sh "$RUNFILE" --check' in src
    assert 'sh "$RUNFILE" --extract-only' in src
    assert "nvidia/nv-kernel.o_binary" in src
    assert "kernel-open" in src


def test_build_uses_explicit_source_and_output_for_uninstalled_kernel() -> None:
    src = _source()
    assert 'make -C "$MODULE_SRC" -j4' in src
    assert 'SYSSRC="$SRC" SYSOUT="$OBJ" KERNEL_UNAME="$KR"' in src
    assert "CC=gcc-16 HOSTCC=gcc-16 modules" in src
    for name in ("nvidia", "nvidia-uvm", "nvidia-modeset", "nvidia-drm"):
        assert name in src
    assert 'modinfo' in src
    assert '"$vermagic" == "$KR "*' in src


def test_never_installs_loads_or_reboots() -> None:
    src = _source()
    assert "No kernel or NVIDIA modules were installed" in src
    assert '[[ ! -e "$path" ]]' in src
    assert 'umask 077' in src
    forbidden = (
        "sudo ", "apt ", "dpkg -i", "dkms install", "make modules_install",
        "update-initramfs", "update-grub", "grub-install", "reboot",
        "modprobe ", "insmod ", "rmmod ", "nvidia-installer ",
    )
    assert all(
        not line.strip().startswith(forbidden)
        for line in src.splitlines() if not line.strip().startswith("#")
    )
