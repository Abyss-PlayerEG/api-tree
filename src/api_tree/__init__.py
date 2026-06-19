"""
API 树 - 获取 OpenAPI 路由信息并以树状结构打印
API Tree - Fetch OpenAPI route information and print as a tree structure.
"""

try:
    from ._version import __version__, __tag__
except (ImportError, AttributeError):
    __version__ = "DEV"
    __tag__ = "dev"

from .app import main

__all__ = ["main", "__version__", "__tag__"]
