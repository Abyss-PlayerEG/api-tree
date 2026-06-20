# AGENTS.md — api-tree

## Project Overview

api-tree is a CLI tool that renders OpenAPI (Swagger) specifications as terminal tree diagrams. Pure Python 3.14, zero third-party dependencies.

## Quick Reference

| Action | Command |
|--------|---------|
| Run (dev) | `uv run api-tree` |
| Type check | `uv run mypy src/api_tree/` |
| Build (macOS) | `bash script/mac-build.sh` |
| Build (macOS test) | `bash script/mac-build.sh test-build` |
| Build (Windows) | `script\win-build.bat` |
| Build (Windows test) | `script\win-build.bat test-build` |
| Generate single-file | `uv run python src/api_tree/tools/merge_src.py <version> --tag <tag>` |

## Project Structure

```
src/api_tree/
├── __init__.py          # Package init, exports __version__, __tag__
├── main.py              # Entry point, help text (docstring)
├── app/
│   ├── args.py          # CLI argument parsing, Args dataclass
│   ├── cli.py           # Main entry: encoding setup → parse → run
│   ├── core.py          # Main flow: fetch → build tree → output
│   ├── config.py        # Config file management
│   ├── color.py         # ANSI color constants
│   ├── console.py       # Terminal tree printing
│   ├── fetcher.py       # OpenAPI fetch (URL/file)
│   ├── tree.py          # Tree building and matching
│   ├── html.py          # HTML export
│   ├── agent_output.py  # LLM-optimized output (markdown/json/curl)
│   ├── rag_output.py    # RAG knowledge base output (jsonl/json)
│   └── updater.py       # Update command (GitHub Releases, SSL, SHA256)
├── installer/
│   ├── macOS/           # install.sh, uninstall.sh
│   └── Windows/         # install.bat, uninstall.bat
└── tools/
    └── merge_src.py     # Single-file builder, --tag, --version-only
```

## Code Conventions

- Python 3.14, type hints optional (mypy `check_untyped_defs = true`)
- No third-party dependencies (stdlib only)
- Docstrings in both Chinese and English
- Module-level imports at top, function-level imports inside functions
- No comments unless asked

## Version System

- Version format: `yy.mm.dd.hhmm` (e.g., `26.06.20.1139`)
- `_version.py` is generated at build time, not committed to git
- `__tag__` identifies build type: `python-script` / `macos-zip` / `win64-zip` / `win64-setup`
- `DEV` / `dev` are fallback values for development environment

## Build Flow

1. `merge_src.py VERSION --tag python-script` → single-file `.py`
2. `merge_src.py VERSION --tag <platform-tag> --version-only` → `_version.py` for PyInstaller
3. PyInstaller builds the binary
4. `rm -f src/api_tree/_version.py` → cleanup

## Update System

- `update --check`: fetch GitHub Releases API → compare versions
- `update`: download → SHA256 verify → backup → replace → cleanup
- SSL: tries default → macOS keychains → Linux CA paths → certifi → raise error
- Windows locked files: rename to `.old` instead of delete
- Only release versions (`yy.mm.dd.hhmm` format) can use update commands
