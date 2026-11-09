# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Load Cli module (tests)

import pytest

from huey.memory.PY import run


def test_load_cli_fails_instead_of_falling_back():
    with pytest.raises(RuntimeError, match="echo-only demo"):
        run._load_cli()
