# Deployment Guide - OTP MCP Server on Render

This guide will walk you through deploying your OTP MCP Server to Render for persistent, cloud-based availability.

## Prerequisites

- A GitHub account with your repository: https://github.com/steve-in-the-cloud/otp-mcp-server
- A Render account (sign up at https://render.com - free tier available)

## Deployment Steps

### 1. Sign Up / Log In to Render

Go to https://render.com and create an account or log in.

### 2. Create a New Web Service

1. Click the "New +" button in the Render dashboard
2. Select "Web Service"

### 3. Connect Your GitHub Repository

1. If this is your first time, you'll need to connect your GitHub account
2. Search for and select: `steve-in-the-cloud/otp-mcp-server`
3. Click "Connect"

### 4. Configure Your Web Service

Fill in the following settings:

**Basic Settings:**
- **Name**: `otp-mcp-server` (or your preferred name)
- **Region**: Choose the closest region to you (e.g., Oregon, Ohio, Frankfurt)
- **Branch**: `master`
- **Runtime**: Python 3

**Build & Deploy Settings:**
- **Build Command**: 
  ```
  pip install -e .
  ```
  
- **Start Command**: 
  ```
  otp-mcp-server --http-stream --host 0.0.0.0 --port $PORT
  ```

**Instance Type:**
- Select **Free** (or paid if you need more resources)

### 5. Add Environment Variables

Click "Add Environment Variable" and add the following:

| Key | Value |
|-----|-------|
| `OTP_MCP_SERVER_TRANSPORT` | `http-stream` |
| `OTP_MCP_SERVER_HOST` | `0.0.0.0` |
| `OTP_MCP_SERVER_LOG_LEVEL` | `INFO` |
| `PYTHON_VERSION` | `3.11` |

**Note**: `PORT` is automatically provided by Render - don't set it manually.

### 6. Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Start your server
   - Provide you with a URL like: `https://otp-mcp-server-xxxx.onrender.com`

### 7. Monitor Deployment

- Watch the deployment logs in real-time
- The first deployment may take 2-3 minutes
- Once you see "Starting OTP MCP server", your service is running!

## Accessing Your MCP Server

Once deployed, your server will be available at the Render URL.

### Test the Endpoint

Your MCP server will be accessible at:
```
https://your-app-name.onrender.com/mcp
```

### Connect from Claude Desktop

Update your Claude Desktop configuration to use the deployed server:

```json
{
  "mcpServers": {
    "otp": {
      "command": "node",
      "args": ["-e", "require('http').get('https://your-app-name.onrender.com/mcp')"]
    }
  }
}
```

Or use it via HTTP client in your applications:

```bash
curl -X POST https://your-app-name.onrender.com/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "list_otp_tokens", "params": {}}'
```

## Important Notes

### Free Tier Limitations

- **Spin Down**: Free tier services spin down after 15 minutes of inactivity
- **Spin Up**: Cold starts take ~30 seconds when the service wakes up
- **Hours**: 750 free hours per month (enough for continuous operation)

### Upgrade for Production

For production use, consider upgrading to a paid plan for:
- Always-on service (no spin down)
- Better performance
- Automatic SSL certificates
- Custom domains

### Database Persistence

⚠️ **Important**: The free tier uses ephemeral storage. Your OTP tokens will be lost when the service restarts.

**Solutions:**
1. **Render Disks** (Paid): Add persistent disk storage to your service
2. **External Database**: Use PostgreSQL or another database service
3. **Regular Backups**: Export your tokens and re-import after restart

To add persistent storage:
1. Go to your service settings
2. Navigate to "Disks"
3. Add a new disk at `/data`
4. Set environment variable: `OTP_MCP_SERVER_DB=/data/otp.db`

## Updating Your Deployment

Render automatically deploys when you push to your GitHub repository:

```bash
# Make changes to your code
git add .
git commit -m "Your changes"
git push origin master
```

Render will detect the push and redeploy automatically.

## Troubleshooting

### Service Won't Start

Check the logs in Render dashboard:
- Look for Python import errors
- Verify all environment variables are set
- Ensure the start command is correct

### Port Binding Issues

Make sure you're using:
```bash
--host 0.0.0.0 --port $PORT
```

Render provides `$PORT` automatically - don't hardcode it.

### Database Not Persisting

Add a persistent disk (see Database Persistence section above).

## Security Considerations

1. **HTTPS**: Render provides free SSL certificates automatically
2. **Environment Variables**: Store sensitive data in Render's environment variables (encrypted at rest)
3. **Access Control**: Consider implementing authentication for production use
4. **Secrets**: Never commit OTP secrets to git - use environment variables

## Monitoring

In the Render dashboard you can:
- View real-time logs
- Monitor resource usage
- Set up alerts
- Track deployment history

## Alternative: Deploy with render.yaml

This repository includes a `render.yaml` file for Infrastructure as Code deployment:

1. Go to https://dashboard.render.com/
2. Click "New" → "Blueprint"
3. Connect your repository
4. Render will automatically detect and use `render.yaml`

## Cost Estimate

- **Free Tier**: $0/month (with limitations)
- **Starter Plan**: $7/month (always on, 512MB RAM)
- **Standard Plan**: $25/month (more resources)
- **Persistent Disk**: $0.25/GB/month

## Support

- Render Documentation: https://render.com/docs
- GitHub Issues: https://github.com/steve-in-the-cloud/otp-mcp-server/issues

## Next Steps

1. Deploy your server to Render
2. Test the endpoints
3. Configure Claude Desktop to use your deployed server
4. (Optional) Set up persistent storage
5. (Optional) Add custom domain

---

**Your Server URL**: https://github.com/steve-in-the-cloud/otp-mcp-server

Happy deploying! 🚀
