# Running the Monkey Head Project

This guide explains the different ways to launch and test the project.

## Launching the Application

- `python run.py` – start the graphical interface.
- `python run.py --cli` – force command‑line mode if no GUI is available.
- `python run.py --minimal` – run the lightweight echo chatbot.
- `python run.py --simple-chat` – open a simple Tkinter demo.

## Helper Scripts

Two wrapper scripts simplify starting the project:

- `run.sh` (Linux/macOS) activates the virtual environment and runs `run.py`.
- `run.bat` (Windows) does the same on Windows systems.

## Running Tests

After installation you can run the built‑in test suite:

```bash
./run-tests.sh
```

The script runs `pytest` with coverage reporting and stores the results in `logs/test_results.log`.

Make sure the project is installed as described in [install.md](install.md) before using these commands.
