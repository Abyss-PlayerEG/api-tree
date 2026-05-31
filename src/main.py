#!/usr/bin/env python3
"""
Fetch OpenAPI route information and print as a tree structure in the terminal.

Usage:
    <python-tool-command>                          # Default: localhost:8080
    <python-tool-command> http://localhost:9090    # Specify server address
    <python-tool-command> /path/to/openapi.json    # Read from local JSON file
    <python-tool-command> -s auth                  # Search paths containing "auth"
    <python-tool-command> --html                   # Also output as HTML to ~/Downloads/
    <python-tool-command> --agent-output markdown  # Output optimized for LLM agents (markdown/json/curl)
    <python-tool-command> --rag-output jsonl       # Output for RAG knowledge base (jsonl/json)
    <python-tool-command> --rag-chunk-size 20      # Endpoints per RAG chunk (default: 10)
    <python-tool-command> -v, --version            # Show version
    <python-tool-command> -h, --help               # Show help

Github: https://github.com/Ender-g/api-tree

"""

import sys
from pathlib import Path

# Add project root to path for src package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app import main

if __name__ == "__main__":
    main()
