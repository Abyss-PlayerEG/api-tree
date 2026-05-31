# API Tree CLI

> 📖 [简体中文](readme/SimplifiedChinese.md) | [繁體中文](readme/TraditionalChinese.md)

A lightweight command-line tool that renders OpenAPI (Swagger) specifications as beautiful terminal tree diagrams. Supports reading from local files or remote servers, with keyword-based search and filtering.

## Features

- **Zero Dependencies** — Uses only the Python 3 standard library. No third-party packages required.
- **Multi-Source** — Reads local JSON files or fetches from a remote OpenAPI server (default port `:8080`).
- **Smart Search** — Use the `-s` flag to quickly filter endpoints by path, method, or summary.
- **Color-Coded Methods** — HTTP methods are highlighted in distinct colors:

  | Method | Color |
  |--------|-------|
  | GET | Green |
  | POST | Blue |
  | PUT | Yellow |
  | DELETE | Red |
  | PATCH | Magenta |

- **HTML Image Export** — Use the `--html` flag to save the tree as a styled HTML file with Catppuccin light/dark theme toggle. Output directory can be configured.

- **Agent Optimized Output** — Use `--agent-output` to generate LLM-friendly formats (markdown/json/curl) optimized for AI agents and automated workflows.

- **RAG Knowledge Base Output** — Use `--rag-output` to generate structured chunks (jsonl/json) for vector databases and RAG retrieval systems.

- **Smart Path Merging** — Automatically collapses single-child path segments for cleaner output.
- **Springdoc Compatible** — Auto-appends `/v3/api-docs` to the provided URL.

## Quick Start

### Prerequisites

- Python 3.6+

### Run

Connect to `http://localhost:8080` by default:
```bash
python main.py
```

### Usage

```bash
python main.py                          # Default: localhost:8080
python main.py http://localhost:9090    # Custom server address
python main.py /path/to/openapi.json   # Read from local file
python main.py -s auth                  # Search endpoints containing 'auth'
python main.py --html                   # Also export as HTML
python main.py --agent-output markdown  # LLM-optimized output (markdown/json/curl)
python main.py --rag-output jsonl       # RAG knowledge base output (jsonl/json)
python main.py --rag-chunk-size 20      # Endpoints per RAG chunk (default: 10)
python main.py --init-config            # Generate default config file
python main.py -h                       # Show help
```

> If the URL has no path (e.g. `http://localhost:9090`), the tool automatically appends `/v3/api-docs`. To use a different endpoint, specify the full URL directly (e.g. `http://localhost:9090/swagger.json`).

## Configuration

Generate a default config file:
```bash
python main.py --init-config
```

This creates `~/.config/api-tree/config.json` with default settings:
```json
{
    "output_dir": "~/Downloads",
    "default_url": "http://localhost:8080"
}
```

Edit this file to customize:
- `output_dir`: Output directory for HTML exports and other file outputs
- `default_url`: Default OpenAPI server URL when no URL is specified

## Build Executable

Build a standalone `.exe` with PyInstaller:

```bash
pip install pyinstaller
build.bat
```

Output: `dist/api-tree.exe`

## Screenshots

![Screenshot](/readme/img/1.png)

![Screenshot](/readme/img/2.png)

![Screenshot](/readme/img/3.png)

![Screenshot](/readme/img/4.png)
