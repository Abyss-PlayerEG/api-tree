#!/usr/bin/env python3
"""Merge src/ package modules into a single main.py file."""

import ast
import re
import sys
from datetime import datetime
from pathlib import Path

# Modules that must be loaded first (dependencies)
PRIORITY_MODULES = ["color.py", "_version.py", "args.py"]
# Module that must be loaded last (entry point)
ENTRY_MODULE = "cli.py"


def discover_modules(src_dir: Path) -> list[str]:
    """Auto-discover all .py modules in src/app/ directory."""
    modules = []
    for f in sorted(src_dir.glob("*.py")):
        if f.name in ("__init__.py", "__main__.py"):
            continue
        modules.append(f.name)
    return modules


def sort_modules(modules: list[str]) -> list[str]:
    """Sort modules: priority first, entry last, rest in middle."""
    priority = [m for m in PRIORITY_MODULES if m in modules]
    entry = [m for m in [ENTRY_MODULE] if m in modules]
    rest = [m for m in modules if m not in priority and m not in entry]
    return priority + rest + entry


def extract_imports(filepath: Path) -> set[str]:
    """Use ast to extract all import statements from a file."""
    source = filepath.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    
    imports = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
        elif isinstance(node, ast.ImportFrom):
            # Skip relative imports
            if node.level > 0:
                continue
            module = node.module or ""
            # Skip src package imports
            if module.startswith("src"):
                continue
            names = ", ".join(alias.name + (f" as {alias.asname}" if alias.asname else "") for alias in node.names)
            imports.add(f"from {module} import {names}")
    return imports


def extract_code(filepath: Path) -> str:
    """Extract module code, removing imports and trailing whitespace."""
    code = filepath.read_text(encoding="utf-8")
    
    # Remove all import lines (relative and standard)
    lines = []
    for line in code.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            continue
        lines.append(line)
    code = "\n".join(lines)
    
    # Clean up multiple blank lines
    code = re.sub(r"\n{3,}", "\n\n", code)
    return code.strip() + "\n"


def _is_wrapper(node: ast.FunctionDef) -> tuple[bool, str]:
    """Check if a function is a trivial wrapper (just calls another function).
    Returns (True, target_name) or (False, "").
    """
    if len(node.body) != 1:
        return False, ""
    stmt = node.body[0]
    # Check: `return other_func(args...)`
    if isinstance(stmt, ast.Return) and stmt.value and isinstance(stmt.value, ast.Call):
        call = stmt.value
        if isinstance(call.func, ast.Name):
            return True, call.func.id
    return False, ""


def _is_simple_pass(node: ast.FunctionDef) -> bool:
    """Check if function body is just `pass`."""
    return len(node.body) == 1 and isinstance(node.body[0], ast.Pass)


def deduplicate_functions(code: str) -> str:
    """Remove duplicate function/class definitions, keeping the first occurrence."""
    tree = ast.parse(code)
    seen: set[str] = set()
    lines_to_remove: set[int] = set()

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in seen:
                # Remove this duplicate definition
                for i in range(node.lineno - 1, node.end_lineno):
                    lines_to_remove.add(i)
            else:
                seen.add(node.name)

    if not lines_to_remove:
        return code

    result_lines = []
    for i, line in enumerate(code.splitlines()):
        if i not in lines_to_remove:
            result_lines.append(line)
    return "\n".join(result_lines)


def remove_wrapper_functions(code: str) -> str:
    """Remove trivial wrapper functions and replace their callers with the target."""
    tree = ast.parse(code)
    wrappers: dict[str, str] = {}  # wrapper_name -> target_name

    # First pass: find all wrapper functions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_wrap, target = _is_wrapper(node)
            if is_wrap:
                wrappers[node.name] = target

    if not wrappers:
        return code

    # Second pass: remove wrapper definitions and rewrite callers
    lines = code.splitlines()
    lines_to_remove: set[int] = set()

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in wrappers:
                for i in range(node.lineno - 1, node.end_lineno):
                    lines_to_remove.add(i)

    # Third pass: replace wrapper calls with target calls
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in wrappers:
                line_idx = node.lineno - 1
                old_name = node.func.id
                new_name = wrappers[old_name]
                line = lines[line_idx]
                lines[line_idx] = line.replace(old_name, new_name, 1)

    result_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_remove:
            result_lines.append(line)
    return "\n".join(result_lines)


