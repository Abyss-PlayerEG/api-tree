"""API Tree - Fetch OpenAPI route information and print as a tree structure."""

from ._version import __version__

from .app import main

__all__ = ["main", "__version__"]
