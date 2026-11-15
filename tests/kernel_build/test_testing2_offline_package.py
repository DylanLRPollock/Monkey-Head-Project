"""Static safeguards for the unprivileged testing2 Debian packaging phase."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-package.sh"


def _source() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_sourced_build_and_config_digests_are_pinned() -> None:
    s = _source()
    assert "b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f" in s
    assert "1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762" in s
    assert "db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3" in s
    assert 'sha256sum --status -c "$REPORT/kernel-compile-hashes.txt"' in s


def test_only_offline_binary_packaging_is_run() -> None:
    s = _source()
    assert "bindeb-pkg" in s
    assert 'O="$OBJ"' in s
    assert "KDEB_PKGVERSION=" in s
    assert 'current_kernel="$(uname -r)"' in s
    forbidden = (
        "sudo ", "apt ", "dpkg -i", "make install",
        "make modules_install", "update-initramfs",
        "update-grub", "reboot", "grub-install",
    )
    assert all(
        not line.strip().startswith(forbidden)
        for line in s.splitlines() if not line.strip().startswith("#")
    )


def test_do_not_publish_build_secrets() -> None:
    s = _source()
    assert "signing_key.pem" in s
    assert "dpkg-deb --contents" in s
    assert "Possible private key" in s
    assert "Do not upload .deb files" in s


def test_package_names_are_verified() -> None:
    s = _source()
    assert '"linux-image-$KR"' in s
    assert '"linux-headers-$KR"' in s
    assert "linux-libc-dev" in s
    assert "Do not use sudo." in s
