# Headless Installation

For servers without a graphical environment you can run the license
agreement from the command line.

```bash
python monkey_head/license_cli.py
```

`license_cli.py` prints the license text and prompts whether you accept
the terms. If you enter anything other than `yes` or `no` it asks again
until a valid response is received. Any errors during this process are
logged to `app.log`.

Declining the license raises `RuntimeError` and leaves the configuration
file unchanged.