def strip_module_docstrings(code: str) -> str:
    """Remove standalone string expressions (module/section docstrings) except the file header."""
    tree = ast.parse(code)
    lines = code.splitlines()
    lines_to_remove: set[int] = set()

    for node in ast.iter_child_nodes(tree):
        # Remove standalone string literals (module docstrings, section headers)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for i in range(node.lineno - 1, node.end_lineno):
                lines_to_remove.add(i)

    if not lines_to_remove:
        return code

    result_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_remove:
            result_lines.append(line)
    return "\n".join(result_lines)


def minify_code(code: str) -> str:
    """Minify code using ast.unparse(). Preserves shebang and module docstring."""
    lines = code.splitlines()
    header_parts = []
    body_start = 0

    # Preserve shebang
    if lines and lines[0].startswith("#!"):
        header_parts.append(lines[0])
        body_start = 1

    # Parse AST
    tree = ast.parse(code)

    # Preserve module docstring
    doc = ast.get_docstring(tree)
    if doc:
        # Remove the docstring Expr node from AST so unparse won't include it
        if (tree.body and isinstance(tree.body[0], ast.Expr)
                and isinstance(tree.body[0].value, ast.Constant)
                and isinstance(tree.body[0].value.value, str)):
            tree.body.pop(0)
        header_parts.append(f'"""{doc}"""')

    # Unparse AST to minimal code
    minified = ast.unparse(tree)
    # ast.unparse joins statements with \n, ensure single newlines
    minified = "\n".join(line for line in minified.splitlines() if line.strip())

    result = "\n".join(header_parts) + "\n" + minified + "\n"
    return result


def post_process(code: str) -> str:
    """Apply AST-based optimizations to merged code."""
    # 1. Remove duplicate function/class definitions
    code = deduplicate_functions(code)
    # 2. Remove trivial wrapper functions and inline their calls
    code = remove_wrapper_functions(code)
    # 3. Clean up multiple blank lines
    code = re.sub(r"\n{3,}", "\n\n", code)
    # 4. Minify using ast.unparse()
    code = minify_code(code)
    return code


def get_version() -> str:
    """Generate version string from date (yy.mm.dd.hhmm)."""
    now = datetime.now()
    return f"{now.year % 100:02d}.{now.month:02d}.{now.day:02d}.{now.hour:02d}{now.minute:02d}"


def main():
    # Get version from argument or generate from date
    version = sys.argv[1] if len(sys.argv) > 1 else get_version()
    
    project_root = Path(__file__).parent.parent.parent
    src_dir = project_root / "src" / "app"
    output_file = project_root / "dist" / f"api-tree-{version}.py"

    # Read docstring from main.py for the header
    main_py = project_root / "src" / "main.py"
    main_doc = "Fetch OpenAPI route information and print as a tree structure in the terminal."
    if main_py.exists():
        try:
            tree = ast.parse(main_py.read_text(encoding="utf-8"))
            doc = ast.get_docstring(tree)
            if doc:
                main_doc = doc
        except Exception:
            pass

    header = f'''#!/usr/bin/env python3
"""
{main_doc}
"""

'''

    # Auto-discover and sort modules
    discovered = discover_modules(src_dir)
    modules = sort_modules(discovered)
    print(f"Discovered modules: {modules}")

    # Collect imports from all modules using ast
    all_imports: set[str] = set()
    module_codes = []

    for mod_name in modules:
        mod_path = src_dir / mod_name
        if not mod_path.exists():
            print(f"Warning: {mod_path} not found, skipping")
            continue

        all_imports |= extract_imports(mod_path)
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

    # Apply AST-based post-processing
    content = post_process(content)

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
