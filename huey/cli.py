# huey/cli.py

import argparse
from .main import main as huey_main


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Huey Project Command-Line Interface")
    parser.add_argument(
        "--config", type=str, help="Path to configuration file", default="config.yaml"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    return parser.parse_args()


def run_cli():
    """Run the CLI application."""
    args = parse_arguments()
    if args.verbose:
        print("Verbose mode enabled.")
    # Pass the config file path to main
    huey_main(config_file=args.config)


if __name__ == "__main__":
    run_cli()
