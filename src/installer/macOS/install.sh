#!/bin/bash

set -e

INSTALL_DIR="/usr/local/bin"
LINK_NAME="api-tree"
SOURCE="$(cd "$(dirname "$0")" && pwd)/api-tree"

if [ ! -f "$SOURCE" ]; then
    echo "Error: api-tree binary not found at $SOURCE"
    exit 1
fi

if [ -w "$INSTALL_DIR" ]; then
    ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
else
    sudo ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
fi

mkdir -p ~/.config/api-tree

echo "Installed api-tree to $INSTALL_DIR/$LINK_NAME"
echo "Run 'api-tree --init-config' to create default config"