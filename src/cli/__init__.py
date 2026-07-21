import sys
from pathlib import Path

_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from version import __version__
from pipeline.registry import get_commands

from cli import train  # noqa: F401
from cli import inference  # noqa: F401
from cli import data as data_module  # noqa: F401
from cli import system  # noqa: F401
from cli import generate  # noqa: F401
from cli import dashboard as dashboard_module  # noqa: F401
from cli import wizard  # noqa: F401


def main():
    import argparse

    from exceptions import MiraError
    from logger import get_logger

    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(
        description="MIRA CLI — Machine Intelligence for Recycling Automation",
        epilog="""\
Examples:
  mira live --model mira_exp014_int8.tflite
  mira train --config experiments/exp014_yolo11n_multidataset.yaml
  mira train --model yolo11n.pt --dataset datasets/mira_v2/dataset.yaml --epochs 50
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
            logger.exception(f"Unexpected error in command '{args.command}': {e}")
            print(f"\nUnexpected error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
