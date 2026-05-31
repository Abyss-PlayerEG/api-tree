"""Tree structure building and traversal utilities."""


def build_tree(paths: dict) -> dict:
    """Build hierarchical tree from OpenAPI paths."""
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
    """Sort children: directories first, then leaves, alphabetically within each group."""
    items = list(node["children"].items())
    items.sort(key=lambda x: (
        0 if x[1]["children"] else 1,  # directories first
        x[0].lower(),
    ))
    return items


def _matches(node: dict, keyword: str) -> bool:
    """Check if node or its subtree contains keyword."""
    for ep in node["endpoints"]:
        if (keyword in ep["path_lower"]
                or keyword in ep["summary_lower"]
                or keyword in ep["method_lower"]):
            return True
    for child in node["children"].values():
        if _matches(child, keyword):
            return True
    return False


def _leaf_name(node: dict, name: str, search: str = "") -> str | None:
    """Trace chain merges to find a leaf node's final display name.
    Returns e.g. 'users/{userId}/orders' or None if node is a directory."""
    children = sort_children(node)
    if search:
        visible = [(cn, cn_node) for cn, cn_node in children if _matches(cn_node, search)]
    else:
        visible = children

    if not visible:
        return name if node["endpoints"] else None

    if len(visible) == 1:
        cn, cnode = visible[0]
        child = _leaf_name(cnode, cn, search)
        if child is not None:
            return f"{name}/{child}"

    return None


def count_endpoints(node: dict) -> int:
    """Recursively count total endpoints."""
    total = len(node["endpoints"])
    for child in node["children"].values():
        total += count_endpoints(child)
    return total
