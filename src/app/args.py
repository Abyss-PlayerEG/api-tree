"""Command-line argument parsing."""

import sys
from dataclasses import dataclass


@dataclass
class Args:
    """Parsed command-line arguments."""
    source: str = "http://localhost:8080"
    search: str = ""
    output_html: bool = False


HELP_TEXT = """Fetch OpenAPI route information and print as a tree structure in the terminal.

Usage:
    <python-tool-command>                          # Default: localhost:8080
    <python-tool-command> http://localhost:9090    # Specify server address
    <python-tool-command> /path/to/openapi.json    # Read from local JSON file
    <python-tool-command> -s auth                  # Search paths containing "auth"
    <python-tool-command> --html                   # Also output as HTML to ~/Downloads/
    <python-tool-command> -h                       # Show help
"""


def parse_args(argv: list[str] | None = None) -> Args:
    """Parse command-line arguments.
    
    Args:
        argv: Arguments to parse (defaults to sys.argv[1:])
    
    Returns:
        Parsed Args instance
    
    Raises:
        SystemExit: On invalid arguments
    """
    if argv is None:
        argv = sys.argv[1:]
    
    args = Args()
    i = 0
    
    while i < len(argv):
        if argv[i] == "-s" and i + 1 < len(argv):
            args.search = argv[i + 1].lower()
            i += 2
        elif argv[i] == "--html":
            args.output_html = True
            i += 1
        elif argv[i] in ("-h", "--help"):
            print(HELP_TEXT)
            sys.exit(0)
        elif argv[i].startswith("-"):
            print(f"Error: Unknown option '{argv[i]}'", file=sys.stderr)
            print(HELP_TEXT)
            sys.exit(1)
        else:
            args.source = argv[i]
            i += 1
    
    return args
