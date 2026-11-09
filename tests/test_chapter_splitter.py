"""Focused standard-library tests for chapter splitting and file safety."""

from __future__ import annotations

from pathlib import Path

import pytest

from huey.memory.PY import chapter_splitter as splitter


def _source(tmp_path: Path, text: str, name: str = "book.txt") -> Path:
    source = tmp_path / name
    source.write_text(text, encoding="utf-8")
    return source


def test_split_writes_preamble_chapters_named_files_and_toc(tmp_path):
    source = _source(
        tmp_path,
        "Preface\n\nCHAPTER 1: Start\nAlpha\n"
        "Chapter II — Middle\nBeta\nEPILOGUE\nDone\n",
    )
    output = tmp_path / "chapters"

    paths = splitter.split_chapters(
        source,
        output,
        name_files=True,
        generate_toc=True,
    )

    assert [path.name for path in paths] == [
        "preamble.txt",
        "chapter_001_chapter-1-start.txt",
        "chapter_002_chapter-ii-middle.txt",
        "chapter_003_epilogue.txt",
        "toc.md",
    ]
    assert (output / "preamble.txt").read_text() == "Preface\n"
    assert (output / "chapter_001_chapter-1-start.txt").read_text() == (
        "CHAPTER 1: Start\nAlpha\n"
    )
    assert (output / "chapter_002_chapter-ii-middle.txt").read_text() == (
        "Chapter II — Middle\nBeta\n"
    )
    toc = (output / "toc.md").read_text()
    assert "# Table of Contents" in toc
    assert "[Preamble](preamble.txt)" in toc
    assert "[EPILOGUE](chapter_003_epilogue.txt)" in toc


@pytest.mark.parametrize(
    ("preamble", "expected_names", "first_content"),
    [
        ("separate", ["preamble.txt", "chapter_001.txt"], "CHAPTER 1\nbody\n"),
        ("prepend", ["chapter_001.txt"], "Intro\nCHAPTER 1\nbody\n"),
        ("discard", ["chapter_001.txt"], "CHAPTER 1\nbody\n"),
    ],
)
def test_split_preamble_modes(tmp_path, preamble, expected_names, first_content):
    source = _source(tmp_path, "Intro\nCHAPTER 1\nbody")
    output = tmp_path / preamble

    paths = splitter.split_chapters(source, output, preamble=preamble)

    assert [path.name for path in paths] == expected_names
    assert (output / expected_names[-1]).read_text() == first_content
    if preamble == "separate":
        assert (output / "preamble.txt").read_text() == "Intro\n"


def test_markdown_preset_and_unicode_slug(tmp_path):
    source = _source(tmp_path, "Opening\n## Chapter 1: Café & Tea\nText\n")
    output = tmp_path / "markdown"

    paths = splitter.split_chapters(
        source,
        output,
        pattern=splitter.PRESETS["markdown"],
        name_files=True,
    )

    assert paths[1].name == "chapter_001_chapter-1-cafe-tea.txt"
    assert paths[1].read_text() == "## Chapter 1: Café & Tea\nText\n"


def test_case_sensitive_matching_and_dry_run_do_not_create_output(tmp_path):
    source = _source(tmp_path, "chapter 1\nsmall\nCHAPTER 2\nlarge\n")
    output = tmp_path / "not-created"

    paths = splitter.split_chapters(
        source,
        output,
        ignore_case=False,
        dry_run=True,
    )

    assert [path.name for path in paths] == ["chapter_001.txt"]
    assert not output.exists()


@pytest.mark.parametrize("text", ["", "   \n\t\n"])
def test_empty_or_whitespace_input_is_rejected(tmp_path, text):
    source = _source(tmp_path, text)

    with pytest.raises(splitter.ChapterSplitError, match="empty"):
        splitter.split_chapters(source, tmp_path / "out")


def test_no_heading_match_is_rejected(tmp_path):
    source = _source(tmp_path, "A document with no chapter headings.")

    with pytest.raises(splitter.ChapterSplitError, match="No chapter headings"):
        splitter.split_chapters(source, tmp_path / "out")


def test_invalid_preamble_encoding_and_pattern_are_rejected(tmp_path):
    source = _source(tmp_path, "CHAPTER 1\nText\n")

    with pytest.raises(ValueError, match="preamble"):
        splitter.split_chapters(source, tmp_path / "out", preamble="unknown")

    with pytest.raises(ValueError, match="Unknown encoding"):
        splitter.split_chapters(source, tmp_path / "out", input_encoding="not-a-codec")

    with pytest.raises(ValueError, match="Invalid chapter pattern"):
        splitter.split_chapters(source, tmp_path / "out", pattern="[")


