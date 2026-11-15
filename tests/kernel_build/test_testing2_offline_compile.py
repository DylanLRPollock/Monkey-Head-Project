"""Ensure the first testing2 compilation never mutates the live Debian host."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/kernel/huey-734-testing2-compile.sh"


def _script() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_pinned_source_and_candidate_hashes() -> None:
    s = _script()
    assert "b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f" in s
    assert "1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762" in s
    assert "db6a1f168766546b2e5e612657d928c737cf5561f2319bf069fdad2a1312a6d3" in s


def test_no_overwrite_of_reviewed_configs() -> None:
    s = _script()
    assert 'OBJ="$ROOT/output/testing2-compile"' in s
    assert 'CAND="$ROOT/output/testing2/.config"' in s
    assert '[[ ! -e "$OBJ" ]]' in s
    assert 'cp -- "$CAND" "$OBJ/.config"' in s
    assert 'check_hash "$OBJ/.config" "$TEST2_SHA"' in s


def test_only_offline_image_and_modules_build() -> None:
    s = _script()
    assert 'LOCALVERSION=-huey-testing2 bzImage modules' in s
    assert 'JOBS=4' in s
    assert 'modinfo -F vermagic' in s
    assert '"$OBJ/Module.symvers"' in s
    for line in s.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        assert not any(
            line.startswith(command)
            for command in (
                "sudo ", "apt ", "dpkg -i", "grub-install", "update-grub",
                "update-initramfs", "reboot", "poweroff", "make modules_install",
            )
        )


def test_signing_material_never_collected() -> None:
    s = _script()
    assert "private signing key" in s
    assert "signing_key.pem" not in s
    assert "sha256sum \"$OBJ/.config\"" in s
