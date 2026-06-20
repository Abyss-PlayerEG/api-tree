"""
终端控制台输出
Console output for API tree.
"""

from .color import Color
from .tree import sort_children, TreeMatcher, _matches, _leaf_name, _leaf_name_no_search, TreeNode, EndpointDict
from .search import match_search


def print_tree(
        node: TreeNode,
        prefix: str = "",
        is_last: bool = True,
        search: str = "",
        name: str = "",
        path_accum: str = "",
        extra_eps: list[EndpointDict] | None = None,
        name_pad: int = 0,
        matcher: TreeMatcher | None = None
) -> None:
    """
    递归打印 API 树状图到终端
    Print API tree to terminal with colors.
    """
    children = sort_children(node)
    eps = node["endpoints"]
    if extra_eps:
        eps = extra_eps + eps
    
    # 搜索过滤
    # Search filter
    if search:
        matched = (matcher.matches(node) if matcher else _matches(node, search))
        if not matched and extra_eps:
            matched = any(
                match_search(ep["path_lower"], search)
                or match_search(ep["summary_lower"], search)
                or match_search(ep["method_lower"], search)
                for ep in extra_eps
            )
        if not matched:
            return
    
    # 搜索模式下预过滤可见子节点
    # Pre-filter visible children in search mode
    if search:
        visible = (matcher.visible_children(node) if matcher
                   else [(cn, cn_node) for cn, cn_node in children if _matches(cn_node, search)])
    else:
        visible = children
    
    # 计算最大叶子路径宽度
    # Calculate max leaf path width
    if search and matcher:
        child_pad = matcher.max_leaf_width(node) if visible else 0
    else:
        child_pad = 0
        if visible:
            for cn, cn_node in visible:
                leaf = _leaf_name(cn_node, cn, search) if search else _leaf_name_no_search(cn_node, cn)
                if leaf:
                    child_pad = max(child_pad, len(f"/{leaf}"))
    
    # 单子节点链合并（仅当没有自身端点时）
    # Single child chain merge (only when no own endpoints)
    if name and len(visible) == 1 and not eps:
        merged = f"{path_accum}/{name}" if path_accum else name
        print_tree(visible[0][1], prefix, is_last, search, visible[0][0], merged, eps,
                   name_pad=name_pad or child_pad, matcher=matcher)
        return
    
    # 搜索模式：仅显示匹配的端点
    # Search mode: only show matching endpoints
    if search and eps:
        eps = [ep for ep in eps if (
                match_search(ep["path_lower"], search)
                or match_search(ep["summary_lower"], search)
                or match_search(ep["method_lower"], search)
        )]
    
    display_name = f"{path_accum}/{name}" if path_accum else name
    branch = "" if name == "" else ("\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 ")
    
    if name:
        line = f"{Color.DIM}{prefix}{Color.RESET}"
        line += f"{Color.DIM}{branch}{Color.RESET}"
        
        if eps:
            full_path = f"/{display_name}"
            if name_pad:
                full_path = full_path.ljust(name_pad)
            line += f"{Color.CYAN}{Color.BOLD}{full_path}{Color.RESET}"
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
            line += f"/{display_name}"
        print(line)
    
    child_prefix = "" if name == "" else prefix + ("    " if is_last else "\u2502   ")
    for i, (child_name, child_node) in enumerate(visible):
        child_is_last = (i == len(visible) - 1)
        print_tree(child_node, child_prefix, child_is_last, search, child_name, "",
                   name_pad=child_pad, matcher=matcher)
