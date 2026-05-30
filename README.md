# API Tree CLI

> 📖 [中文文档](readme/Chinese.md)

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

- **HTML Image Export** — Use the `--html` flag to save the tree as a styled HTML file with Catppuccin light/dark theme toggle. Output goes to your Downloads folder.

- **Smart Path Merging** — Automatically collapses single-child path segments for cleaner output.
- **Springdoc Compatible** — Auto-appends `/v3/api-docs` to the provided URL.

## Quick Start

### Prerequisites

- Python 3.6+

### Run

Connect to `http://localhost:8080` by default:
```bash
python api-tree.py
```

### Usage

```bash
python api-tree.py                          # Default: localhost:8080
python api-tree.py http://localhost:9090    # Custom server address
python api-tree.py /path/to/openapi.json   # Read from local file
python api-tree.py -s auth                  # Search endpoints containing 'auth'
python api-tree.py --html                   # Also export as HTML to ~/Downloads/
python api-tree.py -h                       # Show help
```

> If the URL has no path (e.g. `http://localhost:9090`), the tool automatically appends `/v3/api-docs`. To use a different endpoint, specify the full URL directly (e.g. `http://localhost:9090/swagger.json`).

## Build Executable

Build a standalone `.exe` with PyInstaller:

```bash
pip install pyinstaller
build.bat
```

Output: `dist/api-tree.exe`

## Screenshots

![Screenshot](/img/1.png)

![Screenshot](/img/2.png)

![Screenshot](/img/3.png)

![Screenshot](/img/4.png)
