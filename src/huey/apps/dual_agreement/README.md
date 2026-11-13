# Dual Agreement Review

A small Tkinter desktop port of the supplied sequential agreement flow.

## Run

With the project installed:

```bash
python -m huey.apps.dual_agreement
```

From a repository checkout without installing the package:

```bash
PYTHONPATH=src python -m huey.apps.dual_agreement
```

Tkinter is part of Python's standard library. On Debian, install the system
Tk bindings if they are not already present:

```bash
sudo apt install python3-tk
```

The application requires separate acceptance on each screen and then shows a
five-second completion countdown. It does not collect, persist, or transmit
acceptance records. The second document is explicitly labeled as an excerpt
because that is all the supplied source contained; the UI links to the complete
GPL-3.0 text.
