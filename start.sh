#!/bin/bash
# Startup script for Render deployment
# Ensures HTTP Stream transport is used

echo "Starting OTP MCP Server with HTTP Stream transport..."
echo "Host: 0.0.0.0"
echo "Port: $PORT"
echo "Transport: HTTP Stream"

exec otp-mcp-server --http-stream --host 0.0.0.0 --port "$PORT" --path /mcp
