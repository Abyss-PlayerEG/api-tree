#!/usr/bin/env bash
set -euo pipefail

# Change to project root (parent of script/)
cd "$(dirname "$0")/.."

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
echo "[0/4] Syncing dependencies..."
uv sync

# Record start time
START_TIME=$(date +%T)

# Clean previous build artifacts
echo "[1/4] Cleaning previous build artifacts..."
rm -rf build dist

# Generate version from current date (yy.mm.dd.hhmm)
VERSION=$(date +%y.%m.%d.%H%M)

# Optional version prefix
read -rp "Version prefix (Enter to skip): " PREFIX
if [[ -n "$PREFIX" ]]; then
    VERSION="${PREFIX}-${VERSION}"
fi

# Generate single-file version
echo "[1.5/4] Generating single-file api-tree-${VERSION}.py..."
uv run python src/api_tree/tools/merge_src.py "$VERSION"

# Run PyInstaller via uv (onedir for fast startup)
echo "[2/4] Building executable..."
uv run pyinstaller --onedir --name api-tree --clean --noconfirm --strip --icon=icon.ico src/api_tree/main.py

# Cleanup build-time version file
rm -f src/api_tree/_version.py

# Show result
echo "[3/4] Build complete."
echo ""
echo "---------------------------------------"
if [[ -f dist/api-tree/api-tree ]]; then
    echo "  Output : dist/api-tree/api-tree"
else
    echo "  [WARNING] Output file not found."
fi

# Copy install/uninstall scripts to dist
cp src/api_tree/installer/macOS/install.sh dist/api-tree/
cp src/api_tree/installer/macOS/uninstall.sh dist/api-tree/
chmod +x dist/api-tree/install.sh dist/api-tree/uninstall.sh

# Create zip archive
ARCHIVE=$(uname -s | tr '[:upper:]' '[:lower:]')
case "$ARCHIVE" in
    darwin) PLATFORM="macos" ;;
    linux)  PLATFORM="linux" ;;
    *)      PLATFORM="$ARCHIVE" ;;
esac
ZIP_NAME="api-tree-${VERSION}-${PLATFORM}.zip"
if [[ -f "dist/${ZIP_NAME}" ]]; then
    rm -f "dist/${ZIP_NAME}"
fi
(cd dist && zip -r "${ZIP_NAME}" api-tree/)
echo "  Zip    : dist/${ZIP_NAME}"

echo "  Start  : ${START_TIME}"
echo "  End    : $(date +%T)"
echo "---------------------------------------"
echo ""
echo "========================================"
echo "  Build Successful!"
echo "========================================"
