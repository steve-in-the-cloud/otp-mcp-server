#!/bin/bash
# Startup script for Render deployment
# Uses HTTP/REST transport with OAuth for Zendesk compatibility

echo "Starting OTP MCP Server with HTTP/REST + OAuth transport..."
echo "Host: 0.0.0.0"
echo "Port: $PORT"
echo "Transport: HTTP (Zendesk-compatible)"
echo ""
echo "OAuth endpoints will be available at:"
echo "  - Authorization: https://your-app.onrender.com/oauth/authorize"
echo "  - Token: https://your-app.onrender.com/oauth/token"
echo ""
echo "MCP endpoint:"
echo "  - https://your-app.onrender.com/v1/mcp"
echo ""

exec otp-mcp-server --http --host 0.0.0.0 --port "$PORT"
