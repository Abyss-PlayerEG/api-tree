"""Command-line interface entry point."""

from .args import parse_args
from .app import run


def main():
    """Main entry point."""
    args = parse_args()
    run(args)
