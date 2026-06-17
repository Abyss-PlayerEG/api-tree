#!/usr/bin/env bash
set -euo pipefail

# Change to project root (parent of script/)
cd "$(dirname "$0")/.."

echo "========================================"
echo "  API Tree - Mypy Type Check"
echo "========================================"
echo ""

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv not found."
    echo "        Install it from: https://docs.astral.sh/uv/"
    exit 1
fi

# Sync dependencies (ensures mypy is installed)
echo "[1/2] Syncing dependencies..."
uv sync

# Run mypy
echo "[2/2] Running mypy..."
echo ""
uv run mypy src/app src/__init__.py src/main.py src/tools

echo ""
echo "========================================"
echo "  Type Check PASSED - no issues found"
echo "========================================"
