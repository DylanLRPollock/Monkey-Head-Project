# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Cli Run module (tests)

from monkey_head.cli import CLI


class DummyConfig:
    def __init__(self):
        self.data = {}

    def set_setting(self, key, value):
        self.data[key] = value

    def get_setting(self, key, default=None):
        return self.data.get(key, default)


def test_cli_run(monkeypatch, capsys):
    inputs = iter(["set foo bar", "get foo", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    cli = CLI()
    cli.config_manager = DummyConfig()
    cli.run()
    output = capsys.readouterr().out.strip().splitlines()
    assert output == ["bar"]
    assert cli.config_manager.data["foo"] == "bar"
