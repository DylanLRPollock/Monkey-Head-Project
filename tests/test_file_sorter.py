# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test File Sorter module (tests)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
import time

from hueyos.utils.sorting import list_files_by_mtime, natural_sort


def test_list_files_by_mtime(tmp_path):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a")
    time.sleep(0.01)
    f2.write_text("b")
    expected = [str(f1), str(f2)]
    assert list_files_by_mtime(str(tmp_path)) == expected
    assert list_files_by_mtime(str(tmp_path), reverse=True) == expected[::-1]


def test_natural_sort():
    items = ["file10", "file2", "file1"]
    assert natural_sort(items) == ["file1", "file2", "file10"]
