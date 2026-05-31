"""API Tree - Fetch OpenAPI route information and print as a tree structure."""

try:
    from ._version import __version__
except (ImportError, AttributeError):
    __version__ = "DEV"

from .app import main

__all__ = ["main", "__version__"]
