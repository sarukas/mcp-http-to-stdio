# MCP HTTP-to-STDIO Bridge

A Python bridge utility that enables Claude Desktop to connect to HTTP-based MCP (Model Context Protocol) servers via stdio transport.

## Overview

Claude Desktop uses stdio (stdin/stdout) to communicate with MCP servers, but many MCP servers expose HTTP endpoints. This bridge translates between the two protocols, allowing Claude Desktop to use HTTP-based MCP servers.

**Architecture:**
```
Claude Desktop (stdio/JSON-RPC) ←→ mcp-http-to-stdio (bridge) ←→ HTTP MCP Server
```

## Features

- ✅ **Protocol Translation**: Converts stdio JSON-RPC to HTTP POST requests
- ✅ **Authentication**: Supports custom header-based authentication
- ✅ **Connection Pooling**: Optimized HTTP connections with keep-alive and retry logic
- ✅ **Error Handling**: Comprehensive error responses for network, auth, and server errors
- ✅ **Logging**: File and stderr logging for debugging
- ✅ **Performance**: Tracks request timing and logs slow requests

## Prerequisites

- Python 3.8+
- An HTTP-based MCP server to connect to
- Claude Desktop

## Installation

### From PyPI (Recommended)

```bash
pip install mcp-http-to-stdio
```

This installs the package globally and makes the `mcp-http-to-stdio` command available system-wide.

### From Source

```bash
git clone https://github.com/your-org/agentic-enterprise.git
cd agentic-enterprise/packages/mcp-http-to-stdio
pip install -e .
```

## Configuration

### Claude Desktop Config File Location

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### Basic Configuration

```json
{
  "mcpServers": {
    "my-http-mcp-server": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url",
        "http://localhost:8080/mcp"
      ],
      "env": {
        "AUTH_TOKEN": "your-auth-token-here"
      }
    }
  }
}
```

### Remote Server Configuration

```json
{
  "mcpServers": {
    "remote-mcp-server": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url",
        "https://mcp-server.example.com/mcp"
      ],
      "env": {
        "AUTH_TOKEN": "your-auth-token-here"
      }
    }
  }
}
```

### Configuration with Timeout

```json
{
  "mcpServers": {
    "my-http-mcp-server": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url",
        "http://localhost:8080/mcp",
        "--timeout",
        "600"
      ],
      "env": {
        "AUTH_TOKEN": "your-auth-token-here"
      }
    }
  }
}
```

## Command Line Arguments

```bash
mcp-http-to-stdio --help
```

### Required Arguments

- `--url`: HTTP MCP server endpoint URL (e.g., `http://localhost:8080/mcp`)

### Optional Arguments

- `--share-key`: Authentication key (alternative to environment variable)
- `--timeout`: Request timeout in seconds (default: 300 = 5 minutes)

### Authentication

Authentication tokens can be passed via:
1. **Environment variable** (recommended): Set in the `env` section of Claude Desktop config
2. **Command line argument**: Use `--share-key` flag

The bridge adds the authentication token to the `x-ally-share-key` HTTP header when making requests to the MCP server.

## Usage

1. **Install** the bridge: `pip install mcp-http-to-stdio`
2. **Configure** Claude Desktop with your HTTP MCP server URL
3. **Restart** Claude Desktop to load the new MCP server
4. **Verify**: Ask Claude "What MCP tools are available?"

## Logging

Logs are written to two locations:

1. **Log file**: `mcp_http_to_stdio.log` (in the current directory)
2. **stderr**: Visible in Claude Desktop's developer console

### View Logs

```bash
# Follow log file
tail -f mcp_http_to_stdio.log

# View Claude Desktop logs
# Enable developer mode in Claude Desktop settings
# Open developer console and look for MCP-related messages
```

## Troubleshooting

### "Connection refused" or "Failed to connect"

**Cause**: HTTP MCP server is not running or URL is incorrect

**Solution**:
1. Verify the MCP server is running
2. Check the URL in your configuration
3. Test the endpoint with curl: `curl http://localhost:8080/mcp`

### "Authentication failed" or 401/403 errors

**Cause**: Authentication token is missing, incorrect, or expired

**Solution**:
1. Verify the auth token is correct in the `env` section
2. Check if the token has expired
3. Regenerate the token if necessary

### Claude Desktop doesn't see the MCP server

**Cause**: Configuration file is malformed or in wrong location

**Solution**:
1. Validate JSON syntax at https://jsonlint.com
2. Verify file location matches your operating system
3. Restart Claude Desktop after making changes
4. Check Claude Desktop logs for MCP initialization errors

### Slow response times

**Cause**: MCP server queries can take time, especially for complex operations

**Expected behavior**:
- Simple queries: <10 seconds
- Complex queries: 10-60 seconds
- Very complex queries: 60+ seconds (consider increasing timeout)

The bridge logs warnings for requests taking longer than 10 seconds.

## Supported MCP Methods

The bridge supports all standard MCP JSON-RPC methods:

1. **`initialize`**: Protocol handshake
2. **`tools/list`**: List available tools
3. **`tools/call`**: Execute a tool
4. **Notifications**: Properly handles JSON-RPC notifications (no response expected)

## Technical Details

### Protocol Flow

1. Claude Desktop sends JSON-RPC request via stdin
2. Bridge forwards request to HTTP MCP server via POST
3. HTTP MCP server processes request and returns JSON-RPC response
4. Bridge forwards response back to Claude Desktop via stdout

### HTTP Request Format

```http
POST /mcp HTTP/1.1
Host: localhost:8080
x-ally-share-key: <auth-token>
Content-Type: application/json

{"jsonrpc": "2.0", "method": "tools/list", "id": 1}
```

### Connection Pooling

The bridge uses optimized HTTP connection pooling:

- **Keep-alive**: Connections are reused
- **Retry logic**: Automatic retry on transient errors (429, 500-504)
- **Pool size**: 10 cached connections
- **Backoff**: Exponential backoff (1s, 2s, 4s)

## Example: MyAlly Share Server

This bridge was originally created for MyAlly's workspace sharing feature. Here's an example configuration:

```json
{
  "mcpServers": {
    "myally-workspace": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url",
        "http://localhost:8081/share/mcp"
      ],
      "env": {
        "ALLY_SHARE_KEY": "ally_share_xxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

For MyAlly-specific documentation, see the [MyAlly repository](https://github.com/your-org/agentic-enterprise).

## Security Considerations

- **Protect authentication tokens**: Treat them like passwords
- **Use environment variables**: Don't hardcode tokens in config files
- **Use HTTPS**: For production deployments, always use HTTPS URLs
- **Rotate tokens**: Regularly regenerate authentication tokens
- **Don't commit tokens**: Never commit tokens to version control

## Contributing

Contributions are welcome! This is a simple bridge utility, but improvements to error handling, logging, or protocol support are always appreciated.

## License

MIT License - See LICENSE file for details

## Links

- **PyPI**: https://pypi.org/project/mcp-http-to-stdio/
- **GitHub**: https://github.com/your-org/agentic-enterprise
- **MCP Specification**: https://modelcontextprotocol.io/
