# HueyOS Command Center Desktop

This is the Python desktop port of the supplied Command Center dashboard, placed
alongside the existing read-only backend in `src/huey/apps/command_center`.

## Run

From an installed project:

```bash
python -m huey.apps.command_center.desktop
```

From a source checkout:

```bash
PYTHONPATH=src python -m huey.apps.command_center.desktop
```

The UI uses Python's Tkinter standard-library module. On Debian, install its
system bindings if needed:

```bash
sudo apt install python3-tk
```

Migration progress, checklist state, and notes are saved locally in the user's
state directory. The dashboard uses the project's canonical HueyOS migration,
validation, safety, and V1 sample data. Repository and operator panels remain
mock-only. Validation commands can be copied but are never run. The app makes
no GitHub or other network requests and does not mutate runtime, memory,
governance, or physical systems. Full-state JSON import/export is validated
before the current state is replaced.
