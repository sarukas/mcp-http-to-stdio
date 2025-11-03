# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the mcp-http-to-stdio package.

## Project Overview

**mcp-http-to-stdio** is a Python bridge utility that enables Claude Desktop to connect to HTTP-based MCP (Model Context Protocol) servers via stdio transport.

**Key Purpose:** Protocol translation between Claude Desktop's stdio JSON-RPC interface and HTTP-based MCP servers.

## Architecture

```
Claude Desktop (stdio/JSON-RPC) ←→ mcp-http-to-stdio (bridge) ←→ HTTP MCP Server
```

The bridge:
1. Reads JSON-RPC requests from stdin (from Claude Desktop)
2. Forwards them as HTTP POST requests to the MCP server
3. Returns JSON-RPC responses via stdout (to Claude Desktop)

## Project Structure

```
mcp-http-to-stdio/
├── mcp_http_to_stdio/
│   ├── __init__.py          # Package metadata and exports
│   ├── __main__.py          # Entry point for python -m
│   └── bridge.py            # Core bridge implementation
├── README.md                # User documentation
├── PUBLISHING.md            # PyPI publishing guide
├── pyproject.toml           # Package metadata and build config
├── requirements.txt         # Runtime dependencies
├── LICENSE                  # MIT License
├── MANIFEST.in              # Distribution file list
└── claude_desktop_config.example.json  # Example config

```

## Key Components

### bridge.py

**Core bridge implementation** with these key classes/functions:

1. **MCPClientWrapper** (class)
   - Manages HTTP session with connection pooling
   - Handles JSON-RPC request/response translation
   - Implements retry logic and error handling
   - Runs stdio loop for Claude Desktop communication

2. **main()** (function)
   - Command-line argument parsing
   - Authentication token resolution (env var or arg)
   - Bridge initialization and execution

**Key Features:**
- **Connection Pooling:** Reuses HTTP connections with keep-alive
- **Retry Strategy:** Automatic retry on transient errors (429, 500-504)
- **Authentication:** Custom header-based auth (`x-ally-share-key`)
- **Logging:** File (`mcp_http_to_stdio.log`) and stderr logging
- **Performance Tracking:** Request timing with slow request warnings

### __init__.py

Package initialization with:
- Version info (`__version__`)
- Author and license metadata
- `main` function export

### __main__.py

Entry point allowing:
```bash
python -m mcp_http_to_stdio --url http://localhost:8080/mcp
```

## Development Workflow

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run directly (for testing)
python -m mcp_http_to_stdio --url http://localhost:8080/mcp --share-key YOUR_TOKEN

# Install in editable mode
pip install -e .

# Run as command
mcp-http-to-stdio --url http://localhost:8080/mcp
```

### Testing

Currently manual testing via:
1. Start an HTTP MCP server (e.g., MyAlly Share Server on port 8081)
2. Configure Claude Desktop with the bridge
3. Verify tool discovery and execution

**Future:** Add automated tests for protocol translation, error handling, and retry logic.

### Building for PyPI

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Install build tools
pip install build twine

# Build package
python -m build

# Check build
twine check dist/*

# Test upload (optional)
twine upload --repository testpypi dist/*

# Production upload
twine upload dist/*
```

See `PUBLISHING.md` for detailed publishing instructions.

## Configuration

### Command-Line Arguments

**Required:**
- `--url`: HTTP MCP server endpoint URL (e.g., `http://localhost:8080/mcp`)

**Optional:**
- `--share-key`: Authentication token (can use `ALLY_SHARE_KEY` env var instead)
- `--timeout`: Request timeout in seconds (default: 300)

### Authentication

Authentication token can be provided via:
1. **Environment variable** (recommended): `ALLY_SHARE_KEY=token mcp-http-to-stdio ...`
2. **Command-line argument**: `mcp-http-to-stdio --share-key token ...`

The bridge adds the token to the `x-ally-share-key` HTTP header.

### Claude Desktop Configuration

