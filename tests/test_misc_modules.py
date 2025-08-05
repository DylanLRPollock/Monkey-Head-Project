from unittest.mock import patch
from pathlib import Path
import pytest

pytest.importorskip("numpy")
pytest.importorskip("pandas")
pytest.importorskip("sklearn")
pytest.importorskip("seaborn")
pytest.importorskip("matplotlib")
pytest.importorskip("networkx")
pytest.importorskip("PIL.Image")

from monkey_head.ai_processor import AIProcessor
from monkey_head.chapter_splitter import split_chapters
from monkey_head.huey_core import process_core_data
from monkey_head.huey_checks import check_core_data
from monkey_head.huey_disk_manager_temp import manage_temp_files
from monkey_head.huey_linux import check_linux_service
from monkey_head.huey_remover import remove_files
from monkey_head.huey_tkinter import create_tkinter_window
from monkey_head.file_manager import FileManager
from monkey_head.error_handler import ErrorHandler


def test_ai_processor():
    proc = AIProcessor()
    assert proc.process_data("abc") == "ABC"
    assert proc.analyze_data("123")["length"] == 3

    assert proc.compute_mean([1, 2, 3]) == 2.0

    summary = proc.dataframe_summary(
        [
            {"a": 1, "b": 2},
            {"a": 3, "b": 4},
        ]
    )
    assert summary.loc["mean", "a"] == 2.0

    coef, intercept = proc.train_linear_model([[0], [1]], [0, 1])
    assert round(coef, 5) == 1.0 and round(intercept, 5) == 0.0

    plot = proc.plot_histogram([1, 2, 3], str(tmp_path / "plot.png"))
    assert Path(plot).is_file()

    class DummyResp:
        def __init__(self):
            self.status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"title": "foo"}

    with patch("requests.get", return_value=DummyResp()):
        assert proc.fetch_todo_title(1) == "foo"

    # NetworkX shortest path
    path = proc.shortest_path([("a", "b"), ("b", "c")], "a", "c")
    assert path == ["a", "b", "c"]

    # PIL image size
    from PIL import Image

    img = Image.new("RGB", (10, 20))
    img_file = tmp_path / "img.png"
    img.save(img_file)
    assert proc.image_size(str(img_file)) == (10, 20)


def test_process_and_check_core_data():
    data = {"x": 1, "y": 2}
    processed = process_core_data(data)
    assert check_core_data(processed)
    assert processed["input_length"] == 2


def test_manage_temp_files_delete(tmp_path):
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()
    (temp_dir / "a.txt").write_text("data")
    manage_temp_files(str(temp_dir), "delete")
    assert temp_dir.exists() and not any(temp_dir.iterdir())


def test_manage_temp_files_archive(tmp_path):
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()
    (temp_dir / "a.txt").write_text("data")
    manage_temp_files(str(temp_dir), "archive")
    archive = tmp_path / "tmp_archive"
    assert archive.is_dir()
    assert temp_dir.is_dir()


def test_check_linux_service_active():
    class R:
        stdout = b"active\n"

    with patch("subprocess.run", return_value=R()):
        assert check_linux_service("svc") == "active"


def test_remove_files(tmp_path):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.log"
    f1.write_text("x")
    f2.write_text("y")
    remove_files(str(tmp_path), ".txt")
    assert not f1.exists() and f2.exists()


def test_split_chapters(tmp_path):
    text = "intro\nCHAPTERfirst\nCHAPTERsecond"
    infile = tmp_path / "book.txt"
    infile.write_text(text)
    outdir = tmp_path / "chapters"
    split_chapters(str(infile), str(outdir))
    files = list(outdir.iterdir())
    assert len(files) == 3


def test_file_manager(tmp_path):
    src = tmp_path / "src.txt"
    dest = tmp_path / "dest.txt"
    fm = FileManager()
    fm.write_file(str(src), "hi")
    assert fm.read_file(str(src)) == "hi"
    fm.move_file(str(src), str(dest))
    assert dest.read_text() == "hi"


def test_error_handler(tmp_path):
    log = tmp_path / "log.txt"
    handler = ErrorHandler(str(log))
    handler.log_info("info")
    handler.log_error("error")
    handler.handle_exception(Exception("boom"))


def test_create_tkinter_window():

    class DummyRoot:
        def title(self, t):
            self.t = t

        def mainloop(self):
            self.ran = True

    class DummyButton:
        def __init__(self, root, text, command):
            self.command = command

        def pack(self, pady=0):

            self.command()

    with patch("tkinter.Tk", return_value=DummyRoot()), patch(
        "tkinter.Button", DummyButton
    ), patch("tkinter.messagebox.showinfo") as mbox:
        create_tkinter_window()
        mbox.assert_called_once()
