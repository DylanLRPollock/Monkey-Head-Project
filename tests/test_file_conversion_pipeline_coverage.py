"""Exercise safe PDF extraction and legacy conversion dispatch branches."""

from __future__ import annotations

import builtins
import sys
from types import SimpleNamespace

import pytest

from huey.memory.PY import convert_files as conversion


class FakePage:
    def __init__(self, text="page"):
        self.text = text

    def extract_text(self):
        if isinstance(self.text, Exception):
            raise self.text
        return self.text


class FakeReader:
    def __init__(self, _handle, *, encrypted=False, pages=None, decrypt_result=True):
        self.is_encrypted = encrypted
        self.pages = pages or [FakePage("extracted")]
        self.decrypt_result = decrypt_result

    def decrypt(self, password):
        assert password == ""
        return self.decrypt_result


def install_reader(monkeypatch, reader=FakeReader):
    monkeypatch.setitem(sys.modules, "pypdf", SimpleNamespace(PdfReader=reader))


def test_pdf_reader_dependency_errors_are_actionable(monkeypatch):
    original = builtins.__import__

    def no_pypdf(name, *args, **kwargs):
        if name == "pypdf":
            raise ModuleNotFoundError("missing", name="pypdf")
        return original(name, *args, **kwargs)

    monkeypatch.delitem(sys.modules, "pypdf", raising=False)
    monkeypatch.setattr(builtins, "__import__", no_pypdf)
    with pytest.raises(conversion.DependencyError, match="Install it"):
        conversion._load_pdf_reader()

    def missing_dependency(name, *args, **kwargs):
        if name == "pypdf":
            raise ModuleNotFoundError("missing transitive", name="cryptography")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing_dependency)
    with pytest.raises(conversion.DependencyError, match="cryptography"):
        conversion._load_pdf_reader()

    def import_error(name, *args, **kwargs):
        if name == "pypdf":
            raise ImportError("broken pypdf")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_error)
    with pytest.raises(conversion.DependencyError, match="broken pypdf"):
        conversion._load_pdf_reader()


def test_convert_pdf_extracts_pages_and_handles_empty_content(tmp_path, monkeypatch):
    install_reader(
        monkeypatch,
        lambda handle: FakeReader(handle, pages=[FakePage("one"), FakePage("two")]),
    )
    source = tmp_path / "source.PDF"
    source.write_bytes(b"pdf")

    assert conversion.convert_pdf_to_text(source) == "one\n\ntwo"
    install_reader(
        monkeypatch,
        lambda handle: FakeReader(handle, pages=[FakePage(" "), FakePage(None)]),
    )
    with pytest.raises(conversion.ConversionError, match="No extractable text"):
        conversion.convert_pdf_to_text(source)
    assert conversion.convert_pdf_to_text(source, allow_empty=True) == " \n\n"


