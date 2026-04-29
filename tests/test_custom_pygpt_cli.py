# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Custom Pygpt Cli module (tests)

from hueyos.pygpt_custom_cli import CustomPyGPT


def test_generate_reply():
    bot = CustomPyGPT()
    assert bot.generate_reply("hello") == "Echo: hello"


def test_load_main_prompt(tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("default text")
    bot = CustomPyGPT(prompt_file=prompt_file)
    assert bot.main_prompt == "default text"


def test_pygpt_wrappers_export_maintained_implementation():
    from huey.memory.PY.pygpt_custom_cli import CustomPyGPT as MaintainedCustomPyGPT
    from huey.pygpt_custom_cli import CustomPyGPT as HueyCustomPyGPT
    from hueyos.pygpt_custom_cli import CustomPyGPT as HueyOSCustomPyGPT

    assert HueyCustomPyGPT is MaintainedCustomPyGPT
    assert HueyOSCustomPyGPT is MaintainedCustomPyGPT


def test_run_cli_records_chat_messages(monkeypatch, capsys):
    bot = CustomPyGPT()
    inputs = iter(["", "list pdfs", "hello", "exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.setattr(bot, "_handle_list_pdfs", lambda: ["manual.pdf"])

    bot.run_cli()

    assert bot.memory.get_messages() == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Echo: hello"},
    ]
    output = capsys.readouterr().out
    assert "Available PDFs:" in output
    assert "- manual.pdf" in output
