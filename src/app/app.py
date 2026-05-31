"""Main application logic and orchestration."""

import sys

from .color import Color
from .fetcher import fetch_openapi
from .tree import build_tree, count_endpoints
from .console import print_tree
from .html import render_html_tree
from .args import Args


def run(args: Args) -> None:
    """Run the API tree application.
    
    Args:
        args: Parsed command-line arguments
    """
    spec = fetch_openapi(args.source)
    paths = spec.get("paths", {})

    if not paths:
        print("No API paths found", file=sys.stderr)
        sys.exit(1)

    tree = build_tree(paths)
    total = count_endpoints(tree)

    if args.search:
        print(f'\nMatched - "{args.search}"')
    else:
        title = spec.get("info", {}).get("title", "API")
        print(f"\n{Color.BOLD}{title} API Endpoint Tree{Color.RESET}  ({total} endpoints)")

    print_tree(tree, search=args.search)
    print()
    if not args.search:
        print(f"{Color.DIM}Total: {total} endpoints{Color.RESET}")

    if args.output_html:
        title = spec.get("info", {}).get("title", "API")
        output_path = render_html_tree(tree, title, total, args.search)
        print(f"{Color.DIM}HTML saved to: {output_path}{Color.RESET}")
