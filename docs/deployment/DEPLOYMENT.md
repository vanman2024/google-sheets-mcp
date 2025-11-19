# Google Sheets MCP Server - Deployment Guide

This guide covers all deployment options for the Google Sheets MCP Server.

## Deployment Options

| Transport | Use Case | Multi-client | Network Access |
|-----------|----------|--------------|----------------|
| STDIO | IDE integration | No | No |
| HTTP | Web services, APIs | Yes | Yes |
| HTTP (Production) | High-availability | Yes | Yes |

## Quick Start

### 1. Installation

```bash
# Clone and install
cd /path/to/google-sheets
./scripts/install.sh

# Or with uv
uv pip install -e .

# Or with pip
pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Set Up Google OAuth

Follow the guide in `docs/setup/GOOGLE_OAUTH_SETUP.md`

## STDIO Transport (Local/IDE)

STDIO is the default transport for IDE integrations.

### Starting STDIO Server

```bash
./scripts/start.sh
# or
python src/server.py
```

### IDE Configuration

See the `configs/` directory for ready-to-use configurations:
- `claude_desktop_config.json` - Claude Desktop
- `cursor_config.json` - Cursor IDE
- `claude_code_config.json` - Claude Code

## HTTP Transport (Web/API)

HTTP transport enables network access and multiple clients.

### Starting HTTP Server

```bash
# Development
./scripts/start.sh http

# Production with uvicorn
./scripts/start.sh http-prod
```

### Environment Variables

```bash
MCP_HOST=0.0.0.0        # Bind address
MCP_PORT=8000           # Server port
MCP_WORKERS=4           # Uvicorn workers (production)
CORS_ORIGINS=http://localhost:3000  # Allowed origins
LOG_LEVEL=INFO          # Logging level
```

### Health Check

```bash
# Check server health
./scripts/health_check.sh

# Manual check
curl http://localhost:8000/health
```

### Readiness Check

```bash
curl http://localhost:8000/ready
```

## Production Deployment

### With Uvicorn (Recommended)

```bash
uvicorn src.server_http:app --host 0.0.0.0 --port 8000 --workers 4
```

### With Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "src.server_http:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Build and run:

```bash
docker build -t google-sheets-mcp .
docker run -p 8000:8000 -v ~/.config/mcp-gdrive:/root/.config/mcp-gdrive google-sheets-mcp
```

### With Systemd

Create `/etc/systemd/system/google-sheets-mcp.service`:

```ini
[Unit]
Description=Google Sheets MCP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/google-sheets-mcp
Environment=GDRIVE_CREDS_DIR=/opt/google-sheets-mcp/.config
ExecStart=/usr/bin/uvicorn src.server_http:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable google-sheets-mcp
sudo systemctl start google-sheets-mcp
```

## CORS Configuration

For browser-based clients, configure CORS:

```bash
# In .env
CORS_ORIGINS=http://localhost:3000,https://myapp.com
```

The server includes proper MCP headers:
- `mcp-protocol-version`
- `mcp-session-id`

## SSL/TLS Setup

For production HTTPS, use a reverse proxy like Nginx:

```nginx
server {
    listen 443 ssl;
    server_name sheets-mcp.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Health Endpoint

`GET /health` returns:

```json
{
  "status": "healthy",
  "service": "google-sheets-mcp",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "credentials_configured": true,
  "tools_count": 20
}
```

### Readiness Endpoint

`GET /ready` returns:
- `200` with `{"status": "ready"}` when ready
- `503` with reason when not ready

### Logging

Logs are structured with timestamps:

```
2024-01-15 10:30:45 - google-sheets-mcp - INFO - Creating spreadsheet: Budget 2024
```

Configure log level:

```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Troubleshooting

### Server Won't Start

1. Check Python version (>= 3.10 required)
2. Verify dependencies: `pip list | grep fastmcp`
3. Check environment variables in `.env`

### OAuth Errors

1. Verify `gcp-oauth.keys.json` exists in credentials directory
2. Delete `sheets-token.json` and re-authenticate
3. Check OAuth consent screen configuration

### Connection Refused (HTTP)

1. Verify server is running: `./scripts/health_check.sh`
2. Check firewall rules for port 8000
3. Verify `MCP_HOST` and `MCP_PORT` settings

### CORS Errors

1. Add your origin to `CORS_ORIGINS` in `.env`
2. Restart the server
3. Check browser console for specific blocked headers
