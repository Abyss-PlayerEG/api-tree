#!/usr/bin/env bash
cd "$(dirname "$0")/.."

echo "Cleaning build artifacts..."

if [ -d build ]; then
    rm -rf build
    echo "  Removed build/"
fi
if [ -d dist ]; then
    rm -rf dist
    echo "  Removed dist/"
fi
if [ -f src/api_tree/_version.py ]; then
    rm -f src/api_tree/_version.py
    echo "  Removed src/api_tree/_version.py"
fi

echo "Done."
