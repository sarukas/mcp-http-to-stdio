"""
Entry point for the mcp-http-to-stdio package.

This allows the package to be run as:
- python -m mcp_http_to_stdio
- mcp-http-to-stdio (after pip install)
"""

from .bridge import main

if __name__ == "__main__":
    main()
