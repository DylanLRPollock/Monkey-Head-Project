# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Preloader module (tests)

from huey.os.scripts.preload_data import preload_all


def test_preload_all():
    data = preload_all()
    assert data["prompts"], "Prompts should not be empty"
    assert data["memory"], "Available memory inputs should not be empty"
