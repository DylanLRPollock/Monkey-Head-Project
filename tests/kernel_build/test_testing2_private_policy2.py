"""Static invariants for a second private, rootless testing2 initramfs."""

from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "scripts/kernel/huey-734-testing2-private-policy2.sh"
)


def _source() -> str:
    assert SCRIPT.is_file()
    return SCRIPT.read_text(encoding="utf-8")


def test_pinned_original_and_non_overwrite() -> None:
    source = _source()
    assert "ddcc9e6c238a3c744adca38903c5d4ffcf8c4393ee1517576860a85812cb5bdd" in source
    assert '[[ ! -e "$f" ]]' in source
    assert 'RETRY="$STAGE/work/fakeroot-policy2"' in source
    assert '[[ ! -e "/lib/modules/$KR" && ! -e "/boot/vmlinuz-$KR" ]]' in source
    assert "Run without sudo." in source


def test_expected_arrays_only_with_private_overlay() -> None:
    source = _source()
    assert "f3c8b907:d3b5a85f:a2578548:157bf1d2" in source
    assert "a3068941:490dcc7f:ce9dedcc:6ef270e0" in source
    assert "646adf0e:63c18bd3:053728a3:66c836b5" in source
    assert "38a8dd4b:f15c5eca:fafe213a:2962ac03" in source
    assert 'awk -v md3="$MD3"' in source
    assert '--ro-bind "$PRIVATEMD" /etc/mdadm/mdadm.conf' in source
    assert "'RESUME=none" in source
    assert "grep -Exq 'RESUME=none' \"$RESUME\"" in source
    assert "New image still contains stale md3 ARRAY UUID." in source
    assert "Unexpected embedded ARRAY count." in source


def test_private_namespace_fakeroot_and_integrity() -> None:
    source = _source()
    assert "--ro-bind / /" in source
    assert "--tmpfs /lib/modules" in source
    assert '--ro-bind "$MODTREE" "/lib/modules/$KR"' in source
    assert '--bind "$RETRY" "$RETRY"' in source
    assert "--unshare-net" in source
    assert "FAKEROOTDONTTRYCHOWN 1" in source
    assert "fakeroot -- /usr/sbin/mkinitramfs" in source
    assert "lsinitramfs -l" in source
    assert "unmkinitramfs" in source
    assert '[[ "$(grep -Ec' in source


def test_never_touch_installed_kernel_grub_efi_or_mdadm() -> None:
    src = _source()
    forbidden = (
        "sudo ",
        "apt ",
        "dpkg -i",
        "mkfs",
        "wipefs",
        "mdadm --assemble",
        "mdadm --create",
        "modprobe ",
        "insmod ",
        "rmmod ",
        "update-initramfs ",
        "update-grub ",
        "grub-install ",
        "reboot",
        "mount ",
        "umount ",
        "rm -rf",
    )
    for line in src.splitlines():
        line = line.lstrip()
        if not line or line.startswith("#"):
            continue
        assert not line.startswith(forbidden)
