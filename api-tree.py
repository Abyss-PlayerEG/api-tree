#!/usr/bin/env python3
"""
Fetch OpenAPI route information and print as a tree structure in the terminal.

Usage:
    <python-tool-command>                          # Default: localhost:8080
    <python-tool-command> http://localhost:9090    # Specify server address
    <python-tool-command> /path/to/openapi.json    # Read from local JSON file
    <python-tool-command> -s auth                  # Search paths containing "auth"
    <python-tool-command> -h                       # Show help
"""

import json
import sys
import urllib.request
import urllib.error
import os
from urllib.parse import urlparse
from collections import defaultdict


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
                "summary": summary,
                "path": path,
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
               search: str = "", name: str = "", path_accum: str = ""):
    children = sort_children(node)
    eps = node["endpoints"]

    # 搜索过滤
    if search and not _matches(node, search):
        return

    # 单子节点、无接口 -> 合并路径，跳过当前层级
    if name and not eps and len(children) == 1:
        child_name, child_node = children[0]
        merged = f"{path_accum}/{name}" if path_accum else name
        print_tree(child_node, prefix, is_last, search, child_name, merged)
        return

    # 拼接最终显示的路径名
    display_name = f"{path_accum}/{name}" if path_accum else name

    branch = "" if name == "" else ("└── " if is_last else "├── ")

    if name:
        line = f"{Color.DIM}{prefix}{Color.RESET}"
        line += f"{Color.DIM}{branch}{Color.RESET}"

        if not children and eps:
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
        elif children:
            # 目录节点
            line += f"/{display_name}"
            if eps:
                line += f"  {Color.DIM}({len(eps)} endpoints){Color.RESET}"
        print(line)

    # 子节点
    child_prefix = "" if name == "" else prefix + ("    " if is_last else "│   ")
    for i, (child_name, child_node) in enumerate(children):
        child_is_last = (i == len(children) - 1)
        print_tree(child_node, child_prefix, child_is_last, search, child_name, "")


def _matches(node: dict, keyword: str) -> bool:
    """检查节点或其子树是否包含关键词"""
    for ep in node["endpoints"]:
        if (keyword in ep["path"].lower()
                or keyword in ep["summary"].lower()
                or keyword in ep["method"].lower()):
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


def main():
    search = ""
    source = "http://localhost:8080"

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "-s" and i + 1 < len(args):
            search = args[i + 1].lower()
            i += 2
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


if __name__ == "__main__":
    main()