Edit `claude_desktop_config.json`:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-http-mcp-server": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url", "http://localhost:8080/mcp"
      ],
      "env": {
        "ALLY_SHARE_KEY": "your-auth-token-here"
      }
    }
  }
}
```

## Protocol Details

### JSON-RPC 2.0 over STDIO

Claude Desktop sends JSON-RPC requests via stdin:
```json
{"jsonrpc": "2.0", "method": "tools/list", "id": 1}
```

Bridge forwards as HTTP POST:
```http
POST /mcp HTTP/1.1
Host: localhost:8080
x-ally-share-key: <auth-token>
Content-Type: application/json

{"jsonrpc": "2.0", "method": "tools/list", "id": 1}
```

HTTP response returned via stdout:
```json
{"jsonrpc": "2.0", "result": {...}, "id": 1}
```

### MCP Methods Supported

All standard MCP JSON-RPC methods:
- **initialize** - Protocol handshake
- **tools/list** - List available tools
- **tools/call** - Execute a tool
- **Notifications** - Methods without `id` field (no response expected)

### Error Handling

The bridge handles:
- **Network errors**: Connection refused, timeouts, DNS failures
- **HTTP errors**: 4xx/5xx status codes with retry logic
- **Auth errors**: 401/403 responses
- **JSON errors**: Invalid JSON in stdin
- **Unexpected errors**: Catch-all error handler

Errors returned as JSON-RPC error responses:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Share Server request failed: ..."
  },
  "id": 1
}
```

## Common Development Tasks

### Adding New Features

When adding features to the bridge:
1. **Maintain protocol compliance** - Must be JSON-RPC 2.0 compliant
2. **Preserve backward compatibility** - Don't break existing configurations
3. **Update documentation** - README.md and docstrings
4. **Test with Claude Desktop** - Verify integration works end-to-end

### Debugging

**Enable verbose logging:**
- Check `mcp_http_to_stdio.log` file
- View stderr output in Claude Desktop developer console

**Common issues:**
1. **Connection refused** - MCP server not running or wrong URL
2. **401/403 errors** - Authentication token missing or invalid
3. **Timeout errors** - Increase `--timeout` argument
4. **JSON parse errors** - Check stdin format from Claude Desktop

### Version Numbering

Follow Semantic Versioning (https://semver.org/):
- **MAJOR** version for incompatible API changes (e.g., 1.0.0 → 2.0.0)
- **MINOR** version for new functionality, backwards compatible (e.g., 0.1.0 → 0.2.0)
- **PATCH** version for bug fixes, backwards compatible (e.g., 0.1.0 → 0.1.1)

Update version in:
- `mcp_http_to_stdio/__init__.py` (`__version__`)
- `pyproject.toml` (`version`)

## Security Considerations

1. **Protect authentication tokens** - Never commit tokens to version control
2. **Use environment variables** - Don't hardcode tokens in config files
3. **Use HTTPS in production** - Always use HTTPS URLs for remote servers
4. **Rotate tokens regularly** - Implement token rotation strategy
5. **Validate inputs** - Sanitize all inputs from stdin and HTTP responses

## Contributing Guidelines

When contributing to this project:
1. **Follow existing code style** - Consistent formatting and naming
2. **Add docstrings** - Document all functions and classes
3. **Update documentation** - Keep README.md in sync with code changes
4. **Test thoroughly** - Manual testing with Claude Desktop before committing
5. **Increment version** - Follow semantic versioning for releases

## License

MIT License - See LICENSE file for details

## Links

- **PyPI Package:** https://pypi.org/project/mcp-http-to-stdio/
- **Model Context Protocol:** https://modelcontextprotocol.io/
- **Claude Desktop:** https://claude.ai/download

## Example Usage

### MyAlly Workspace Sharing

This bridge was originally created for MyAlly's workspace sharing feature:

```json
{
  "mcpServers": {
    "myally-workspace": {
      "command": "mcp-http-to-stdio",
      "args": [
        "--url", "http://localhost:8081/share/mcp"
      ],
      "env": {
        "ALLY_SHARE_KEY": "ally_share_xxxxxxxx..."
      }
    }
  }
}
```

But it works with any HTTP-based MCP server that follows the JSON-RPC 2.0 protocol.