@pytest.mark.parametrize(
    ("text", "pattern", "message"),
    [
        ("CHAPTER 1\n", "(?=CHAPTER)", "empty match"),
        ("Intro CHAPTER 1\n", "CHAPTER", "line boundaries"),
    ],
)
def test_empty_or_unanchored_matches_are_rejected(tmp_path, text, pattern, message):
    source = _source(tmp_path, text)

    with pytest.raises(ValueError, match=message):
        splitter.split_chapters(source, tmp_path / "out", pattern=pattern)


def test_source_must_be_a_regular_file_and_output_must_be_a_directory(tmp_path):
    with pytest.raises(ValueError, match="Input is not a regular file"):
        splitter.split_chapters(tmp_path, tmp_path / "out")

    source = _source(tmp_path, "CHAPTER 1\n")
    output_file = _source(tmp_path, "not a directory", "output")
    with pytest.raises(NotADirectoryError):
        splitter.split_chapters(source, output_file)


def test_output_encoding_failure_happens_before_directory_creation(tmp_path):
    source = _source(tmp_path, "CHAPTER 1\nSnowman ☃\n")
    output = tmp_path / "latin"

    with pytest.raises(UnicodeEncodeError):
        splitter.split_chapters(source, output, output_encoding="ascii")

    assert not output.exists()


def test_existing_output_requires_overwrite_and_can_be_replaced(tmp_path):
    source = _source(tmp_path, "CHAPTER 1\nnew content\n")
    output = tmp_path / "chapters"
    output.mkdir()
    chapter = output / "chapter_001.txt"
    chapter.write_text("old content\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Use overwrite"):
        splitter.split_chapters(source, output)

    splitter.split_chapters(source, output, overwrite=True)
    assert chapter.read_text() == "CHAPTER 1\nnew content\n"


def test_split_refuses_to_overwrite_input_or_follow_output_symlink(tmp_path):
    source = _source(tmp_path, "CHAPTER 1\n", "chapter_001.txt")
    with pytest.raises(ValueError, match="replace the input"):
        splitter.split_chapters(source, tmp_path)

    source = _source(tmp_path, "CHAPTER 1\n", "book.txt")
    output = tmp_path / "linked"
    output.mkdir()
    target = tmp_path / "target.txt"
    target.write_text("protected\n", encoding="utf-8")
    link = output / "chapter_001.txt"
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError):
        pytest.skip("symlink support unavailable")

    with pytest.raises(ValueError, match="symlink"):
        splitter.split_chapters(source, output, overwrite=True)

    assert target.read_text() == "protected\n"


def test_atomic_writer_removes_temporary_file_when_replace_fails(
    monkeypatch, tmp_path
):
    destination = tmp_path / "chapter.txt"
    destination.write_text("old\n", encoding="utf-8")

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(splitter.os, "replace", fail_replace)
    with pytest.raises(OSError, match="simulated"):
        splitter._write_atomic(
            destination,
            "new\n",
            encoding="utf-8",
            overwrite=True,
        )

    assert destination.read_text() == "old\n"
    assert list(tmp_path.iterdir()) == [destination]


def test_parser_supports_presets_and_mutually_exclusive_pattern_options():
    parser = splitter.build_parser()
    arguments = parser.parse_args(["source.txt", "out", "--preset", "markdown"])

    assert arguments.preset == "markdown"
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["source.txt", "out", "--preset", "markdown", "--pattern", "CUSTOM"]
        )


def test_main_success_quiet_and_dry_run_modes(tmp_path, capsys):
    source = _source(tmp_path, "CHAPTER 1\nText\n")
    output = tmp_path / "chapters"

    assert splitter.main([str(source), str(output), "--quiet"]) == 0
    assert output.joinpath("chapter_001.txt").is_file()
    assert capsys.readouterr().out == ""

    dry_output = tmp_path / "dry-run"
    assert splitter.main([str(source), str(dry_output), "--dry-run"]) == 0
    captured = capsys.readouterr()
    assert "Dry run: 1 file(s) planned." in captured.out
    assert not dry_output.exists()


def test_main_reports_validation_error_and_keyboard_interrupt(monkeypatch, tmp_path):
    source = _source(tmp_path, "CHAPTER 1\n")
    assert splitter.main([str(source), str(tmp_path / "bad"), "--pattern", "["]) == 1

    monkeypatch.setattr(
        splitter,
        "split_chapters",
        lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    assert splitter.main([str(source), str(tmp_path / "interrupted")]) == 130
