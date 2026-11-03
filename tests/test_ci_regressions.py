"""Regression checks for CI failures uncovered after workflow pin repair."""

import sqlite3

import pytest

from huey.os.utils.persistence import TelemetryStore
from huey.storage.hex_cluster import HexClusterIndex
from scripts.repo.check_canon_terms import _compile_rules, _should_flag_pygpt


def test_bucket_hash_remains_compatible():
    assert HexClusterIndex().cluster_for("hello") == "aaf"


def test_telemetry_connection_closes_and_rolls_back(tmp_path):
    store = TelemetryStore(tmp_path / "events.db")
    with store._connection() as connection:
        connection.execute("INSERT INTO events VALUES (NULL, 1, 'committed', '{}')")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")

    with (
        pytest.raises(ValueError, match="rollback"),
        store._connection() as failed_connection,
    ):
        failed_connection.execute(
            "INSERT INTO events VALUES (NULL, 2, 'rolled-back', '{}')"
        )
        raise ValueError("rollback")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        failed_connection.execute("SELECT 1")
    assert [event.event_type for event in store.fetch_recent_events()] == ["committed"]


def test_hims_rule_distinguishes_design_from_runtime_claims():
    rule = next(rule for rule in _compile_rules() if rule.name == "hims-active-runtime")
    assert rule.pattern.search("HIMS is the active runtime.")
    assert not rule.pattern.search("HIMS is the planned internal communication layer.")
    assert not rule.pattern.search("HIMS is not yet a network protocol.")
    assert not rule.pattern.search("Preserve HIMS message contracts.")
    assert not _should_flag_pygpt("Vendored PyGPT mirrors preserve attribution.")
