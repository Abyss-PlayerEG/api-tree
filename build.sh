#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo "  API Tree - Build Script (uv)"
echo "========================================"
echo ""

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "[ERROR] uv not found."
    echo "        Install it from: https://docs.astral.sh/uv/"
    exit 1
fi

# Sync dependencies
echo "[0/3] Syncing dependencies..."
uv sync

# Record start time
START_TIME=$(date +%T)

# Clean previous build artifacts
echo "[1/3] Cleaning previous build artifacts..."
rm -rf build dist

# Run PyInstaller via uv
echo "[2/3] Building executable..."
uv run pyinstaller --onefile --name api-tree --clean --noconfirm --icon=icon.ico api-tree.py

# Show result
echo "[3/3] Build complete."
echo ""
echo "---------------------------------------"
if [[ -f dist/api-tree ]]; then
    SIZE=$(wc -c < dist/api-tree | tr -d ' ')
    SIZE_KB=$((SIZE / 1024))
    SIZE_MB=$((SIZE / 1048576))
    echo "  Output : dist/api-tree"
    echo "  Size   : ${SIZE} bytes (approx. ${SIZE_MB} MB / ${SIZE_KB} KB)"
else
    echo "  [WARNING] Output file not found."
fi
echo "  Start  : ${START_TIME}"
echo "  End    : $(date +%T)"
echo "---------------------------------------"
echo ""
echo "========================================"
echo "  Build Successful!"
echo "========================================"
