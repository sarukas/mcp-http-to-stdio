#!/usr/bin/env python3
"""MCP HTTP-to-STDIO Bridge for Claude Desktop integration.

This script bridges Claude Desktop's stdio-based MCP protocol to HTTP-based
MCP servers.

Usage:
    # Via environment variable (recommended - more secure)
    ALLY_SHARE_KEY=YOUR_AUTH_TOKEN mcp-http-to-stdio --url http://localhost:8080/mcp

    # Via command-line argument (backward compatible)
    mcp-http-to-stdio --share-key YOUR_AUTH_TOKEN --url http://localhost:8080/mcp

Configuration for Claude Desktop (claude_desktop_config.json):
{
  "mcpServers": {
    "my-http-mcp-server": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url", "http://localhost:8080/mcp"
      ],
      "env": {
        "ALLY_SHARE_KEY": "your-auth-token"
      }
    }
  }
}
"""

import sys
import json
import argparse
import requests
import logging
import time
from typing import Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('mcp_http_to_stdio.log'), logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Reduce urllib3 verbosity (connection pool debug messages)
logging.getLogger('urllib3.connectionpool').setLevel(logging.INFO)


class MCPClientWrapper:
    """Wrapper that translates stdio MCP protocol to HTTP MCP endpoint."""

    def __init__(self, share_key: str, url: str, timeout: int = 300):
        """Initialize wrapper.

        Args:
            share_key: Share key for authentication (x-ally-share-key header)
            url: Share Server MCP endpoint URL
            timeout: Request timeout in seconds (default: 300 = 5 minutes)
        """
        self.share_key = share_key
        self.url = url
        self.timeout = timeout

        # Configure session with optimized connection pooling
        self.session = requests.Session()

        # Retry strategy for transient errors
        retry_strategy = Retry(
            total=3,  # Max 3 retries
            backoff_factor=1,  # 1s, 2s, 4s delays
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            allowed_methods=["POST"]  # Only retry POST requests
        )

        # HTTP adapter with connection pooling configuration
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,  # Number of connection pools to cache
            pool_maxsize=10,  # Max connections in each pool
            pool_block=False  # Don't block if pool is full, create new connection
        )

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update({
            'x-ally-share-key': share_key,
            'Content-Type': 'application/json',
            'Connection': 'keep-alive'  # Enable HTTP keep-alive
        })

        logger.info(f"Initialized MCP client wrapper for {url} (timeout: {timeout}s)")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request from Claude Desktop.

        Args:
            request: JSON-RPC request from Claude Desktop

        Returns:
            JSON-RPC response from Share Server, or None for notifications
        """
        method = request.get('method')
        is_notification = 'id' not in request
        logger.info(f"Handling {'notification' if is_notification else 'request'}: {method}")
        logger.debug(f"Request payload: {json.dumps(request, indent=2)}")

        try:
            # Track timing for performance monitoring
            start_time = time.time()

            # Log tool call details for better debugging
            if method == 'tools/call':
                params = request.get('params', {})
                tool_name = params.get('name', 'unknown')
                logger.info(f"Executing tool call: {tool_name}")

            # Forward request to Share Server MCP endpoint
            response = self.session.post(
                self.url,
                json=request,
                timeout=self.timeout
            )

            # Log timing
            elapsed = time.time() - start_time
            logger.info(f"Request completed in {elapsed:.2f}s")

            # Warn on slow requests
            if elapsed > 10:
                logger.warning(f"Slow request detected ({elapsed:.2f}s) - this is expected for complex agent queries")

            response.raise_for_status()

            # Handle HTTP 204 No Content (notifications)
            if response.status_code == 204:
                logger.debug(f"Received 204 No Content for notification {method}")
                return None

            result = response.json()

            # For notifications, don't return a response to Claude Desktop
            if is_notification:
                logger.debug(f"Notification handled, no response sent")
                return None

            logger.debug(f"Response: {json.dumps(result, indent=2)}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {e}")

            # Don't send error responses for notifications
            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Share Server request failed: {str(e)}"
                },
                "id": request.get('id')
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)

            # Don't send error responses for notifications
            if is_notification:
                return None

            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                },
                "id": request.get('id')
            }

    def run(self):
        """Run MCP client wrapper (stdio loop)."""
        logger.info("Starting MCP client wrapper stdio loop")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)

                    # Write response to stdout (for Claude Desktop)
                    # Skip if None (notifications don't get responses)
                    if response is not None:
                        sys.stdout.write(json.dumps(response) + '\n')
                        sys.stdout.flush()

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON input: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        },
                        "id": None
                    }
                    sys.stdout.write(json.dumps(error_response) + '\n')
                    sys.stdout.flush()

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down")
        except Exception as e:
            logger.error(f"Fatal error in stdio loop: {e}", exc_info=True)
            sys.exit(1)


def main():
    """Main entry point."""
    import os

    parser = argparse.ArgumentParser(
        description='MCP HTTP-to-STDIO Bridge - Connect Claude Desktop to HTTP MCP servers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--share-key',
        required=False,  # Not required if ALLY_SHARE_KEY env var is set
        help='Authentication token for the HTTP MCP server (x-ally-share-key header). Can also be set via ALLY_SHARE_KEY environment variable.'
    )
    parser.add_argument(
        '--url',
        required=True,
        help='HTTP MCP server endpoint URL (e.g., http://localhost:8080/mcp)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Request timeout in seconds (default: 300 = 5 minutes)'
    )

    args = parser.parse_args()

    # Get auth token from environment variable or argument
    auth_token = args.share_key or os.getenv('ALLY_SHARE_KEY')

    if not auth_token:
        logger.error("Authentication token not provided via --share-key argument or ALLY_SHARE_KEY environment variable")
        parser.error("--share-key argument or ALLY_SHARE_KEY environment variable is required")

    # Create and run bridge
    wrapper = MCPClientWrapper(auth_token, args.url, timeout=args.timeout)
    wrapper.run()


if __name__ == '__main__':
    main()
