# OTP-MCP-Server

Model Context Protocol (MCP) server that provides OTP (One-Time Password) generation

A Model Context Protocol (MCP) server built with FastMCP
that provides secure OTP (One-Time Password) generation.
Supports TOTP (Time-based) and HOTP (HMAC-based) algorithms
and multiple transport options including stdio, SSE, and HTTP Stream
for seamless integration with AI assistants and applications.

## Quick Start

### Installation

```bash
# Use uvx for isolated execution
uvx otp-mcp-server

# Or install from PyPI
pip install otp-mcp-server
```

### Basic Usage

```bash
# Run with STDIO (default, for Claude Desktop)
otp-mcp-server

# Run with HTTP Stream transport
otp-mcp-server --http-stream --host 0.0.0.0 --port 8000

# Run with SSE transport
otp-mcp-server --sse --host 0.0.0.0 --port 8000
```

### Using with Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "otp": {
      "command": "uvx",
      "args": ["otp-mcp-server"]
    }
  }
}
```

### Configuration

You can configure the server using command-line arguments or environment variables.

| Environment Variable      | Description                                  |
|---------------------------|----------------------------------------------|
| `OTP_MCP_SERVER_DB`       | Path to the tokens database file             |
| `OTP_MCP_SERVER_HOST`     | Host to bind the server to                   |
| `OTP_MCP_SERVER_PORT`     | Port to bind the server to                   |
| `OTP_MCP_SERVER_TRANSPORT`| Transport protocol to use                    |
| `OTP_MCP_SERVER_PATH`     | Path for HTTP transport                      |
| `OTP_MCP_SERVER_LOG_LEVEL`| Logging level                                |

## Features

- **TOTP (Time-based OTP)**: Generate time-based one-time passwords
- **HOTP (HMAC-based OTP)**: Generate HMAC-based one-time passwords
- **Multiple Transports**: Support for stdio, SSE, and HTTP Stream
- **Secure Storage**: Token secrets stored securely in local database
- **Multiple Hash Algorithms**: Support for SHA1, SHA256, SHA512, and MD5

## Available Tools

- `list_otp_tokens`: List all stored OTP tokens
- `get_details`: Get detailed information about specific tokens
- `calculate_otp_codes`: Generate OTP codes for tokens
- `add_token`: Add new OTP tokens
- `delete_token`: Remove OTP tokens

## Deployment

### Deploy to Render

This server can be deployed to Render for persistent availability:

1. Push the code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set the build command: `pip install -e .`
5. Set the start command: `otp-mcp-server --http-stream --host 0.0.0.0 --port $PORT`
6. Deploy!

### Environment Variables for Render

Set these in your Render dashboard:

- `OTP_MCP_SERVER_TRANSPORT`: `http-stream`
- `OTP_MCP_SERVER_HOST`: `0.0.0.0`
- `OTP_MCP_SERVER_PORT`: Render will provide this automatically via `$PORT`
- `OTP_MCP_SERVER_LOG_LEVEL`: `INFO` (or your preferred level)

## Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/steve-in-the-cloud/otp-mcp-server.git
cd otp-mcp-server

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## Requirements

- Python 3.11+
- Dependencies: click, fastmcp, freakotp, securid

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
