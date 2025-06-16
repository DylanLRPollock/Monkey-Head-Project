# Running the Monkey Head Project

This guide explains the different ways to launch and test the project.

## Launching the Application

- `python run.py` – start the graphical interface.
- `python run.py --cli` – force command‑line mode if no GUI is available.
- `python run.py --minimal` – run the lightweight echo chatbot.
- `python run.py --simple-chat` – open a simple Tkinter demo.
- `python run.py --module package.module[:func]` – execute a module's callable.
- `python run.py --system-check` – perform environment checks and exit.
- `python run.py --docker-compose` – build and start the Docker Compose stack.
- `python run.py --kubernetes` – deploy manifests from the `k8s/` directory.
- `python launcher.py [command]` – unified script to run or install the project. Use
  `install`, `uninstall`, `fresh-install`, or `system-check` commands, or omit the
  command to start the application.

## Helper Scripts

Two wrapper scripts simplify starting the project:

- `run.sh` (Linux/macOS) activates the virtual environment and runs `run.py`.
- `run.bat` (Windows) does the same on Windows systems. Use `run.bat help` to
  list available options or `run.bat tests` to execute the test suite.

## Running Tests

After installation you can run the built‑in test suite:

```bash
./run-tests.sh
```
On Windows use:
```cmd
run-tests.bat
```

Each script runs `pytest` with coverage reporting and stores the results in
`memory/LOGS/test_results.log`.

Make sure the project is installed as described in [install.md](install.md) before using these commands.
