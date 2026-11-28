"""Static safety and provenance checks for post-packaging reconciliation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-artifact-reconcile.sh"


def _script() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_four_original_artifacts_are_compared() -> None:
    source = _script()
    assert "for name in config bzImage vmlinux Module.symvers" in source
    assert 'awk -v f="$file"' in source
    assert "kernel-compile-hashes.txt" in source


def test_known_packages_and_configs_are_pinned() -> None:
    source = _script()
    assert "25a047a9ab044dce4fad765476c51f1c4aa0b37ffcb6c9b759143f0a887692e0" in source
    assert "bcafa5d683b0f80a524685e281c789e662f72857226bad5a70e6104f6ce7a76a" in source
    assert "db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3" in source


def test_image_and_headers_match_build_objects() -> None:
    source = _script()
    assert 'embedded_sha "$IMAGE" "./boot/vmlinuz-$KR"' in source
    assert (
        'embedded_sha "$HEADERS" "./usr/src/linux-headers-$KR/Module.symvers"' in source
    )
    assert "current_image_sha" in source
    assert "current_symvers_sha" in source
    assert "Do NOT yet build or install NVIDIA" in source


def test_read_only_and_prevents_report_overwrites() -> None:
    source = _script()
    assert '[[ ! -e "$RESULT" ]]' in source
    assert "dpkg-deb --fsys-tarfile" in source
    for line in source.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert not any(
            line.startswith(command)
            for command in (
                "sudo ",
                "apt ",
                "make ",
                "dpkg -i",
                "update-initramfs",
                "update-grub",
                "grub-install",
                "reboot",
                "modprobe",
            )
        )


def test_debian_package_filenames_expand_in_bash() -> None:
    source = _script()
    assert 'IMAGE="$OUT/linux-image-${KR}_${VERSION}_amd64.deb"' in source
    assert 'HEADERS="$OUT/linux-headers-${KR}_${VERSION}_amd64.deb"' in source
    assert "\\${KR}" not in source
    assert "\\${VERSION}" not in source
