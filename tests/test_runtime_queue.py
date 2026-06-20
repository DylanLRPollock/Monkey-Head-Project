from pathlib import Path

from huey.os.runtime.queue import (
    claim_fixture,
    list_pending_fixtures,
    mark_failed,
    mark_processed,
)


def _write_file(path: Path, content: str = "fixture") -> None:
    path.write_text(content, encoding="utf-8")


def test_list_pending_fixtures_ignores_partial_and_tmp_and_sorts(
    tmp_path: Path,
) -> None:
    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()

    _write_file(queue_dir / "b_fixture.mp3")
    _write_file(queue_dir / "a_fixture.mp3")
    _write_file(queue_dir / "z_fixture.partial")
    _write_file(queue_dir / "y_fixture.tmp")

    pending = list_pending_fixtures(queue_dir)

    assert [path.name for path in pending] == ["a_fixture.mp3", "b_fixture.mp3"]


def test_claim_fixture_moves_file_to_runs_directory(tmp_path: Path) -> None:
    queue_dir = tmp_path / "queue"
    runs_dir = tmp_path / "runs"
    queue_dir.mkdir()

    source = queue_dir / "fixture.mp3"
    _write_file(source, "audio")

    claimed = claim_fixture(source, runs_dir)

    assert claimed == runs_dir / "fixture.mp3"
    assert not source.exists()
    assert claimed.read_text(encoding="utf-8") == "audio"


def test_mark_processed_moves_claimed_file(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    processed_dir = tmp_path / "processed"
    runs_dir.mkdir()

    fixture = runs_dir / "fixture.mp3"
    _write_file(fixture, "done")

    archived = mark_processed(fixture, processed_dir)

    assert archived == processed_dir / "fixture.mp3"
    assert not fixture.exists()
    assert archived.read_text(encoding="utf-8") == "done"


def test_mark_failed_preserves_file_and_writes_reason(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    failed_dir = tmp_path / "failed"
    runs_dir.mkdir()

    fixture = runs_dir / "fixture.mp3"
    _write_file(fixture, "bad audio")

    moved_fixture, reason_path = mark_failed(
        fixture, failed_dir, "transcription failed"
    )

    assert moved_fixture == failed_dir / "fixture.mp3"
    assert not fixture.exists()
    assert moved_fixture.read_text(encoding="utf-8") == "bad audio"
    assert reason_path.read_text(encoding="utf-8") == "transcription failed"
