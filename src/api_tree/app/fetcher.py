"""
OpenAPI 规范获取器
OpenAPI specification fetcher.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from .updater import _get_ssl_context


def fetch_openapi(source: str) -> dict[str, Any]:
    """
    获取 OpenAPI JSON:支持本地文件和远程 URL
    Fetch OpenAPI JSON from URL or local file.
    """
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]

    # Check if full URL: use directly if contains specific path
    parsed = urlparse(source)
    if parsed.path and parsed.path.rstrip("/") not in ("", "/"):
        url = source
    else:
        url = source.rstrip("/") + "/v3/api-docs"

    try:
        ctx = _get_ssl_context()
        req = urllib.request.Request(url, headers={"User-Agent": "api-tree"})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))  # type: ignore[no-any-return]
    except (urllib.error.URLError, ValueError) as e:
        reason = getattr(e, 'reason', str(e))
        print(f"Error: Cannot connect to {url}\n  {reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: {url} returned invalid JSON", file=sys.stderr)
        sys.exit(1)
