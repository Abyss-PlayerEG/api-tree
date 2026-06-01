"""Tree structure building and traversal utilities."""

from typing import TypedDict, NotRequired

class EndpointDict(TypedDict):
    """Typed representation of an API endpoint."""
    method: str
    method_lower: str
    summary: str
    summary_lower: str
    path: str
    path_lower: str


class TreeNode(TypedDict):
    """Typed representation of a tree node."""
    children: dict[str, "TreeNode"]
    endpoints: list[EndpointDict]
    sorted_children: NotRequired[list[tuple[str, "TreeNode"]]]


def build_tree(paths: dict[str, dict[str, object]]) -> TreeNode:
    """Build hierarchical tree from OpenAPI paths."""
    root: TreeNode = {"children": {}, "endpoints": []}

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

    _sort_tree(root)
    return root


def _sort_tree(node: TreeNode) -> None:
    """Recursively sort children in-place: directories first, then alphabetically."""
    for child in node["children"].values():
        _sort_tree(child)
    node["sorted_children"] = sorted(
        node["children"].items(),
        key=lambda x: (0 if x[1]["children"] else 1, x[0].lower()),
    )


def sort_children(node: TreeNode) -> list[tuple[str, TreeNode]]:
    """Return pre-sorted children list."""
    return node.get("sorted_children", sorted(
        node["children"].items(),
        key=lambda x: (0 if x[1]["children"] else 1, x[0].lower()),
    ))


def count_endpoints(node: TreeNode) -> int:
    """Recursively count total endpoints."""
    total = len(node["endpoints"])
    for child in node["children"].values():
        total += count_endpoints(child)
    return total


class TreeMatcher:
    """Pre-computed match results with memoization to avoid redundant recursion."""

    def __init__(self, root: TreeNode, search: str):
        self._search = search
        self._match_cache: dict[int, bool] = {}
        self._leaf_cache: dict[tuple[int, str], str | None] = {}
        self._match(root)

    def _match(self, node: TreeNode) -> bool:
        nid = id(node)
        if nid in self._match_cache:
            return self._match_cache[nid]
        result = False
        for ep in node["endpoints"]:
            if (self._search in ep["path_lower"]
                    or self._search in ep["summary_lower"]
                    or self._search in ep["method_lower"]):
                result = True
                break
        if not result:
            for child in node["children"].values():
                if self._match(child):
                    result = True
        self._match_cache[nid] = result
        return result

    def matches(self, node: TreeNode) -> bool:
        """Check if node or its subtree contains the search keyword."""
        return self._match_cache.get(id(node), False)

    def visible_children(self, node: TreeNode) -> list[tuple[str, TreeNode]]:
        """Return children filtered by match results."""
        return [(cn, cn_node) for cn, cn_node in sort_children(node)
                if self.matches(cn_node)]

    def leaf_name(self, node: TreeNode, name: str) -> str | None:
        """Trace chain merges to find a leaf node's final display name."""
        key = (id(node), name)
        if key in self._leaf_cache:
            return self._leaf_cache[key]
        self._leaf_cache[key] = None  # prevent infinite recursion
        visible = self.visible_children(node)
        if not visible:
            result = name if node["endpoints"] else None
        elif len(visible) == 1:
            cn, cnode = visible[0]
            child = self.leaf_name(cnode, cn)
            result = f"{name}/{child}" if child is not None else None
        else:
            result = None
        self._leaf_cache[key] = result
        return result

    def max_leaf_width(self, node: TreeNode) -> int:
        """Calculate max leaf path width for visible children of a node."""
        pad = 0
        for cn, cn_node in sort_children(node):
            if self.matches(cn_node):
                leaf = self.leaf_name(cn_node, cn)
                if leaf:
                    pad = max(pad, len(f"/{leaf}"))
        return pad


# Keep standalone functions for non-search usage (backward compatible)
def _matches(node: TreeNode, keyword: str) -> bool:
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


def _leaf_name(node: TreeNode, name: str, search: str = "") -> str | None:
    """Trace chain merges to find a leaf node's final display name."""
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


def _leaf_name_no_search(node: TreeNode, name: str) -> str | None:
    """Leaf name calculation without search filter."""
    children = sort_children(node)
    if not children:
        return name if node["endpoints"] else None
    if len(children) == 1:
        cn, cnode = children[0]
        child = _leaf_name_no_search(cnode, cn)
        if child is not None:
            return f"{name}/{child}"
    return None
