"""Console output for API tree."""

from .color import Color
from .tree import sort_children, _matches, _leaf_name


def print_tree(node: dict, prefix: str = "", is_last: bool = True,
               search: str = "", name: str = "", path_accum: str = "",
               extra_eps: list = None, name_pad: int = 0):
    """Print API tree to terminal with colors."""
    children = sort_children(node)
    eps = node["endpoints"]
    if extra_eps:
        eps = extra_eps + eps

    # Search filter (including ancestor endpoints)
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

    # Pre-filter visible children in search mode
    if search:
        visible = [(cn, cn_node) for cn, cn_node in children if _matches(cn_node, search)]
    else:
        visible = children

    # Calculate max leaf path width (for comment column alignment)
    child_pad = 0
    if visible:
        for cn, cn_node in visible:
            leaf = _leaf_name(cn_node, cn, search)
            if leaf:
                child_pad = max(child_pad, len(f"/{leaf}"))

    # Single child (visible) -> chain merge path and endpoints
    # Only merge when current node has no own endpoints
    if name and len(visible) == 1 and not eps:
        merged = f"{path_accum}/{name}" if path_accum else name
        print_tree(visible[0][1], prefix, is_last, search, visible[0][0], merged, eps,
                   name_pad=name_pad or child_pad)
        return

    # Search mode: only show matching endpoints
    if search and eps:
        eps = [ep for ep in eps if (
            search in ep["path_lower"]
            or search in ep["summary_lower"]
            or search in ep["method_lower"]
        )]

    # Build final display path
    display_name = f"{path_accum}/{name}" if path_accum else name

    branch = "" if name == "" else ("└── " if is_last else "├── ")

    if name:
        line = f"{Color.DIM}{prefix}{Color.RESET}"
        line += f"{Color.DIM}{branch}{Color.RESET}"

        if eps:
            # Show endpoints (whether or not has children)
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
            # Directory node (no endpoints)
            line += f"/{display_name}"
        print(line)

    # Children
    child_prefix = "" if name == "" else prefix + ("    " if is_last else "│   ")
    for i, (child_name, child_node) in enumerate(visible):
        child_is_last = (i == len(visible) - 1)
        print_tree(child_node, child_prefix, child_is_last, search, child_name, "",
                   name_pad=child_pad)
