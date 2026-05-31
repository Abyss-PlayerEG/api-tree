#!/usr/bin/env python3
"""Patch __version__ in src/__init__.py for PyInstaller build.

Usage:
    python src/tools/patch_version.py <version>
    python src/tools/patch_version.py restore
"""

import sys
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: patch_version.py <version|restore>")
        sys.exit(1)

    project_root = Path(__file__).parent.parent.parent
    init_file = project_root / "src" / "__init__.py"
    backup_file = project_root / "src" / "__init__.py.bak"

    action = sys.argv[1]

    if action == "restore":
        if backup_file.exists():
            backup_file.replace(init_file)
            print(f"Restored: {init_file}")
        else:
            print(f"No backup found: {backup_file}")
        return

    version = action

    # Backup original
    if init_file.exists():
        backup_file.write_text(init_file.read_text(encoding="utf-8"), encoding="utf-8")

    # Patch version
    content = init_file.read_text(encoding="utf-8")
    content = content.replace('__version__ = "DEV"', f'__version__ = "{version}"')
    init_file.write_text(content, encoding="utf-8")
    print(f"Patched {init_file}: __version__ = \"{version}\"")


if __name__ == "__main__":
    main()
