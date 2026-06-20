#!/bin/bash

set -e

LINK_PATH="/usr/local/bin/api-tree"

if [ -L "$LINK_PATH" ]; then
    if [ -w "/usr/local/bin" ]; then
        rm "$LINK_PATH"
    else
        sudo rm "$LINK_PATH"
    fi
    echo "Removed api-tree symlink"
else
    echo "api-tree not found in /usr/local/bin"
fi