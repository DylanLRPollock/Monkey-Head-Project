from monkey_head.storage_management import StorageManager


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
