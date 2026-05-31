"""Command-line interface entry point."""

from .args import parse_args
from .app import run


def main():
    """Main entry point."""
    try:
        args = parse_args()
        run(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
