# Monkey Head Project
# By: Dylan L.R. Pollock
# www.dlrp.ca
# HueyOS: Config module (huey/memory/PY)

# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.11.2025
# ==================================================
# huey/config.py


def load_config(config_file: str = "config.yaml"):
    """Load configuration settings from a YAML file."""
    try:
        import yaml
    except ImportError as exc:
        raise ImportError("PyYAML is required to load configuration.") from exc

    try:
        with open(config_file, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Configuration file '{config_file}' not found."
        ) from exc
    except yaml.YAMLError as exc:
        raise Exception(f"Error parsing configuration file: {exc}") from exc
