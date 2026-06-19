"""
命令行参数解析
Command-line argument parsing.
"""

import sys
from dataclasses import dataclass, field
from .config import config

BANNER = """
 █████╗ ██████╗ ██╗    ████████╗██████╗ ███████╗███████╗
██╔══██╗██╔══██╗██║    ╚══██╔══╝██╔══██╗██╔════╝██╔════╝
███████║██████╔╝██║       ██║   ██████╔╝█████╗  █████╗
██╔══██║██╔═══╝ ██║       ██║   ██╔══██╗██╔══╝  ██╔══╝
██║  ██║██║     ██║       ██║   ██║  ██║███████╗███████╗
╚═╝  ╚═╝╚═╝     ╚═╝       ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝
GitHub: https://github.com/Abyss-PlayerEG/api-tree
"""


def get_version() -> str:
    """
    获取应用版本号
    Get application version.
    """
    # Single-file distribution: __version__ defined at module level
    if "__version__" in globals():
        return str(globals()["__version__"])
    # Package: import from _version module
    try:
        from api_tree._version import __version__
        return str(__version__)
    except ImportError:
        return "DEV"


def get_tag() -> str:
    """
    获取构建标签
    Get build tag.
    """
    if "__tag__" in globals():
        return str(globals()["__tag__"])
    try:
        from api_tree._version import __tag__
        return str(__tag__)
    except ImportError:
        return "dev"


@dataclass
class Args:
    """
    解析后的命令行参数
    Parsed command-line arguments.
    """
    source: str = field(default_factory=lambda: config.default_url)
    search: str = ""
    output_html: bool = False
    agent_output: str = ""  # markdown, json, curl
    rag_output: str = ""  # jsonl, json
    rag_chunk_size: int = 10  # Number of endpoints per RAG chunk
    init_config: bool = False  # Generate default config file
    show_config: bool = False  # Show current config
    update: bool = False       # Execute update
    update_check: bool = False # Check for updates only


HELP_TEXT = ""


def get_help_text() -> str:
    """
    读取帮助文本
    Read help text from main module docstring.
    """
    # Single-file: module docstring is at the top of the merged file
    doc = sys.modules.get("__main__", None)
    if doc and doc.__doc__:
        return doc.__doc__.strip()
    # Package: read from main.py
    try:
        from api_tree.main import __doc__
        if __doc__:
            return __doc__.strip()
    except ImportError:
        pass
    return HELP_TEXT


def parse_args(argv: list[str] | None = None) -> Args:
    """
    解析命令行参数为 Args 实例
    Parse command-line arguments.
    """
    if argv is None:
        argv = sys.argv[1:]
    
    args = Args()
    i = 0
    
    while i < len(argv):
        if argv[i] == "-s" and i + 1 < len(argv):
            args.search = argv[i + 1].lower()
            i += 2
        elif argv[i] == "--html":
            args.output_html = True
            i += 1
        elif argv[i] == "--agent-output" and i + 1 < len(argv):
            format_type = argv[i + 1].lower()
            if format_type not in ("markdown", "json", "curl"):
                print(f"Error: Invalid agent output format '{format_type}'. Use: markdown, json, curl", file=sys.stderr)
                sys.exit(1)
            args.agent_output = format_type
            i += 2
        elif argv[i] == "--rag-output" and i + 1 < len(argv):
            format_type = argv[i + 1].lower()
            if format_type not in ("jsonl", "json"):
                print(f"Error: Invalid RAG output format '{format_type}'. Use: jsonl, json", file=sys.stderr)
                sys.exit(1)
            args.rag_output = format_type
            i += 2
        elif argv[i] == "--rag-chunk-size" and i + 1 < len(argv):
            try:
                args.rag_chunk_size = int(argv[i + 1])
                if args.rag_chunk_size <= 0:
                    raise ValueError
            except ValueError:
                print(f"Error: Invalid chunk size '{argv[i + 1]}'. Must be positive integer.", file=sys.stderr)
                sys.exit(1)
            i += 2
        elif argv[i] == "--init-config":
            args.init_config = True
            i += 1
        elif argv[i] == "--show-config":
            args.show_config = True
            i += 1
        elif argv[i] == "update":
            args.update = True
            i += 1
            if i < len(argv) and argv[i] == "--check":
                args.update_check = True
                i += 1
        elif argv[i] in ("-h", "--help"):
            print(get_help_text())
            sys.exit(0)
        elif argv[i] in ("-v", "--version"):
            for line in BANNER.splitlines():
                print(f"\t{line}")
            print(f"\tVersion: {get_version()}  Tag: {get_tag()}\n")
            sys.exit(0)
        elif argv[i].startswith("-"):
            print(f"Error: Unknown option '{argv[i]}'", file=sys.stderr)
            print(get_help_text())
            sys.exit(1)
        else:
            args.source = argv[i]
            i += 1
    
    return args
