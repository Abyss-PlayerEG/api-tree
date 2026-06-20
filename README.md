# API Tree CLI

> 📖 [简体中文](readme/SimplifiedChinese.md) | [繁體中文](readme/TraditionalChinese.md)

A lightweight CLI tool that renders OpenAPI (Swagger) specifications as beautiful terminal tree diagrams. Supports local files and remote servers, with keyword search, LLM-optimized output, and RAG knowledge base export.

## Features

- **Zero Dependencies** — Pure Python 3 standard library. No third-party packages required.
- **Multi-Source** — Read local JSON files or fetch from remote OpenAPI servers.
- **Smart Search** — `-s` flag filters endpoints by path, method, or summary.
- **Color-Coded Methods** — HTTP methods highlighted in distinct colors:

  | Method | Color |
  |--------|-------|
  | GET | Green |
  | POST | Blue |
  | PUT | Yellow |
  | DELETE | Red |
  | PATCH | Magenta |

- **HTML Export** — `--html` saves a styled HTML file with Catppuccin light/dark theme toggle.
- **Agent Output** — `--agent-output` generates LLM-friendly formats for AI-assisted development.
- **RAG Export** — `--rag-output` generates structured chunks for vector databases and retrieval systems.
- **Smart Path Merging** — Auto-collapses single-child path segments for cleaner output.
- **Springdoc Compatible** — Auto-appends `/v3/api-docs` to bare URLs.

## Installation

### Standalone executables

Download from [GitHub Releases](https://github.com/Abyss-PlayerEG/api-tree/releases) — no Python required.

**macOS**: If you see "api-tree cannot be opened because the developer cannot be verified", run:
```bash
xattr -cr /path/to/api-tree
```
Or right-click the binary → Open → Open Anyway.

### Build from source

```bash
git clone https://github.com/Abyss-PlayerEG/api-tree.git
cd api-tree
uv sync
uv run api-tree
```

### Future

- [ ] `pip install api-tree`
- [ ] `pipx install api-tree`
- [ ] `brew install api-tree`
- [ ] `winget install api-tree`

## Quick Start

```bash
# Connect to local server (default: localhost:8080)
api-tree

# Specify a server
api-tree http://localhost:9090

# Read from local file
api-tree ./openapi.json
```

## Usage

### Basic

```bash
api-tree                              # Default: localhost:8080
api-tree http://localhost:9090        # Custom server
api-tree /path/to/openapi.json        # Local file
api-tree -s auth                      # Search endpoints containing 'auth'
api-tree --html                       # Export as HTML
```

> If the URL has no path (e.g. `http://localhost:9090`), the tool auto-appends `/v3/api-docs`. To use a different endpoint, specify the full URL directly.

### Agent Output (for AI-assisted development)

Generate LLM-optimized representations of your API structure. Useful when feeding API context to AI coding assistants.

```bash
api-tree --agent-output markdown      # Clean markdown table
api-tree --agent-output json          # Structured JSON
api-tree --agent-output curl          # Ready-to-use curl commands
```

**Use cases:**
- Feed API structure to ChatGPT/Claude for code generation
- Generate curl commands for API testing
- Create API reference docs for AI pair programming

### RAG Knowledge Base Export

Generate structured chunks for vector databases and retrieval-augmented generation systems.

```bash
api-tree --rag-output jsonl           # One JSON object per line (for vector DB ingestion)
api-tree --rag-output json            # Full JSON structure
api-tree --rag-chunk-size 20          # Endpoints per chunk (default: 10)
```

**Use cases:**
- Build a searchable API knowledge base
- Enhance RAG systems with endpoint context
- Feed structured data to embedding pipelines

### Configuration

```bash
api-tree --init-config                # Generate ~/.config/api-tree/config.json
api-tree --show-config                # Show current config
```

### Update

```bash
api-tree update --check               # Check for new version (no install)
api-tree update                       # Download and install latest version
```

Supports single-file `.py`, macOS zip, Windows zip, and Windows installer. Downloads are verified with SHA256 and auto-rolled back on failure.

Config file:
```json
{
    "output_dir": "~/Downloads",
    "default_url": "http://localhost:8080"
}
```

## Screenshots

![Terminal tree view](/readme/img/1.png)

![Search filter](/readme/img/2.png)

![HTML export](/readme/img/3.png)

![Color coding](/readme/img/4.png)
