# ==================================================
# This file is a part of the 'Monkey Head Project'
# Website:   https://dlrp.ca
# GitHub:  https://github.com/DylanLRPollock/Monkey-Head-Project
# License:   https://opensource.org/license/gpl-3-0
# Overseen By:   Dylan L.R. Pollock
# Updated: 06.05.2025
# ==================================================
# huey/cli.py

import argparse
from pathlib import Path
from .main import main as huey_main
from .utils import convert_image, convert_images_in_directory


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Huey Project Command-Line Interface")

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run the Huey application")
    run_parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file",
        default="config.yaml",
    )
    run_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output"
    )

    convert_parser = subparsers.add_parser("convert", help="Convert image files")
    convert_parser.add_argument("input", help="Input file or directory")
    convert_parser.add_argument("--format", required=True, help="Output format")
    convert_parser.add_argument("--output", help="Output file or directory")
    convert_parser.add_argument(
        "--quality",
        type=int,
        default=100,
        help="Quality for conversion (default: 100)",
    )

    return parser.parse_args()


def run_cli():
    """Run the CLI application."""
    args = parse_arguments()

    if args.command == "convert":
        inp = Path(args.input)
        if inp.is_dir():
            convert_images_in_directory(
                str(inp), args.format, args.output, quality=args.quality
            )
        else:
            convert_image(str(inp), args.format, args.output, quality=args.quality)
        return

    if args.verbose:
        print("Verbose mode enabled.")
    # Pass the config file path to main
    huey_main(config_file=args.config)


if __name__ == "__main__":
    run_cli()
