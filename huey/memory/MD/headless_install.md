# Headless Installation

For servers without a graphical environment you can run the license
agreement from the command line.

```bash
python monkey_head/license_cli.py
```

`license_cli.py` prints the license text and prompts whether you accept
the terms. If you enter anything other than `yes` or `no` it asks again
until a valid response is received. Any errors during this process are
logged to `memory/LOGS/app.log`.

Once the license is accepted you can start a lightweight headless session
with:

```bash
python run.py --minimal
```

This launches a very small echo chatbot without any GUI dependencies. For a
graphical demonstration you can instead run:

```bash
python run.py --simple-chat
```

Declining the license raises `RuntimeError` and leaves the configuration
file unchanged.
