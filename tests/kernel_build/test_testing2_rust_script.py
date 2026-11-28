"""Static, no-host-mutation safeguards for Rust-enabled testing2 preparation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "kernel" / "huey-734-testing2-config.sh"


def _read() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_testing2_writes_to_separate_directory() -> None:
    source = _read()
    assert 'OUT="$ROOT/output/testing2"' in source
    assert 'REPORT="$ROOT/reports/testing2"' in source
    assert 'TEST1="$ROOT/output/testing1/.config"' in source
    assert 'cp -- "$TEST1" "$OUT/.config"' in source
    assert '[[ ! -e "$OUT" ]]' in source


def test_testing1_baseline_digest_is_protected() -> None:
    source = _read()
    assert "1c72bf3f45c2dac5318d80ec373fcb04b8e2a423b005f8a12a6da18e2c614762" in source
    assert "b11b6df8295e8e991ff040b71aaa4994a8b55caa23b6b092907f195b5840fd1f" in source


def test_rust_reenabled_and_release_guarded() -> None:
    source = _read()
    assert "LOCALVERSION=-huey-testing2 olddefconfig" in source
    assert "--enable RUST" in source
    assert "CONFIG_RUST=y" in source
    assert "7.3.4-huey-testing2" in source
    assert "--stage testing1" in source  # Same strict Optane/V100 hardware policy.
    assert "CONFIG_MODVERSIONS is not set" in source


def test_script_never_installs_or_reboots() -> None:
    # Check operative lines, not harmless safety comments/messages.
    code_lines = [
        line.strip()
        for line in _read().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for forbidden in (
        "sudo ",
        "dpkg -i",
        "apt install",
        "reboot",
        "update-grub",
        "grub-install",
        "update-initramfs",
    ):
        assert all(not line.startswith(forbidden) for line in code_lines)
