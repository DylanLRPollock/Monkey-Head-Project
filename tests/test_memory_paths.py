# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Memory Paths module (tests)


from hueyos.utils.paths import (
    ensure_subdirectory,
    get_memory_path,
    memory_candidates,
)


def test_memory_path_env_override(monkeypatch, tmp_path):
    target = tmp_path / "custom-memory"
    monkeypatch.setenv("MEMORY_PATH", str(target))
    path = get_memory_path()
    assert path == target
    assert path.exists()


def test_ensure_subdirectory_creates(monkeypatch, tmp_path):
    base = tmp_path / "memory"
    monkeypatch.setenv("MEMORY_PATH", str(base))
    child = ensure_subdirectory("LOGS")
    assert child == base / "LOGS"
    assert child.exists()


def test_memory_candidates_includes_env(monkeypatch, tmp_path):
    custom = tmp_path / "alt"
    monkeypatch.setenv("MEMORY_PATH", str(custom))
    candidates = memory_candidates()
    assert candidates[0] == custom.resolve()
    assert any("huey" in str(path) for path in candidates)
