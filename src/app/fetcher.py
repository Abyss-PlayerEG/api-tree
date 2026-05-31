"""OpenAPI specification fetcher."""

import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlparse


def fetch_openapi(source: str) -> dict:
    """Fetch OpenAPI JSON from URL or local file."""
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8") as f:
            return json.load(f)

    # Check if full URL: use directly if contains specific path
    parsed = urlparse(source)
    if parsed.path and parsed.path.rstrip("/") not in ("", "/"):
        url = source
    else:
        url = source.rstrip("/") + "/v3/api-docs"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"Error: Cannot connect to {url}\n  {e.reason}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: {url} returned invalid JSON", file=sys.stderr)
        sys.exit(1)
