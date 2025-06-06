import os
import time

from src.utils.list_by_mtime import list_files_by_mtime


def test_list_files_by_mtime(tmp_path):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a")
    time.sleep(0.01)
    f2.write_text("b")
    expected = [str(f1), str(f2)]
    assert list_files_by_mtime(str(tmp_path)) == expected
