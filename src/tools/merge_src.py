#!/usr/bin/env python3
"""
单文件构建工具
Merge src/ package modules into a single main.py file.
"""

import ast
import re
import sys
from datetime import datetime
from pathlib import Path

# 必须优先加载的模块(依赖关系)
PRIORITY_MODULES = ["color.py", "_version.py", "config.py", "args.py"]
# 必须最后加载的模块(程序入口)
ENTRY_MODULE = "cli.py"


def discover_modules(src_dir: Path) -> list[str]:
    """
    自动发现 src/app/ 目录下所有 .py 模块
    Auto-discover all .py modules in src/app/ directory.
    """
    modules = []
    for f in sorted(src_dir.glob("*.py")):
        if f.name in ("__init__.py", "__main__.py"):
            continue
        modules.append(f.name)
    return modules


def sort_modules(modules: list[str]) -> list[str]:
    """
    按优先级排序:依赖模块在前 → 普通模块 → 入口模块在最后
    Sort modules: priority first, entry last, rest in middle.
    """
    priority = [m for m in PRIORITY_MODULES if m in modules]
    entry = [m for m in [ENTRY_MODULE] if m in modules]
    rest = [m for m in modules if m not in priority and m not in entry]
    return priority + rest + entry


def extract_imports(filepath: Path) -> set[str]:
    """
    用 AST 提取文件中的所有导入语句(跳过相对导入和 src 内部导入)
    Use ast to extract all import statements from a file.
    """
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
    """
    提取模块代码,仅删除模块级导入,保留函数内 import
    Extract module code using AST to remove only module-level imports.
    """
    code = filepath.read_text(encoding="utf-8")
    
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code.strip() + "\n"
    
    # Find module-level import lines to remove
    lines_to_remove: set[int] = set()
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            assert node.end_lineno is not None
            for i in range(node.lineno - 1, node.end_lineno):
                lines_to_remove.add(i)
        elif isinstance(node, ast.ImportFrom):
            # Keep only absolute, non-src imports (same logic as extract_imports)
            if node.level > 0 or (node.module or "").startswith("src"):
                assert node.end_lineno is not None
                for i in range(node.lineno - 1, node.end_lineno):
                    lines_to_remove.add(i)
    
    if not lines_to_remove:
        return code.strip() + "\n"
    
    lines = code.splitlines()
    result = [line for i, line in enumerate(lines) if i not in lines_to_remove]
    code = "\n".join(result)
    
    # Clean up multiple blank lines
    code = re.sub(r"\n{3,}", "\n\n", code)
    return code.strip() + "\n"


def _is_wrapper(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[bool, str]:
    """
    检测函数是否为简单包装器(仅调用另一个函数)
    Check if a function is a trivial wrapper (just calls another function).
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
    """
    检查函数体是否仅为 pass
    Check if function body is just `pass`.
    """
    return len(node.body) == 1 and isinstance(node.body[0], ast.Pass)


def deduplicate_functions(code: str) -> str:
    """
    删除重复的函数/类定义,保留第一次出现
    Remove duplicate function/class definitions, keeping the first occurrence.
    """
    tree = ast.parse(code)
    seen: set[str] = set()
    lines_to_remove: set[int] = set()
    
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in seen:
                # Remove this duplicate definition
                assert node.end_lineno is not None
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
    """
    删除简单包装函数,并将其调用替换为直接调用目标函数
    Remove trivial wrapper functions and replace their callers with the target.
    """
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
                assert node.end_lineno is not None
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
    """
    删除模块文档字符串(仅保留文件头部的)
    Remove standalone string expressions (module/section docstrings) except the file header.
    """
    tree = ast.parse(code)
    lines = code.splitlines()
    lines_to_remove: set[int] = set()
    
    for node in ast.iter_child_nodes(tree):
        # Remove standalone string literals (module docstrings, section headers)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            assert node.end_lineno is not None
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
    """
    压缩代码:保留 shebang,模块文档字符串和 # type: ignore 注释
    Minify code while preserving # type: ignore comments.
    """
    lines = code.splitlines()
    header_parts: list[str] = []
    body_start = 0
    
    # Preserve shebang
    if lines and lines[0].startswith("#!"):
        header_parts.append(lines[0])
        body_start = 1
    
    # Parse AST to locate module docstring
    tree = ast.parse(code)
    doc = ast.get_docstring(tree)
    doc_lines_to_remove: set[int] = set()
    if doc and tree.body and isinstance(tree.body[0], ast.Expr) \
            and isinstance(tree.body[0].value, ast.Constant) \
            and isinstance(tree.body[0].value.value, str):
        doc_node = tree.body[0]
        assert doc_node.end_lineno is not None
        for i in range(doc_node.lineno - 1, doc_node.end_lineno):
            doc_lines_to_remove.add(i)
        header_parts.append(f'"""{doc}"""')
    
    # Line-by-line: strip blanks, docstring, pure comments (keep type: ignore)
    result_body: list[str] = []
    for i, line in enumerate(lines):
        if i < body_start:
            continue
        if i in doc_lines_to_remove:
            continue
        
        stripped = line.strip()
        
        # Skip blank lines
        if not stripped:
            continue
        
        # Keep # type: ignore comments (inline or standalone)
        if stripped.startswith("#"):
            if "type:" in stripped:
                result_body.append(line)
            # Skip other pure comment lines
            continue
        
        result_body.append(line)
    
    result = "\n".join(header_parts) + "\n" + "\n".join(result_body) + "\n"
    return result


def post_process(code: str) -> str:
    """
    对合并后的代码应用 AST 优化:去重 → 内联包装器 → 清理空行 → 压缩
    Apply AST-based optimizations to merged code.
    """
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
    """
    根据当前日期生成版本号(格式 yy.mm.dd.hhmm)
    Generate version string from date (yy.mm.dd.hhmm).
    """
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
