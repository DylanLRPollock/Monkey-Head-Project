# huey/config.py

import yaml


def load_config(config_file="config.yaml"):
    """Load configuration settings from a YAML file."""
    try:
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file '{config_file}' not found.")
    except yaml.YAMLError as e:
        raise Exception(f"Error parsing configuration file: {e}")
