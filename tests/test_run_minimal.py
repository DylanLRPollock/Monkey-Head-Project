import os
from run import minimal_run
from monkey_head.pygpt_custom_cli import CustomPyGPT


def test_minimal_run(monkeypatch):
    called = {}
    def fake_run(self):
        called['x'] = True
    monkeypatch.setattr(CustomPyGPT, 'run_cli', fake_run)
    minimal_run()
    assert called.get('x') is True
    assert os.environ.get('MONKEY_HEAD_LIGHT_IMPORTS') == '1'
