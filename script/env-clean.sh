#!/usr/bin/env bash
cd "$(dirname "$0")/.."

if [ -d .venv ]; then
    echo "Removing .venv..."
    rm -rf .venv
    echo "Done."
else
    echo ".venv not found."
fi
