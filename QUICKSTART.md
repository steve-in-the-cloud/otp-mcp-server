# Quick Start Guide

## 🎉 Your OTP MCP Server is Ready!

**GitHub Repository**: https://github.com/steve-in-the-cloud/otp-mcp-server

## What You Have

A complete Model Context Protocol (MCP) server for OTP management with:
- ✅ TOTP (Time-based OTP) support
- ✅ HOTP (HMAC-based OTP) support  
- ✅ Multiple transport protocols (stdio, SSE, HTTP Stream)
- ✅ Ready for Render deployment
- ✅ All code committed and pushed to GitHub

## Next Steps to Deploy on Render

### Option 1: Quick Deploy (Recommended)

1. **Sign up at Render**: https://render.com (free tier available)

2. **Deploy with Blueprint**:
   - Click "New" → "Blueprint"
   - Connect your GitHub repo: `steve-in-the-cloud/otp-mcp-server`
   - Render will auto-detect `render.yaml` and configure everything
   - Click "Apply" and wait for deployment

3. **Done!** Your server will be live at: `https://otp-mcp-server-xxxx.onrender.com`

### Option 2: Manual Deploy

See the detailed [DEPLOYMENT.md](DEPLOYMENT.md) guide for step-by-step instructions.

## Local Testing

Test locally before deploying:

```bash
# Install dependencies
pip install -e .

# Run locally with HTTP Stream (simulates Render)
otp-mcp-server --http-stream --host 0.0.0.0 --port 8000

# Or run with stdio (for Claude Desktop local)
otp-mcp-server
```

## Using with Claude Desktop (Local)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

## Available Tools

Once running, your MCP server provides these tools:

- `list_otp_tokens` - List all stored OTP tokens
- `get_details` - Get token details
- `calculate_otp_codes` - Generate OTP codes
- `add_token` - Add new OTP tokens
- `delete_token` - Remove tokens

## Project Structure

```
OTP_MCP_Server/
├── otp_mcp/              # Main package
│   ├── __init__.py
│   ├── __main__.py       # Entry point
│   ├── server.py         # FastMCP server
│   ├── tool.py           # MCP tools
│   ├── resource.py       # MCP resources
│   └── common.py         # Constants
├── tests/                # Test files
├── pyproject.toml        # Package configuration
├── requirements.txt      # Dependencies
├── render.yaml           # Render deployment config
├── Procfile              # Alternative deployment config
├── README.md             # Documentation
├── DEPLOYMENT.md         # Deployment guide
└── LICENSE               # MIT License
```

## Environment Variables

For Render deployment:

- `OTP_MCP_SERVER_TRANSPORT` = `http-stream`
- `OTP_MCP_SERVER_HOST` = `0.0.0.0`
- `OTP_MCP_SERVER_PORT` = `$PORT` (auto-provided by Render)
- `OTP_MCP_SERVER_LOG_LEVEL` = `INFO`

## Important Notes

⚠️ **Free Tier Limitations**:
- Services spin down after 15 minutes of inactivity
- Ephemeral storage (OTP database resets on restart)
- Consider adding persistent disk for production use

🔒 **Security**:
- HTTPS enabled automatically on Render
- Store sensitive data in environment variables
- Consider adding authentication for production

## Resources

- **GitHub Repo**: https://github.com/steve-in-the-cloud/otp-mcp-server
- **Render Dashboard**: https://dashboard.render.com
- **MCP Documentation**: https://modelcontextprotocol.io
- **FastMCP Docs**: https://github.com/jlowin/fastmcp

## Need Help?

1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions
2. Review logs in Render dashboard
3. Open an issue on GitHub

---

**Ready to deploy?** Go to https://render.com and follow Option 1 above! 🚀
