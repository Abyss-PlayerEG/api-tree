"""HTML output renderer for API tree."""

from datetime import datetime

from .config import config
from .tree import sort_children, _leaf_name_no_search, TreeMatcher


def _escape(text: str) -> str:
    """Escape HTML special characters."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_html_tree(node: dict, title: str, total: int, search: str = "") -> str:
    """Render API tree as an HTML file. Returns the output file path."""
    METHOD_CLASS = {
        "GET": "method-get", "POST": "method-post", "PUT": "method-put",
        "DELETE": "method-delete", "PATCH": "method-patch",
    }

    matcher = TreeMatcher(node, search) if search else None
    lines = []

    def walk(n, prefix, is_last, path_acc, name, extra_eps=None, name_pad=0):
        children = sort_children(n)
        eps = n["endpoints"]
        if extra_eps:
            eps = extra_eps + eps

        if search:
            matched = matcher.matches(n)
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
            visible = matcher.visible_children(n)
        else:
            visible = children

        # Calculate max leaf path width
        if visible:
            child_pad = matcher.max_leaf_width(n) if search else _max_leaf_width_no_search(n)
        else:
            child_pad = 0

        # Only merge when current node has no own endpoints
        if name and len(visible) == 1 and not eps:
            merged = f"{path_acc}/{name}" if path_acc else name
            walk(visible[0][1], prefix, is_last, merged, visible[0][0], eps,
                 name_pad=name_pad or child_pad)
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

            if eps:
                # Show endpoints
                full_path = f"/{display}"
                if name_pad:
                    full_path = full_path.ljust(name_pad)
                line += f'<span class="leaf">{_escape(full_path)}</span>'
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

            lines.append(line)

        child_prefix = "" if name == "" else prefix + ("    " if is_last else "│   ")
        for i, (cn, cnode) in enumerate(visible):
            child_last = (i == len(visible) - 1)
            walk(cnode, child_prefix, child_last, "", cn, name_pad=child_pad)

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

    output_dir = config.output_dir
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = "".join(c for c in title if c.isalnum() or c in " _-")[:50].strip().replace(" ", "_")
    fname = f"api-tree_{safe}_{ts}.html" if safe else f"api-tree_{ts}.html"
    out = output_dir / fname
    out.write_text(html, encoding="utf-8")
    return str(out)



def _max_leaf_width_no_search(node: dict) -> int:
    """Calculate max leaf path width for all children (no search filter)."""
    pad = 0
    for cn, cn_node in sort_children(node):
        leaf = _leaf_name_no_search(cn_node, cn)
        if leaf:
            pad = max(pad, len(f"/{leaf}"))
    return pad
