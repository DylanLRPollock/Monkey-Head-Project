from monkey_head.pygpt_custom_cli import CustomPyGPT


def test_generate_reply():
    bot = CustomPyGPT()
    assert bot.generate_reply("hello") == "Echo: hello"
