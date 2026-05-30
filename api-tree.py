#!/usr/bin/env python3
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

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


def fetch_openapi(source: str) -> dict:
    """从 URL 或本地文件获取 OpenAPI JSON"""
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8") as f:
            return json.load(f)

    # 判断是否为完整 URL：如果已含具体路径（如 /v3/api-docs、.json 等）则直接用
    parsed = urlparse(source)
    if parsed.path and parsed.path.rstrip("/") not in ("", "/"):
        url = source
    else:
        url = source.rstrip("/") + "/v3/api-docs"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Error: Cannot connect to {url}\n  {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: {url} returned invalid JSON", file=sys.stderr)
        sys.exit(1)


def build_tree(paths: dict) -> dict:
    """将 OpenAPI paths 构建为层级树"""
    root = {"children": {}, "endpoints": []}

    for path, methods in paths.items():
        segments = [s for s in path.split("/") if s]
        node = root
        for seg in segments:
            if seg not in node["children"]:
                node["children"][seg] = {"children": {}, "endpoints": []}
            node = node["children"][seg]

        for method, detail in methods.items():
            if not isinstance(detail, dict):
                continue
            summary = (detail.get("summary") or "").replace("\n", " ")
            node["endpoints"].append({
                "method": method.upper(),
                "method_lower": method.lower(),
                "summary": summary,
                "summary_lower": summary.lower(),
                "path": path,
                "path_lower": path.lower(),
            })

    return root


def sort_children(node: dict) -> list:
    """排序子节点：有子节点的（目录）在前，叶子在后，同类按字母排序"""
    items = list(node["children"].items())
    items.sort(key=lambda x: (
        0 if x[1]["children"] else 1,  # 目录优先
        x[0].lower(),
    ))
    return items


# 终端颜色 (ANSI)
class Color:
    RESET  = "\033[0m"
    DIM    = "\033[2m"
    BLUE   = "\033[34m"
    GREEN  = "\033[32m"
    YELLOW = "\033[33m"
    RED    = "\033[31m"
    MAGENTA= "\033[35m"
    CYAN   = "\033[36m"
    BOLD   = "\033[1m"

    @staticmethod
    def method(m: str) -> str:
        return {
            "GET":    Color.GREEN,
            "POST":   Color.BLUE,
            "PUT":    Color.YELLOW,
            "DELETE": Color.RED,
            "PATCH":  Color.MAGENTA,
        }.get(m, Color.RESET)


def print_tree(node: dict, prefix: str = "", is_last: bool = True,
               search: str = "", name: str = "", path_accum: str = "",
               extra_eps: list = None):
    children = sort_children(node)
    eps = node["endpoints"]
    if extra_eps:
        eps = extra_eps + eps

    # 搜索过滤（含累积祖先接口）
    if search:
        matched = _matches(node, search)
        if not matched and extra_eps:
            matched = any(
                search in ep["path_lower"]
                or search in ep["summary_lower"]
                or search in ep["method_lower"]
                for ep in extra_eps
            )
        if not matched:
            return

    # 预过滤搜索模式下的可见子节点
    if search:
        visible = [(cn, cn_node) for cn, cn_node in children if _matches(cn_node, search)]
    else:
        visible = children

    # 单子节点（可见） -> 链式合并路径和接口，递归处理
    if name and len(visible) == 1:
        merged = f"{path_accum}/{name}" if path_accum else name
        print_tree(visible[0][1], prefix, is_last, search, visible[0][0], merged, eps)
        return

    # 搜索模式下只显示匹配的接口
    if search and eps:
        eps = [ep for ep in eps if (
            search in ep["path_lower"]
            or search in ep["summary_lower"]
            or search in ep["method_lower"]
        )]

    # 拼接最终显示的路径名
    display_name = f"{path_accum}/{name}" if path_accum else name

    branch = "" if name == "" else ("└── " if is_last else "├── ")

    if name:
        line = f"{Color.DIM}{prefix}{Color.RESET}"
        line += f"{Color.DIM}{branch}{Color.RESET}"

        if not visible and eps:
            # 叶子节点（有接口）
            line += f"{Color.CYAN}{Color.BOLD}/{display_name}{Color.RESET}"
            first = True
            for ep in eps:
                mc = Color.method(ep["method"])
                if not first:
                    line += " "
                line += f" {mc}{ep['method']:<6}{Color.RESET}"
                if ep["summary"]:
                    line += f" {Color.DIM}{ep['summary']}{Color.RESET}"
                first = False
        elif visible:
            # 目录节点
            line += f"/{display_name}"
            if eps:
                line += f"  {Color.DIM}({len(eps)} endpoints){Color.RESET}"
        print(line)

    # 子节点
    child_prefix = "" if name == "" else prefix + ("    " if is_last else "│   ")
    for i, (child_name, child_node) in enumerate(visible):
        child_is_last = (i == len(visible) - 1)
        print_tree(child_node, child_prefix, child_is_last, search, child_name, "")


def _matches(node: dict, keyword: str) -> bool:
    """检查节点或其子树是否包含关键词（预计算小写值，避免重复调用 .lower()）"""
    for ep in node["endpoints"]:
        if (keyword in ep["path_lower"]
                or keyword in ep["summary_lower"]
                or keyword in ep["method_lower"]):
            return True
    for child in node["children"].values():
        if _matches(child, keyword):
            return True
    return False


def count_endpoints(node: dict) -> int:
    """递归统计接口总数"""
    total = len(node["endpoints"])
    for child in node["children"].values():
        total += count_endpoints(child)
    return total


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_html_tree(node: dict, title: str, total: int, search: str = "") -> str:
    """Render API tree as an HTML file. Returns the output file path."""
    METHOD_CLASS = {
        "GET": "method-get", "POST": "method-post", "PUT": "method-put",
        "DELETE": "method-delete", "PATCH": "method-patch",
    }

    lines = []

    def walk(n, prefix, is_last, path_acc, name, extra_eps=None):
        children = sort_children(n)
        eps = n["endpoints"]
        if extra_eps:
            eps = extra_eps + eps

        if search:
            matched = _matches(n, search)
            if not matched and extra_eps:
                matched = any(
                    search in ep["path_lower"]
                    or search in ep["summary_lower"]
                    or search in ep["method_lower"]
                    for ep in extra_eps
                )
            if not matched:
                return

        if search:
            visible = [(cn, cn_node) for cn, cn_node in children if _matches(cn_node, search)]
        else:
            visible = children

        if name and len(visible) == 1:
            merged = f"{path_acc}/{name}" if path_acc else name
            walk(visible[0][1], prefix, is_last, merged, visible[0][0], eps)
            return

        if search and eps:
            eps = [ep for ep in eps if (
                search in ep["path_lower"]
                or search in ep["summary_lower"]
                or search in ep["method_lower"]
            )]

        display = f"{path_acc}/{name}" if path_acc else name

        if name:
            branch = "└── " if is_last else "├── "
            line = f'<span class="dim">{_escape(prefix)}{branch}</span>'

            if not visible and eps:
                line += f'<span class="leaf">/{_escape(display)}</span>'
                first = True
                for ep in eps:
                    mc = METHOD_CLASS.get(ep["method"], "")
                    if not first:
                        line += " "
                    method_text = f"{ep['method']:<6}"
                    line += f' <span class="method {mc}">{_escape(method_text)}</span>'
                    if ep["summary"]:
                        line += f' <span class="dim">{_escape(ep["summary"])}</span>'
                    first = False
            elif visible:
                line += f'<span class="dir">/{_escape(display)}</span>'
                if eps:
                    line += f' <span class="dim">({len(eps)} endpoints)</span>'

            lines.append(line)

        child_prefix = "" if name == "" else prefix + ("    " if is_last else "│   ")
        for i, (cn, cnode) in enumerate(visible):
            child_last = (i == len(visible) - 1)
            walk(cnode, child_prefix, child_last, "", cn)

    walk(node, "", True, "", "")

    css = (
        ":root{"
        "--base:#24273a;--mantle:#1e2030;--crust:#181926;"
        "--text:#cad3f5;--subtext1:#b8c0e0;--subtext0:#a5adcb;"
        "--overlay0:#6e738d;--surface0:#363a4f;--surface1:#494d64;"
        "--green:#a6da95;--blue:#8aadf4;--yellow:#eed49f;"
        "--red:#ed8796;--mauve:#c6a0f6;--teal:#8bd5ca"
        "}"
        "[data-theme=latte]{"
        "--base:#eff1f5;--mantle:#e6e9ef;--crust:#dce0e8;"
        "--text:#4c4f69;--subtext1:#5c5f77;--subtext0:#6c6f85;"
        "--overlay0:#9ca0b0;--surface0:#ccd0da;--surface1:#bcc0cc;"
        "--green:#40a02b;--blue:#1e66f5;--yellow:#df8e1d;"
        "--red:#d20f39;--mauve:#8839ef;--teal:#179299"
        "}"
        "*{margin:0;padding:0;box-sizing:border-box}"
        "body{background:var(--base);color:var(--text);"
        "font-family:'Cascadia Code','Fira Code',Consolas,Monaco,monospace;"
        "padding:32px 40px;min-height:100vh;transition:background .2s,color .2s}"
        "h1{font-size:20px;font-weight:600;color:var(--text);margin-bottom:4px}"
        ".subtitle{color:var(--subtext0);font-weight:400;font-size:16px}"
        ".total{font-size:13px;color:var(--overlay0);margin-bottom:28px}"
        ".tree{font-size:14px;line-height:1.75;"
        "font-family:'Cascadia Code','Fira Code',Consolas,Monaco,monospace;"
        "color:var(--text)}"
        ".dim{color:var(--overlay0)}"
        ".leaf{color:var(--teal);font-weight:700}"
        ".dir{color:var(--text)}"
        ".method{font-weight:700}"
        ".method-get{color:var(--green)}"
        ".method-post{color:var(--blue)}"
        ".method-put{color:var(--yellow)}"
        ".method-delete{color:var(--red)}"
        ".method-patch{color:var(--mauve)}"
        ".theme-btn{"
        "position:fixed;top:20px;right:20px;"
        "background:var(--surface0);color:var(--text);"
        "border:1px solid var(--surface1);border-radius:8px;"
        "padding:6px 14px;cursor:pointer;font-size:13px;"
        "font-family:inherit;transition:background .2s;z-index:10"
        "}"
        ".theme-btn:hover{background:var(--surface1)}"
    )

    html = (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
        f'<title>{_escape(title)} - API Tree</title>\n'
        f'<style>{css}</style>\n'
        '</head>\n<body>\n'
        '<button id="theme-btn" class="theme-btn" '
        'title="Toggle light/dark theme">🌙 Dark</button>\n'
        f'<h1>{_escape(title)} <span class="subtitle">API Endpoint Tree</span></h1>\n'
        f'<p class="total">{total} endpoints</p>\n'
        '<pre class="tree">\n'
        + '\n'.join(lines) +
        '\n</pre>\n'
        '<script>\n'
        '(function(){\n'
        'var h=document.documentElement,b=document.getElementById("theme-btn");\n'
        'var t=localStorage.getItem("api-tree-theme")||"macchiato";\n'
        'if(t==="latte")h.setAttribute("data-theme","latte");\n'
        'b.textContent=t==="latte"?"☀️ Light":"🌙 Dark";\n'
        'b.onclick=function(){\n'
        'var c=h.getAttribute("data-theme")==="latte"?"macchiato":"latte";\n'
        'if(c==="latte")h.setAttribute("data-theme","latte");'
        'else h.removeAttribute("data-theme");\n'
        'localStorage.setItem("api-tree-theme",c);\n'
        'b.textContent=c==="latte"?"☀️ Light":"🌙 Dark";\n'
        '};\n'
        '})();\n'
        '</script>\n'
        '</body>\n</html>'
    )

    home = Path.home() / "Downloads"
    home.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c for c in title if c.isalnum() or c in " _-")[:50].strip().replace(" ", "_")
    fname = f"api-tree_{safe}_{ts}.html" if safe else f"api-tree_{ts}.html"
    out = home / fname
    out.write_text(html, encoding="utf-8")
    return str(out)


def main():
    search = ""
    output_html = False
    source = "http://localhost:8080"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "-s" and i + 1 < len(args):
            search = args[i + 1].lower()
            i += 2
        elif args[i] == "--html":
            output_html = True
            i += 1
        elif args[i] == "-h" or args[i] == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            source = args[i]
            i += 1

    spec = fetch_openapi(source)
    paths = spec.get("paths", {})

    if not paths:
        print("No API paths found", file=sys.stderr)
        sys.exit(1)

    tree = build_tree(paths)
    total = count_endpoints(tree)

    if search:
        print(f"\nMatched - \"{search}\"")
    else:
        title = spec.get("info", {}).get("title", "API")
        print(f"\n{Color.BOLD}{title} API Endpoint Tree{Color.RESET}  ({total} endpoints)")

    print_tree(tree, search=search)
    print()
    if not search:
        print(f"{Color.DIM}Total: {total} endpoints{Color.RESET}")

    if output_html:
        img_title = spec.get("info", {}).get("title", "API")
        output_path = render_html_tree(tree, img_title, total, search)
        print(f"{Color.DIM}HTML saved to: {output_path}{Color.RESET}")


if __name__ == "__main__":
    main()