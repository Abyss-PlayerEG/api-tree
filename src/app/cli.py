"""Command-line interface entry point."""

import io
import sys

from .args import parse_args
from .core import run


def _setup_encoding():
    """Ensure UTF-8 encoding for stdout/stderr and console, cross-platform."""
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper) and stream.encoding != 'utf-8':
            try:
                stream.reconfigure(encoding='utf-8')
            except Exception:
                pass

    if sys.platform == 'win32':
        import ctypes
        try:
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass


def main():
    """Main entry point."""
    _setup_encoding()

    try:
        args = parse_args()
        run(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
