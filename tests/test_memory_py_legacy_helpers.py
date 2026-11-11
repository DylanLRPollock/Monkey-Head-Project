"""Regression coverage for dynamically loaded legacy Huey utilities.

These modules remain in use through historical filenames and compatibility
entry points, so the tests import the modules directly instead of relying on
static imports from the main package.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from huey.memory.PY import formatter_temp, utils


class _Image:
    def __init__(self):
        self.saved = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def save(self, path, **kwargs):
        self.saved.append((Path(path), kwargs))
        Path(path).write_bytes(b"image")


def _image_module(monkeypatch):
    image = _Image()
    monkeypatch.setattr(
        utils,
        "_load_image_module",
        lambda: SimpleNamespace(open=lambda _path: image),
    )
    return image


def test_legacy_utils_validation_logging_and_basic_sum(monkeypatch):
    basic_config = Mock()
    info = Mock()
    monkeypatch.setattr(utils.logging, "basicConfig", basic_config)
    monkeypatch.setattr(utils.logging, "info", info)

    assert utils.calculate_sum(4, 5) == 9
    assert utils.validate_input("x", str)
    with pytest.raises(utils.InvalidInputError):
        utils.validate_input(3, str)

    utils.setup_logging({"logging": {"level": "warning", "file": "test.log"}})
    basic_config.assert_called_once()
    assert basic_config.call_args.kwargs["level"] == utils.logging.WARNING
    assert basic_config.call_args.kwargs["filename"] == "test.log"
    info.assert_called_once_with("Logging is set up.")


def test_legacy_utils_image_conversions_validate_and_save(tmp_path, monkeypatch):
    image = _image_module(monkeypatch)
    source = tmp_path / "photo.jpeg"
    source.write_bytes(b"source")

    assert utils.convert_jpeg_to_png(str(source)) == str(tmp_path / "photo.png")
    assert image.saved[-1] == (tmp_path / "photo.png", {"format": "PNG"})

    custom_png = tmp_path / "custom.png"
    utils.convert_jpeg_to_png(str(source), str(custom_png))
    assert image.saved[-1][0] == custom_png

    assert utils.convert_image(str(source), "jpeg", quality=73) == str(
        tmp_path / "photo.jpg"
    )
    assert image.saved[-1] == (
        tmp_path / "photo.jpg",
        {"format": "JPEG", "quality": 73},
    )
    utils.convert_image(str(source), "webp", str(tmp_path / "custom.webp"), 62)
    assert image.saved[-1][1] == {"format": "WEBP", "quality": 62}
    utils.convert_image(str(source), "png")
    assert image.saved[-1][1] == {"format": "PNG", "optimize": True}

    with pytest.raises(FileNotFoundError):
        utils.convert_jpeg_to_png(str(tmp_path / "missing.jpg"))
    with pytest.raises(FileNotFoundError):
        utils.convert_image(str(tmp_path / "missing.jpg"), "PNG")
    with pytest.raises(ValueError, match="Unsupported format"):
        utils.convert_image(str(source), "SVG")


def test_legacy_utils_directory_conversion_skips_invalid_files(tmp_path, monkeypatch):
    source_dir = tmp_path / "images"
    source_dir.mkdir()
    (source_dir / "first.jpg").write_bytes(b"image")
    (source_dir / "bad.jpg").write_bytes(b"image")
    (source_dir / "note.txt").write_text("not an image")
    (source_dir / "subdir").mkdir()
    output_dir = tmp_path / "converted"

    def convert(source, _format, output, quality):
        if _format == "png":
            raise FileNotFoundError("source removed during conversion")
        assert quality == 80
        if Path(source).name == "bad.jpg":
            raise ValueError("invalid image")
        Path(output).write_bytes(b"converted")
        return output

    monkeypatch.setattr(utils, "convert_image", convert)
    result = utils.convert_images_in_directory(
        str(source_dir), "JPEG", str(output_dir), quality=80
    )
    assert set(result) == {
        str(output_dir / "first.jpg"),
        str(output_dir / "note.jpg"),
    }
    assert (output_dir / "first.jpg").read_bytes() == b"converted"

    assert utils.convert_images_in_directory(str(source_dir), "png") == []
    with pytest.raises(NotADirectoryError):
        utils.convert_images_in_directory(str(tmp_path / "absent"), "PNG")


def test_formatter_temp_reads_config_and_applies_defaults(tmp_path, monkeypatch):
    formatter = formatter_temp.Formatter.__new__(formatter_temp.Formatter)
    missing = tmp_path / "missing.json"
    formatter.load_config(missing)
    assert (
        formatter.books_folder,
        formatter.memory_folder,
        formatter.splitter_folder,
    ) == (
        "BOOKS",
        "MEMORY",
        "SPLITTER",
    )

    config = tmp_path / "formatter.json"
    config.write_text(
        json.dumps(
            {
                "books_folder": "BOOKS_IN",
                "memory_folder": "MEMORY_IN",
                "splitter_folder": "SPLITTER_IN",
            }
        )
    )
    formatter.load_config(config)
    assert formatter.books_folder == "BOOKS_IN"
    assert formatter.memory_folder == "MEMORY_IN"
    assert formatter.splitter_folder == "SPLITTER_IN"

    logger = SimpleNamespace(handlers=[])
    monkeypatch.setattr(formatter_temp, "configure_logging", lambda: logger)
    formatter.setup_logging()
    formatter.initial_variable()
    assert formatter.program_name.endswith("formatter_temp.py")
    assert formatter.books_folder.endswith("BOOKS_IN")
    assert formatter.memory_folder.endswith("MEMORY_IN")
    assert formatter.splitter_folder.endswith("SPLITTER_IN")


def test_formatter_temp_messages_validation_and_folder_creation(
    tmp_path, monkeypatch, capsys
):
    formatter = formatter_temp.Formatter.__new__(formatter_temp.Formatter)
    formatter.parent_folder = str(tmp_path)
    formatter.print_message("hello", "info")
    formatter.print_message("careful", "alert")
    output = capsys.readouterr().out
    assert "Info: hello" in output
    assert "Alert has been triggered" in output

    monkeypatch.setattr("builtins.input", lambda prompt: prompt)
    assert formatter.print_message("question", "user_input").endswith("question")
    formatter.ensure_folder_exists("created")
    formatter.ensure_folder_exists("created")
    assert (tmp_path / "created").is_dir()

    formatter.initial_message()
    assert "Formatter Temp Initialized" in capsys.readouterr().out
    formatter.main()
    assert "end" in capsys.readouterr().out

    def stop():
        raise SystemExit(1)

    formatter.graceful_exit = stop
    for output, kind, message in (
        (None, "status", "Invalid input types"),
        ("", "status", "Empty strings"),
        ("hello", "unknown", "Invalid message_type"),
    ):
        with pytest.raises(SystemExit):
            formatter.validate_print_message_input(output, kind)
        assert message in capsys.readouterr().out
