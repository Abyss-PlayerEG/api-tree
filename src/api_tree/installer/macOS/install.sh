#!/bin/bash

set -e

INSTALL_DIR="/usr/local/bin"
LINK_NAME="api-tree"
SOURCE="$(cd "$(dirname "$0")" && pwd)/api-tree"

echo "========================================"
echo "  api-tree Installer"
echo "========================================"
echo ""
echo "  This script will:"
echo "  - Remove quarantine attributes from the binary"
echo "  - Make 'api-tree' available as a system command"
echo "  - Create config directory at ~/.config/api-tree"
echo ""
echo "  By continuing, you acknowledge that this software"
echo "  is provided as-is without warranty of any kind."
echo ""
read -rp "  Do you want to proceed? (Yes/No): " CONFIRM
if [[ "$CONFIRM" != "Yes" && "$CONFIRM" != "yes" ]]; then
    echo "  Installation cancelled."
    exit 0
fi
echo ""

if [ ! -f "$SOURCE" ]; then
    echo "Error: api-tree binary not found at $SOURCE"
    exit 1
fi

# Remove quarantine attribute to bypass macOS Gatekeeper
xattr -cr "$(dirname "$SOURCE")" 2>/dev/null || true

if [ -w "$INSTALL_DIR" ]; then
    ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
else
    sudo ln -sf "$SOURCE" "$INSTALL_DIR/$LINK_NAME"
fi

mkdir -p ~/.config/api-tree

echo "Installed api-tree to $INSTALL_DIR/$LINK_NAME"
echo "Run 'api-tree --init-config' to create default config"