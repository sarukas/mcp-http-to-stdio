"""
MCP HTTP-to-STDIO Bridge

A bridge utility that enables Claude Desktop to connect to HTTP-based MCP servers
via stdio transport.
"""

__version__ = "0.1.1"
__author__ = "sarukas"
__license__ = "MIT"

from .bridge import main

__all__ = ["main"]
