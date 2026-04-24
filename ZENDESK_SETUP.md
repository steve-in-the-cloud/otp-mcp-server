# Zendesk MCP Integration Setup Guide

This guide explains how to connect your OTP MCP Server to Zendesk using OAuth authentication.

## Architecture

Your OTP MCP Server now includes:
- **HTTP/REST endpoint** - Stateless JSON-RPC over HTTP
- **OAuth 2.0 flow** - Similar to Atlassian's MCP implementation
- **Zendesk-compatible** - Works with Zendesk's MCP connection interface

## Endpoints

Once deployed to Render, your server provides:

### OAuth Endpoints
- **Authorization**: `https://your-app.onrender.com/oauth/authorize`
- **Token**: `https://your-app.onrender.com/oauth/token`

### MCP Endpoint
- **Primary**: `https://your-app.onrender.com/v1/mcp`
- **Alternate**: `https://your-app.onrender.com/mcp`

### Health Check
- **Health**: `https://your-app.onrender.com/health`

## Deployment to Render

### 1. Push Changes to GitHub

The code has been updated. Push to GitHub:
```bash
cd /Users/stephenujfalussyzendesk.com/OTP_MCP_Server
git add -A
git commit -m "Add OAuth 2.0 and HTTP/REST transport for Zendesk"
git push
```

### 2. Render Will Auto-Deploy

Render detects the push and automatically redeploys with:
- HTTP/REST transport
- OAuth 2.0 endpoints
- Zendesk-compatible JSON-RPC

Wait 2-3 minutes for deployment to complete.

## Connecting to Zendesk

### Step 1: Get Your Render URL

From your Render dashboard:
- Navigate to your `otp-mcp-server` service
- Copy the URL (e.g., `https://otp-mcp-server-7luc.onrender.com`)

### Step 2: Configure in Zendesk

1. Go to **Zendesk Admin Centre** → **Apps and integrations** → **Actions** → **MCP connections**

2. Click **"Create MCP connection"**

3. In the **MCP server** section:
   - **URL**: Enter one of these:
     - `https://otp-mcp-server-7luc.onrender.com/v1/mcp` (recommended)
     - `https://otp-mcp-server-7luc.onrender.com/mcp` (alternate)

4. Click **"Test URL"**

5. Zendesk will initiate the OAuth flow:
   - You'll be redirected to your server's authorization page
   - Click **"Grant Access"**
   - You'll be redirected back to Zendesk with an authorization code
   - Zendesk exchanges the code for an access token
   - Connection established! ✅

### Step 3: Verify Connection

Once connected, Zendesk will show:
- ✅ Connection successful
- List of available tools:
  - `list_otp_tokens`
  - `get_details`
  - `calculate_otp_codes`
  - `add_token`
  - `delete_token`

## OAuth Flow Details

### Authorization Flow

1. **User initiates connection in Zendesk**
   - Zendesk redirects to: `https://your-app.onrender.com/oauth/authorize?client_id=...&redirect_uri=...&state=...`

2. **User grants access**
   - Server displays authorization page
   - User clicks "Grant Access"
   - Server generates authorization code
   - Redirects back to Zendesk with code

3. **Token exchange**
   - Zendesk POSTs to: `https://your-app.onrender.com/oauth/token`
   - Sends authorization code
   - Server responds with access token

4. **Authenticated requests**
   - Zendesk includes: `Authorization: Bearer <access_token>`
   - Server validates token
   - Processes MCP requests

### Token Lifecycle

- **Authorization codes**: Valid for 5 minutes
- **Access tokens**: Valid for 1 hour
- **Refresh tokens**: Can be used to get new access tokens

## Testing the Server

### Test Health Endpoint
```bash
curl https://otp-mcp-server-7luc.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "otp-mcp-server"
}
```

