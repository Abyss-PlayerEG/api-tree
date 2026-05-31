"""Main application logic and orchestration."""

import json
import sys
from pathlib import Path

from .color import Color
from .fetcher import fetch_openapi
from .tree import build_tree, count_endpoints, TreeMatcher
from .console import print_tree
from .html import render_html_tree
from .agent_output import generate_agent_output
from .rag_output import generate_rag_output
from .args import Args


def _init_config() -> None:
    """Generate default config file."""
    config_dir = Path.home() / ".config" / "api-tree"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    
    if config_file.exists():
        print(f"Config file already exists: {config_file}")
        print("Edit it manually or delete it first.")
        return
    
    default_config = {
        "output_dir": "~/Downloads",
        "default_url": "http://localhost:8080"
    }
    
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)
    
    print(f"Config file created: {config_file}")
    print("Edit it to customize output directory and default URL.")


def run(args: Args) -> None:
    """Run the API tree application.
    
    Args:
        args: Parsed command-line arguments
    """
    # Handle init-config command
    if args.init_config:
        _init_config()
        return
    
    spec = fetch_openapi(args.source)
    paths = spec.get("paths", {})

    if not paths:
        print("No API paths found", file=sys.stderr)
        sys.exit(1)

    tree = build_tree(paths)
    total = count_endpoints(tree)

    title = spec.get("info", {}).get("title", "API")
    
    # Handle agent output mode
    if args.agent_output:
        output = generate_agent_output(tree, title, total, args.agent_output, args.search)
        print(output)
        return
    
    # Handle RAG output mode
    if args.rag_output:
        output = generate_rag_output(tree, title, total, args.rag_output, 
                                    args.rag_chunk_size, args.search)
        print(output)
        return
    
    # Normal terminal output
    if args.search:
        print(f'\nMatched - "{args.search}"')
    else:
        print(f"\n{Color.BOLD}{title} API Endpoint Tree{Color.RESET}  ({total} endpoints)")

    matcher = TreeMatcher(tree, args.search) if args.search else None
    print_tree(tree, search=args.search, matcher=matcher)
    print()
    if not args.search:
        print(f"{Color.DIM}Total: {total} endpoints{Color.RESET}")

    if args.output_html:
        output_path = render_html_tree(tree, title, total, args.search)
        print(f"{Color.DIM}HTML saved to: {output_path}{Color.RESET}")
