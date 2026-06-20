"""
RAG 优化输出,供向量数据库知识库使用
RAG-optimized output for vector database knowledge base.
"""

import json

from .tree import sort_children, TreeMatcher, TreeNode, EndpointDict
from .search import match_search


def generate_rag_output(
        node: TreeNode,
        title: str,
        total: int,
        format_type: str,
        chunk_size: int = 10,
        search: str = ""
) -> str:
    """
    按指定格式生成 RAG 优化输出
    Generate RAG-optimized output in specified format.
    """
    if format_type == "jsonl":
        return _generate_jsonl(node, title, chunk_size, search)
    elif format_type == "json":
        return _generate_json_chunks(node, title, total, chunk_size, search)
    else:
        raise ValueError(f"Unsupported RAG format: {format_type}")


def _generate_jsonl(
        node: TreeNode,
        title: str,
        chunk_size: int,
        search: str = ""
) -> str:
    """
    生成 JSONL 格式:每行一个 JSON 块,适合逐行导入向量库
    Generate JSON Lines format for RAG knowledge base.
    """
    matcher = TreeMatcher(node, search) if search else None
    
    # Collect all endpoints with their path context
    endpoints: list[dict[str, object]] = []
    _collect_endpoints_with_context(node, endpoints, "", "", matcher, search)
    
    # Group endpoints by path prefix
    grouped = _group_by_prefix(endpoints)
    
    # Create chunks
    chunks: list[dict[str, object]] = []
    current_chunk: list[dict[str, object]] = []
    current_prefix = ""
    
    for prefix, eps in grouped.items():
        if not current_prefix:
            current_prefix = prefix
        
        # If adding this group would exceed chunk size, finalize current chunk
        if current_chunk and len(current_chunk) + len(eps) > chunk_size:
            chunks.append(_create_chunk(title, current_prefix, current_chunk))
            current_chunk = []
            current_prefix = prefix
        
        current_chunk.extend(eps)
        
        # If current chunk is exactly at size, finalize it
        if len(current_chunk) >= chunk_size:
            chunks.append(_create_chunk(title, current_prefix, current_chunk))
            current_chunk = []
            current_prefix = ""
    
    # Add remaining endpoints
    if current_chunk:
        chunks.append(_create_chunk(title, current_prefix, current_chunk))
    
    # Output as JSON Lines
    lines: list[str] = []
    for chunk in chunks:
        lines.append(json.dumps(chunk, ensure_ascii=False))
    
    return "\n".join(lines)


def _generate_json_chunks(
        node: TreeNode,
        title: str,
        total: int,
        chunk_size: int,
        search: str = ""
) -> str:
    """
    生成 JSON 格式:包含 chunks 数组的完整 JSON 文档
    Generate JSON format with array of chunks.
    """
    matcher = TreeMatcher(node, search) if search else None
    
    # Collect all endpoints with their path context
    endpoints: list[dict[str, object]] = []
    _collect_endpoints_with_context(node, endpoints, "", "", matcher, search)
    
    # Group endpoints by path prefix
    grouped = _group_by_prefix(endpoints)
    
    # Create chunks
    chunks: list[dict[str, object]] = []
    current_chunk: list[dict[str, object]] = []
    current_prefix = ""
    
    for prefix, eps in grouped.items():
        if not current_prefix:
            current_prefix = prefix
        
        # If adding this group would exceed chunk size, finalize current chunk
        if current_chunk and len(current_chunk) + len(eps) > chunk_size:
            chunks.append(_create_chunk(title, current_prefix, current_chunk))
            current_chunk = []
            current_prefix = prefix
        
        current_chunk.extend(eps)
        
        # If current chunk is exactly at size, finalize it
        if len(current_chunk) >= chunk_size:
            chunks.append(_create_chunk(title, current_prefix, current_chunk))
            current_chunk = []
            current_prefix = ""
    
    # Add remaining endpoints
    if current_chunk:
        chunks.append(_create_chunk(title, current_prefix, current_chunk))
    
    # Output as JSON
    result = {
        "title": title,
        "total_endpoints": total,
        "chunk_size": chunk_size,
        "filtered_by": search if search else None,
        "chunks": chunks
    }
    
    return json.dumps(result, indent=2, ensure_ascii=False)


def _collect_endpoints_with_context(
        node: TreeNode,
        endpoints: list[dict[str, object]],
        prefix: str,
        path_accum: str,
        matcher: TreeMatcher | None = None,
        search: str = ""
) -> None:
    """
    递归收集端点及其路径上下文
    Recursively collect endpoints with their path context.
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
        _collect_endpoints_with_context(visible[0][1], endpoints, visible[0][0], merged, matcher, search)
        return
    
    # Current path
    current_path = f"{path_accum}/{prefix}" if path_accum else prefix
    
    # Add endpoints with context
    for ep in eps:
        endpoint_data: dict[str, object] = {
            "method": ep["method"],
            "path": ep["path"],
            "summary": ep["summary"],
            "path_prefix": f"/{current_path}" if current_path else "/",
            "context": {
                "parent_path": f"/{path_accum}" if path_accum else "/",
                "current_segment": prefix,
                "full_path": f"/{current_path}" if current_path else "/"
            }
        }
        endpoints.append(endpoint_data)
    
    # Process children
    for child_name, child_node in visible:
        _collect_endpoints_with_context(child_node, endpoints, child_name, current_path, matcher, search)


def _group_by_prefix(endpoints: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    """
    按路径前缀分组端点,保持上下文连贯性
    Group endpoints by their path prefix for better context.
    """
    groups: dict[str, list[dict[str, object]]] = {}
    
    for ep in endpoints:
        prefix = str(ep["path_prefix"])
        if prefix not in groups:
            groups[prefix] = []
        groups[prefix].append(ep)
    
    return groups


def _create_chunk(title: str, prefix: str, endpoints: list[dict[str, object]]) -> dict[str, object]:
    """
    创建一个 RAG 块,包含元数据和可搜索文本
    Create a RAG chunk with metadata.
    """
    # Create a descriptive title for the chunk
    if prefix == "/":
        chunk_title = f"{title} - Root endpoints"
    else:
        chunk_title = f"{title} - {prefix} endpoints"
    
    # Create searchable text content
    text_parts = [chunk_title]
    text_parts.append(f"Path prefix: {prefix}")
    text_parts.append(f"Number of endpoints: {len(endpoints)}")
    text_parts.append("")
    
    for ep in endpoints:
        text_parts.append(f"{ep['method']} {ep['path']}")
        if ep["summary"]:
            text_parts.append(f"  Description: {ep['summary']}")
    
    chunk: dict[str, object] = {
        "chunk_id": f"{prefix}_{len(endpoints)}",
        "title": chunk_title,
        "path_prefix": prefix,
        "endpoint_count": len(endpoints),
        "endpoints": endpoints,
        "text": "\n".join(text_parts),  # Main text for vectorization
        "metadata": {
            "api_title": title,
            "chunk_type": "api_endpoints",
            "has_summary": any(ep["summary"] for ep in endpoints)
        }
    }
    
    return chunk


def _matches_search(node: TreeNode, search: str) -> bool:
    """
    检查节点或其子树是否匹配搜索关键词(无缓存)
    Check if node or its subtree matches search keyword.
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