### Test MCP Endpoint (Requires Auth)
```bash
# This will fail without authentication
curl https://otp-mcp-server-7luc.onrender.com/v1/mcp
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32001,
    "message": "Unauthorized",
    "data": {"description": "Valid OAuth access token required"}
  }
}
```

This is correct! OAuth authentication is required.

## Available MCP Tools

Once connected, Zendesk can call these tools:

### 1. list_otp_tokens
List all stored OTP tokens.
```json
{
  "name": "list_otp_tokens",
  "arguments": {}
}
```

### 2. get_details
Get detailed information about specific tokens.
```json
{
  "name": "get_details",
  "arguments": {
    "pattern": "github"
  }
}
```

### 3. calculate_otp_codes
Generate OTP codes for matching tokens.
```json
{
  "name": "calculate_otp_codes",
  "arguments": {
    "pattern": "github"
  }
}
```

### 4. add_token
Add a new OTP token.
```json
{
  "name": "add_token",
  "arguments": {
    "secret": "JBSWY3DPEHPK3PXP",
    "issuer": "GitHub",
    "account": "user@example.com",
    "type": "TOTP",
    "algorithm": "SHA1",
    "digits": 6,
    "period": 30
  }
}
```

### 5. delete_token
Delete matching tokens.
```json
{
  "name": "delete_token",
  "arguments": {
    "pattern": "old-token"
  }
}
```

## Troubleshooting

### Connection Failed

**Problem**: "MCP server endpoint may be invalid or server may not be reachable"

**Solutions**:
1. Verify Render deployment is complete (check dashboard)
2. Test health endpoint: `curl https://your-app.onrender.com/health`
3. Ensure URL includes `/v1/mcp` or `/mcp`
4. Check Render logs for errors

### OAuth Authorization Failed

**Problem**: OAuth flow doesn't complete

**Solutions**:
1. Check Render logs during OAuth flow
2. Verify redirect URI matches Zendesk's expected URL
3. Ensure SECRET_KEY environment variable is set in Render

### Tokens Expire Quickly

**Problem**: Need to re-authenticate frequently

**Solution**: This is expected with the free tier's ephemeral storage. For production:
1. Add persistent disk storage in Render
2. Set `OTP_MCP_SERVER_DB=/data/otp.db`
3. Tokens will persist across restarts

### Server Spins Down

**Problem**: First request after inactivity is slow

**Solution**: This is expected on Render's free tier. The server spins down after 15 minutes of inactivity. Options:
1. Accept 30-second cold start delay
2. Upgrade to paid tier for always-on service
3. Set up periodic health checks to keep server warm

## Security Considerations

### Production Deployment

For production use, consider:

1. **Persistent Storage**: Add Render disk for database persistence
2. **Token Storage**: Implement Redis/database for OAuth tokens
3. **Rate Limiting**: Add rate limiting to endpoints
4. **Logging**: Enable detailed security logging
5. **HTTPS**: Already enabled by Render automatically
6. **Secrets**: Use Render's secret management for sensitive data

### Environment Variables

Set these in Render dashboard:
- `OTP_MCP_SERVER_TRANSPORT=http`
- `OTP_MCP_SERVER_LOG_LEVEL=INFO`
- `SECRET_KEY` (auto-generated by Render)
- `OTP_MCP_SERVER_DB=/data/otp.db` (if using persistent disk)

## Next Steps

1. **Push code to GitHub** (if not already done)
2. **Wait for Render deployment** (2-3 minutes)
3. **Test health endpoint** to verify deployment
4. **Connect from Zendesk** using the steps above
5. **Test OTP tools** in Zendesk

## Support

- **GitHub Issues**: https://github.com/steve-in-the-cloud/otp-mcp-server/issues
- **Render Logs**: Check dashboard for deployment/runtime logs
- **Zendesk Support**: Contact Zendesk for MCP integration questions

---

**Your Server**: https://otp-mcp-server-7luc.onrender.com

Ready to connect to Zendesk! 🚀
