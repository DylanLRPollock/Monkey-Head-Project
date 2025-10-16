# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Test Custom Pygpt Cli module (tests)

from monkey_head.pygpt_custom_cli import CustomPyGPT


def test_generate_reply():
    bot = CustomPyGPT()
    assert bot.generate_reply("hello") == "Echo: hello"


def test_load_main_prompt(tmp_path):
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("default text")
    bot = CustomPyGPT(prompt_file=prompt_file)
    assert bot.main_prompt == "default text"
