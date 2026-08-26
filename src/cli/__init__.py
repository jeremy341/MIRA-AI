"""CLI entry point for MIRA - registers and dispatches all subcommands."""

import sys

from src.version import __version__
from src.pipeline.registry import get_commands

from . import train  # noqa: F401
from . import inference  # noqa: F401
from . import data as data_module  # noqa: F401
from . import system  # noqa: F401
from . import generate  # noqa: F401
from . import dashboard as dashboard_module  # noqa: F401
from . import wizard  # noqa: F401

__all__ = ["main"]


def main():
    import argparse

    from src.exceptions import MiraError
    from src.logger import get_logger

    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(
        description="MIRA CLI - Machine Intelligence for Recycling Automation",
        epilog="""\
Examples:
  mira live --model mira_exp014_int8.tflite
  mira train --config experiments/exp014_yolo11n_multidataset.yaml
  mira train --model yolo11n.pt --dataset datasets/trashnet_labeled/dataset.yaml --epochs 50
  mira merge --sources taco_trashnet roboflow warp --output datasets/mira_merged
  mira benchmark --models mira_exp014.pt mira_exp014_int8.tflite
  mira models
  mira experiments
  mira doctor
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"MIRA {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    for name, entry in get_commands().items():
        sub = subparsers.add_parser(name, help=entry.help_text)
        if entry.add_args:
            entry.add_args(sub)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = get_commands()
    if args.command in commands:
        try:
            commands[args.command].fn(args)
        except MiraError as e:
            logger.error(str(e))
            print(f"\nError: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nInterrupted by user.")
            sys.exit(130)
        except Exception as e:
            logger.exception("Unexpected error in command '%s': %s", args.command, e)
            print(f"\nUnexpected error: {e}")
            print("Try running 'mira doctor' to diagnose common issues.")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

