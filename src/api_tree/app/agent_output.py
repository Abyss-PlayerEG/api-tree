"""
Agent 优化输出格式,专供 LLM 消费
Agent-optimized output formats for LLM consumption.
"""

import json

from .tree import sort_children, TreeMatcher, TreeNode, EndpointDict
from .search import match_search


def generate_agent_output(
        node: TreeNode,
        title: str,
        total: int,
        format_type: str,
        search: str = ""
) -> str:
    """
    按指定格式生成 Agent 优化输出
    Generate agent-optimized output in specified format.
    """
    if format_type == "markdown":
        return _generate_markdown(node, title, total, search)
    elif format_type == "json":
        return _generate_json(node, title, total, search)
    elif format_type == "curl":
        return _generate_curl(node, title, total, search)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def _generate_markdown(
        node: TreeNode,
        title: str,
        total: int,
        search: str = ""
) -> str:
    """
    生成 Markdown 格式,按路径层级组织端点
    Generate clean Markdown format optimized for LLM consumption.
    """
    lines = []
    lines.append(f"# {title} API Endpoints")
    lines.append(f"Total: {total} endpoints")
    if search:
        lines.append(f"Filtered by: {search}")
    lines.append("")
    
    matcher = TreeMatcher(node, search) if search else None
    _walk_markdown(node, lines, "", "", matcher, search)
    
    return "\n".join(lines)


def _walk_markdown(
        node: TreeNode,
        lines: list[str],
        prefix: str,
        path_accum: str,
        matcher: TreeMatcher | None = None,
        search: str = ""
) -> None:
    """
    递归遍历树并生成 Markdown 行
    Recursively walk tree and generate Markdown lines.
    """
    children = sort_children(node)
    eps = node["endpoints"]
    
    # Apply search filter
    if search:
        if matcher:
            if not matcher.matches(node):
                return
            visible = matcher.visible_children(node)
        else:
            visible = [(cn, cn_node) for cn, cn_node in children
                       if _matches_search(cn_node, search)]
    else:
        visible = children
    
    # Filter endpoints if searching
    if search and eps:
        eps = [ep for ep in eps if (
                match_search(ep["path_lower"], search)
                or match_search(ep["summary_lower"], search)
                or match_search(ep["method_lower"], search)
        )]
    
    # Single child chain merge (only when no own endpoints)
    if prefix and len(visible) == 1 and not eps:
        merged = f"{path_accum}/{prefix}" if path_accum else prefix
        _walk_markdown(visible[0][1], lines, visible[0][0], merged, matcher, search)
        return
    
    # Current path
    current_path = f"{path_accum}/{prefix}" if path_accum else prefix
    if prefix:
        if eps:
            # This node has endpoints - show them
            lines.append(f"## /{current_path}")
            lines.append("")
            for ep in eps:
                method = ep["method"]
                path = ep["path"]
                summary = ep["summary"]
                lines.append(f"- **{method}** `{path}`")
                if summary:
                    lines.append(f"  {summary}")
            lines.append("")
        elif visible:
            # This is a directory node
            pass  # Don't output directory headers, just endpoints
    
    # Process children
    for child_name, child_node in visible:
        _walk_markdown(child_node, lines, child_name, current_path, matcher, search)


def _generate_json(
        node: TreeNode,
        title: str,
        total: int,
        search: str = ""
) -> str:
    """
    生成扁平化 JSON 格式,包含所有端点列表
    Generate structured JSON format for programmatic consumption.
    """
    matcher = TreeMatcher(node, search) if search else None
    
    result: dict[str, object] = {
        "title": title,
        "total_endpoints": total,
        "filtered_by": search if search else None,
        "endpoints": []
    }
    
    endpoints_list: list[dict[str, object]] = []
    _collect_endpoints(node, endpoints_list, "", "", matcher, search)
    result["endpoints"] = endpoints_list
    
    return json.dumps(result, indent=2, ensure_ascii=False)


