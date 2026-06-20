#!/usr/bin/env python3
"""
Fetch OpenAPI route information and print as a tree structure in the terminal.

Usage:
    api-tree                          # Default: from config or localhost:8080
    api-tree http://localhost:9090    # Specify server address
    api-tree /path/to/openapi.json    # Read from local JSON file
    api-tree -s auth                  # Search paths containing "auth"
    api-tree --html                   # Also output as HTML
    api-tree --agent-output markdown  # Output optimized for LLM agents (markdown/json/curl)
    api-tree --rag-output jsonl       # Output for RAG knowledge base (jsonl/json)
    api-tree --rag-chunk-size 20      # Endpoints per RAG chunk (default: 10)
    api-tree --init-config            # Generate default config file
    api-tree --show-config            # Show current config
    api-tree update                   # Update to latest version
    api-tree update --check           # Check for updates (no install)
    api-tree -v, --version            # Show version
    api-tree -h, --help               # Show help

Regex Search:
    Use $:{pattern} syntax with -s flag for regex matching.
    api-tree -s '$:{user|pet}'        # Match "user" or "pet"
    api-tree -s '$:{^/api/v1}'        # Paths starting with /api/v1
    api-tree -s '$:{GET|POST}'        # Match GET or POST methods
    api-tree -s '$:{create|update}'   # Match create or update

GitHub: https://github.com/Abyss-PlayerEG/api-tree

"""

import os
import sys
from pathlib import Path

# 设置 UTF-8 编码环境变量，确保中文输出不乱码
# Set UTF-8 encoding environment variable to ensure Chinese output is not garbled
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

# 将项目根目录加入搜索路径，确保 src 包可导入
# Add project root to search path to ensure src package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api_tree.app import main

if __name__ == "__main__":
    main()
