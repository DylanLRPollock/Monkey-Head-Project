# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Storage Management module (tests)

import os
import time

from huey.os.storage_management import StorageManager


def test_sort_and_list(tmp_path):
    base = tmp_path / "mem"
    base.mkdir()
    (base / "foo.txt").write_text("data")
    (base / "img.PNG").write_text("data")

    mgr = StorageManager(base)
    mgr.sort_root_files()

    assert (base / "TXT" / "foo.txt").is_file()
    assert (base / "PNG" / "img.PNG").is_file()

    files = mgr.list_files("TXT")
    assert str(base / "TXT" / "foo.txt") in files


def test_cleanup_empty_dirs(tmp_path):
    base = tmp_path / "mem"
    empty = base / "EMPTY"
    empty.mkdir(parents=True)

    mgr = StorageManager(base)
    mgr.cleanup_empty_dirs()

    assert not empty.exists()


def test_get_total_size_and_remove_old(tmp_path):
    base = tmp_path / "mem"
    base.mkdir()
    file1 = base / "a.txt"
    file2 = base / "b.txt"
    file1.write_text("a" * 10)
    file2.write_text("b" * 5)

    mgr = StorageManager(base)

    size = mgr.get_total_size()
    assert size == 15

    old_time = time.time() - 10 * 86400
    os.utime(file1, (old_time, old_time))

    removed = mgr.remove_older_than(7)
    assert removed == 1
    assert not file1.exists()
    assert file2.exists()
