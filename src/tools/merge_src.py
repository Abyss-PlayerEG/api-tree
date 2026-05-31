#!/usr/bin/env python3
"""Merge src/ package modules into a single main.py file."""

import re
import sys
from datetime import datetime
from pathlib import Path

# Modules that must be loaded first (dependencies)
PRIORITY_MODULES = ["color.py", "_version.py", "banner.py", "args.py"]
# Module that must be loaded last (entry point)
ENTRY_MODULE = "cli.py"


def discover_modules(src_dir: Path) -> list[str]:
    """Auto-discover all .py modules in src/app/ directory."""
    modules = []
    for f in sorted(src_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        modules.append(f.name)
    return modules


def sort_modules(modules: list[str]) -> list[str]:
    """Sort modules: priority first, entry last, rest in middle."""
    priority = [m for m in PRIORITY_MODULES if m in modules]
    entry = [m for m in [ENTRY_MODULE] if m in modules]
    rest = [m for m in modules if m not in priority and m not in entry]
    return priority + rest + entry

# Imports to remove
RELATIVE_IMPORT_RE = re.compile(r"^from \.\w+ import .+$", re.MULTILINE)
IMPORT_RE = re.compile(r"^import .+$", re.MULTILINE)
FROM_IMPORT_RE = re.compile(r"^from [\w.]+ import .+$", re.MULTILINE)


def extract_code(filepath: Path) -> str:
    """Extract module code, removing all imports (moved to top)."""
    code = filepath.read_text(encoding="utf-8")
    # Remove relative imports
    code = RELATIVE_IMPORT_RE.sub("", code)
    # Remove standard imports
    code = IMPORT_RE.sub("", code)
    code = FROM_IMPORT_RE.sub("", code)
    # Clean up multiple blank lines
    code = re.sub(r"\n{3,}", "\n\n", code)
    code = code.strip() + "\n"
    return code


def get_version() -> str:
    """Generate version string from date (yy.M.d)."""
    now = datetime.now()
    return f"{now.year % 100}.{now.month}.{now.day}"


def main():
    # Get version from argument or generate from date
    version = sys.argv[1] if len(sys.argv) > 1 else get_version()
    
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src" / "app"
    output_file = project_root / "dist" / "api-tree.py"

    # Start with shebang and docstring
    header = '''#!/usr/bin/env python3
"""
Fetch OpenAPI route information and print as a tree structure in the terminal.

Usage:
    <python-tool-command>                          # Default: localhost:8080
    <python-tool-command> http://localhost:9090    # Specify server address
    <python-tool-command> /path/to/openapi.json    # Read from local JSON file
    <python-tool-command> -s auth                  # Search paths containing "auth"
    <python-tool-command> --html                   # Also output as HTML to ~/Downloads/
    <python-tool-command> -h                       # Show help
"""

'''

    # Auto-discover and sort modules
    discovered = discover_modules(src_dir)
    modules = sort_modules(discovered)
    print(f"Discovered modules: {modules}")

    # Collect standard imports from all modules
    all_imports = set()
    module_codes = []

    for mod_name in modules:
        mod_path = src_dir / mod_name
        if not mod_path.exists():
            print(f"Warning: {mod_path} not found, skipping")
            continue

        code = mod_path.read_text(encoding="utf-8")

        # Extract standard library imports
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or (stripped.startswith("from ") and "from ." not in stripped):
                # Only keep non-relative imports and exclude src imports
                if not stripped.startswith("from .") and not stripped.startswith("from src"):
                    all_imports.add(stripped)

        # Get code without relative imports
        clean_code = extract_code(mod_path)
        module_codes.append(f"# === {mod_name} ===\n{clean_code}")

    # Build final content
    imports_section = "\n".join(sorted(all_imports)) + "\n"
    body = "\n\n".join(module_codes)

    # Add version and main entry point
    main_entry = f'''

__version__ = "{version}"

if __name__ == "__main__":
    main()
'''

    content = header + imports_section + "\n" + body + main_entry

    # Replace DEV version with actual version
    content = content.replace('__version__ = "DEV"', f'__version__ = "{version}"')
    print(f"Version: {version}")

    # Ensure dist directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(content, encoding="utf-8")
    print(f"Generated: {output_file}")

    # Write version to src/_version.py for PyInstaller
    version_file = project_root / "src" / "_version.py"
    version_file.write_text(f'__version__ = "{version}"\n', encoding="utf-8")
    print(f"Version file: {version_file}")


if __name__ == "__main__":
    main()
