"""Regression tests for the repository's pytest hooks."""

from types import SimpleNamespace

import pytest

from conftest import pytest_pyfunc_call


@pytest.mark.parametrize("marker", [None, object()])
def test_sync_pytest_functions_are_delegated_to_default_runner(marker):
    item = SimpleNamespace(get_closest_marker=lambda _name: marker, obj=lambda: None)

    assert pytest_pyfunc_call(item) is None
