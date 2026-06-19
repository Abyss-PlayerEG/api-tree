#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "Checking uv..."
if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv not found."
    echo "        Install: https://docs.astral.sh/uv/"
    exit 1
fi

echo "Creating virtual environment and syncing dependencies..."
uv sync

echo ""
echo "Done. Run with: uv run python src/api_tree/main.py"