def test_convert_pdf_rejects_missing_encrypted_and_broken_pages(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    install_reader(monkeypatch)
    with pytest.raises(conversion.ConversionError, match="not a regular file"):
        conversion.convert_pdf_to_text(tmp_path / "missing.pdf")

    install_reader(
        monkeypatch,
        lambda handle: FakeReader(handle, encrypted=True, decrypt_result=False),
    )
    with pytest.raises(conversion.ConversionError, match="requires a password"):
        conversion.convert_pdf_to_text(source)

    install_reader(
        monkeypatch,
        lambda handle: FakeReader(handle, pages=[FakePage(RuntimeError("bad page"))]),
    )
    with pytest.raises(conversion.ConversionError, match="page 1"):
        conversion.convert_pdf_to_text(source)

    class BrokenReader:
        def __init__(self, _handle):
            raise OSError("broken file")

    install_reader(monkeypatch, BrokenReader)
    with pytest.raises(conversion.ConversionError, match="Could not read PDF"):
        conversion.convert_pdf_to_text(source)


def test_atomic_save_creates_new_and_overwrites_existing_file(tmp_path):
    target = tmp_path / "nested" / "output.txt"
    conversion.save_text_to_file("one", target)
    assert target.read_text() == "one"
    conversion.save_text_to_file("two", target, overwrite=True)
    assert target.read_text() == "two"
    assert list(target.parent.iterdir()) == [target]


def test_atomic_save_rejects_symlinks_directories_and_existing_targets(tmp_path):
    target = tmp_path / "output.txt"
    target.write_text("existing")
    with pytest.raises(conversion.ConversionError, match="already exists"):
        conversion.save_text_to_file("new", target)

    directory = tmp_path / "directory"
    directory.mkdir()
    with pytest.raises(conversion.ConversionError, match="not a regular file"):
        conversion.save_text_to_file("new", directory)

    linked = tmp_path / "link.txt"
    linked.symlink_to(target)
    with pytest.raises(conversion.ConversionError, match="output symlink"):
        conversion.save_text_to_file("new", linked)


def test_atomic_save_maps_link_races_and_unsupported_filesystems(tmp_path, monkeypatch):
    target = tmp_path / "output.txt"
    monkeypatch.setattr(
        conversion.os, "link", lambda *_args: (_ for _ in ()).throw(FileExistsError())
    )
    with pytest.raises(conversion.ConversionError, match="created concurrently"):
        conversion.save_text_to_file("new", target)
    assert not list(tmp_path.glob("*.tmp"))

    def unsupported(*_args):
        raise OSError("unsupported")

    monkeypatch.setattr(conversion.os, "link", unsupported)
    with pytest.raises(conversion.ConversionError, match="hard-link support"):
        conversion.save_text_to_file("new", target)
    assert not list(tmp_path.glob("*.tmp"))

    monkeypatch.setattr(conversion.os, "link", lambda *_args: None)
    monkeypatch.setattr(
        conversion.os,
        "fsync",
        lambda _fd: (_ for _ in ()).throw(OSError("write fsync")),
    )
    with pytest.raises(conversion.ConversionError, match="Could not save"):
        conversion.save_text_to_file("new", target)


def test_atomic_save_logs_when_temporary_cleanup_fails(tmp_path, monkeypatch, caplog):
    original = conversion.Path.unlink

    def fail_temp_cleanup(path, *args, **kwargs):
        if path.suffix == ".tmp":
            raise OSError("cleanup denied")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(conversion.Path, "unlink", fail_temp_cleanup)
    conversion.save_text_to_file("written", tmp_path / "clean.txt")
    assert "Could not remove temporary file" in caplog.text


def test_fsync_directory_ignores_open_and_fsync_errors(monkeypatch, tmp_path):
    def fail_open(*_args):
        raise OSError("cannot open directory")

    monkeypatch.setattr(conversion.os, "open", fail_open)
    conversion._fsync_directory(tmp_path)

    monkeypatch.setattr(conversion.os, "open", lambda *_args: 11)
    closed = []
    monkeypatch.setattr(
        conversion.os, "fsync", lambda _fd: (_ for _ in ()).throw(OSError("fsync"))
    )
    monkeypatch.setattr(conversion.os, "close", closed.append)
    conversion._fsync_directory(tmp_path)
    assert closed == [11]


def test_process_pdf_validates_source_and_publishes_text(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    monkeypatch.setattr(conversion, "convert_pdf_to_text", lambda *_a, **_k: "body")
    target = conversion.process_pdf(source, tmp_path / "out")
    assert target.read_text() == "body"

    text_source = tmp_path / "source.txt"
    text_source.write_text("not pdf")
    with pytest.raises(conversion.ConversionError, match=r"\.pdf extension"):
        conversion.process_pdf(text_source, tmp_path / "out")

    with pytest.raises(FileNotFoundError):
        conversion.process_pdf(tmp_path / "missing.pdf", tmp_path / "out")


def test_process_pdf_refuses_symlink_output_that_aliases_source(tmp_path, monkeypatch):
    source = tmp_path / "source.pdf"
    source.write_bytes(b"pdf")
    output = tmp_path / "out"
    output.mkdir()
    (output / "source.txt").symlink_to(source)
    monkeypatch.setattr(conversion, "convert_pdf_to_text", lambda *_a, **_k: "body")
    with pytest.raises(conversion.ConversionError, match="replace the source"):
        conversion.process_pdf(source, output)

    hard_link_output = tmp_path / "hardlink-out"
    hard_link_output.mkdir()
    (hard_link_output / "source.txt").hardlink_to(source)
    with pytest.raises(conversion.ConversionError, match="refers to the source"):
        conversion.process_pdf(source, hard_link_output)


def test_batch_pdf_processing_collects_success_and_failure(tmp_path, monkeypatch):
    source = tmp_path / "input"
    source.mkdir()
    first = source / "a.pdf"
    second = source / "b.PDF"
    first.touch()
    second.touch()
    (source / "ignore.txt").touch()
    monkeypatch.setattr(conversion, "_load_pdf_reader", lambda: FakeReader)

    def process(path, output, **_kwargs):
        if path.name == "b.PDF":
            raise conversion.ConversionError("bad document")
        return output / "a.txt"

    monkeypatch.setattr(conversion, "process_pdf", process)
    result = conversion.process_pdfs_in_directory(source, tmp_path / "out", workers=2)
    assert result.written == [tmp_path / "out" / "a.txt"]
    assert result.failed == {second: "bad document"}
    assert result.ok is False


def test_batch_pdf_processing_rejects_invalid_inputs_and_collisions(
    tmp_path, monkeypatch
):
    for workers in (True, 0, -1, 1.5):
        with pytest.raises(ValueError, match="positive integer"):
            conversion.process_pdfs_in_directory(
                tmp_path, tmp_path / "out", workers=workers
            )

    monkeypatch.setattr(conversion, "_load_pdf_reader", lambda: FakeReader)
    with pytest.raises(NotADirectoryError):
        conversion.process_pdfs_in_directory(__file__, tmp_path / "out")
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(conversion.ConversionError, match="No PDF files"):
        conversion.process_pdfs_in_directory(empty, tmp_path / "out")

    collision = tmp_path / "collision"
    collision.mkdir()
    (collision / "A.pdf").touch()
    (collision / "a.PDF").touch()
    with pytest.raises(conversion.ConversionError, match="Conflicting output names"):
        conversion.process_pdfs_in_directory(collision, tmp_path / "out")


def test_normalize_exit_codes_and_legacy_dispatch_restore_process_state(monkeypatch):
    assert conversion._normalize_exit_code(None) == 0
    assert conversion._normalize_exit_code(5) == 5
    assert conversion._normalize_exit_code("bad") == 1

    original_argv = ["tool", "original"]
    original_path = list(sys.path)
    monkeypatch.setattr(conversion.sys, "argv", original_argv)
    module = SimpleNamespace(__name__="legacy", main=lambda: 4)
    monkeypatch.setattr(conversion.importlib, "import_module", lambda _name: module)
    assert conversion._run_legacy("mkv2mp4", ["input.mkv"]) == 4
    assert sys.argv is original_argv
    assert sys.path == original_path


def test_legacy_dispatch_normalizes_exit_and_rejects_missing_main(monkeypatch):
    original_argv = sys.argv
    monkeypatch.setattr(conversion.sys, "argv", ["tool"])
    monkeypatch.setattr(
        conversion.importlib,
        "import_module",
        lambda _name: SimpleNamespace(
            __name__="legacy", main=lambda: (_ for _ in ()).throw(SystemExit(None))
        ),
    )
    assert conversion._run_legacy("avi2mkv", []) == 0

    monkeypatch.setattr(
        conversion.importlib,
        "import_module",
        lambda _name: SimpleNamespace(__name__="legacy"),
    )
    with pytest.raises(conversion.ConversionError, match="no callable main"):
        conversion._run_legacy("avi2mkv", [])
    assert sys.argv == ["tool"]
    assert original_argv is not None


def test_positive_integer_and_parser_options():
    assert conversion._positive_integer("3") == 3
    for value in ("x", "0", "-2"):
        with pytest.raises(conversion.argparse.ArgumentTypeError):
            conversion._positive_integer(value)
    parser = conversion.build_parser()
    assert parser.parse_args(["pdf2txt"]).command == "pdf2txt"
    pdf = conversion.build_pdf_parser().parse_args(
        ["--workers", "2", "--quiet", "--allow-empty"]
    )
    assert pdf.workers == 2 and pdf.quiet and pdf.allow_empty


def test_main_dispatches_legacy_and_pdf_commands(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(conversion, "_run_legacy", lambda command, args: 6)
    assert conversion.main(["mkv2mp4", "in.mkv"]) == 6

    result = conversion.BatchResult(written=[tmp_path / "out.txt"])
    monkeypatch.setattr(
        conversion, "process_pdfs_in_directory", lambda *_a, **_k: result
    )
    assert conversion.main(["pdf2txt", "-i", str(tmp_path), "-v"]) == 0
    assert "Converted 1 PDF(s); failed 0" in capsys.readouterr().out

    result.failed[tmp_path / "bad.pdf"] = "failure"
    assert conversion.main(["pdf2txt", "-q"]) == 1
    assert capsys.readouterr().out == ""


def test_main_normalizes_cli_and_runtime_failures(monkeypatch):
    assert conversion.main(["--help"]) == 0

    monkeypatch.setattr(
        conversion,
        "process_pdfs_in_directory",
        lambda *_a, **_k: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    assert conversion.main(["pdf2txt"]) == 130

    monkeypatch.setattr(
        conversion,
        "process_pdfs_in_directory",
        lambda *_a, **_k: (_ for _ in ()).throw(conversion.ConversionError("bad")),
    )
    assert conversion.main(["pdf2txt"]) == 1

    monkeypatch.setattr(
        conversion,
        "process_pdfs_in_directory",
        lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("unexpected")),
    )
    assert conversion.main(["pdf2txt"]) == 1


def test_legacy_dispatch_skips_path_insert_when_root_is_already_present(monkeypatch):
    original_path = list(sys.path)
    monkeypatch.setattr(conversion.sys, "argv", ["tool"])
    monkeypatch.setattr(conversion.sys, "path", [str(conversion._ROOT)])
    monkeypatch.setattr(
        conversion.importlib,
        "import_module",
        lambda _name: SimpleNamespace(__name__="legacy", main=lambda: 0),
    )
    assert conversion._run_legacy("avi2mkv", []) == 0
    assert sys.path == [str(conversion._ROOT)]
    monkeypatch.setattr(conversion.sys, "path", original_path)