def _collect_endpoints(
        node: TreeNode,
        endpoints: list[dict[str, object]],
        prefix: str,
        path_accum: str,
        matcher: TreeMatcher | None = None,
        search: str = ""
) -> None:
    """
    递归收集所有端点到扁平列表
    Recursively collect all endpoints into flat list.
    """
    children = sort_children(node)
    eps = node["endpoints"]
    
    # Apply search filter
    if search:
        if matcher:
            if not matcher.matches(node):
                return
            visible = matcher.visible_children(node)
        else:
            visible = [(cn, cn_node) for cn, cn_node in children
                       if _matches_search(cn_node, search)]
    else:
        visible = children
    
    # Filter endpoints if searching
    if search and eps:
        eps = [ep for ep in eps if (
                match_search(ep["path_lower"], search)
                or match_search(ep["summary_lower"], search)
                or match_search(ep["method_lower"], search)
        )]
    
    # Single child chain merge (only when no own endpoints)
    if prefix and len(visible) == 1 and not eps:
        merged = f"{path_accum}/{prefix}" if path_accum else prefix
        _collect_endpoints(visible[0][1], endpoints, visible[0][0], merged, matcher, search)
        return
    
    # Current path
    current_path = f"{path_accum}/{prefix}" if path_accum else prefix
    
    # Add endpoints
    for ep in eps:
        endpoint_data: dict[str, object] = {
            "method": ep["method"],
            "path": ep["path"],
            "summary": ep["summary"],
            "path_prefix": f"/{current_path}" if current_path else "/"
        }
        endpoints.append(endpoint_data)
    
    # Process children
    for child_name, child_node in visible:
        _collect_endpoints(child_node, endpoints, child_name, current_path, matcher, search)


def _generate_curl(
        node: TreeNode,
        title: str,
        total: int,
        search: str = ""
) -> str:
    """
    生成 CURL 命令模板,包含认证头和示例请求体
    Generate CURL request templates for each endpoint.
    """
    matcher = TreeMatcher(node, search) if search else None
    
    lines = []
    lines.append(f"# CURL templates for {title} API")
    lines.append(f"# Total: {total} endpoints")
    if search:
        lines.append(f"# Filtered by: {search}")
    lines.append("")
    lines.append("# Replace BASE_URL with your actual server address")
    lines.append("# Replace AUTH_TOKEN with your actual authentication token")
    lines.append("")
    
    _collect_curl_templates(node, lines, "", "", matcher, search)
    
    return "\n".join(lines)


def _collect_curl_templates(
        node: TreeNode,
        lines: list[str],
        prefix: str,
        path_accum: str,
        matcher: TreeMatcher | None = None,
        search: str = ""
) -> None:
    """
    递归收集所有端点的 CURL 模板
    Recursively collect CURL templates for all endpoints.
    """
    children = sort_children(node)
    eps = node["endpoints"]
    
    # Apply search filter
    if search:
        if matcher:
            if not matcher.matches(node):
                return
            visible = matcher.visible_children(node)
        else:
            visible = [(cn, cn_node) for cn, cn_node in children
                       if _matches_search(cn_node, search)]
    else:
        visible = children
    
    # Filter endpoints if searching
    if search and eps:
        eps = [ep for ep in eps if (
                match_search(ep["path_lower"], search)
                or match_search(ep["summary_lower"], search)
                or match_search(ep["method_lower"], search)
        )]
    
    # Single child chain merge (only when no own endpoints)
    if prefix and len(visible) == 1 and not eps:
        merged = f"{path_accum}/{prefix}" if path_accum else prefix
        _collect_curl_templates(visible[0][1], lines, visible[0][0], merged, matcher, search)
        return
    
    # Current path
    current_path = f"{path_accum}/{prefix}" if path_accum else prefix
    
    # Generate CURL templates
    for ep in eps:
        method = ep["method"]
        path = ep["path"]
        summary = ep["summary"]
        
        lines.append(f"# {summary}" if summary else f"# {method} {path}")
        lines.append(f"curl -X {method} \\")
        lines.append(f"  'BASE_URL{path}' \\")
        lines.append(f"  -H 'Authorization: Bearer AUTH_TOKEN' \\")
        lines.append(f"  -H 'Content-Type: application/json'")
        
        # Add example request body for POST/PUT/PATCH
        if method in ("POST", "PUT", "PATCH"):
            lines.append(f"  -d '{{}}'")
        
        lines.append("")
    
    # Process children
    for child_name, child_node in visible:
        _collect_curl_templates(child_node, lines, child_name, current_path, matcher, search)


def _matches_search(
        node: TreeNode,
        search: str
) -> bool:
    """
    检查节点或其子树是否匹配搜索关键词(无缓存)
    Check if node or its subtree matches search keyword (no cache).
    """
    for ep in node["endpoints"]:
        if (match_search(ep["path_lower"], search)
                or match_search(ep["summary_lower"], search)
                or match_search(ep["method_lower"], search)):
            return True
    for child in node["children"].values():
        if _matches_search(child, search):
            return True
    return False
