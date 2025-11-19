# Google Sheets MCP Server

A FastMCP server providing comprehensive Google Sheets operations including formulas, formatting, charts, data validation, and more.

## Features

**20 Tools** for complete spreadsheet management:

### Basic Data Operations
- `sheets_create` - Create new spreadsheets
- `sheets_read` - Read data from ranges
- `sheets_write` - Write data with formula support (=SUM, =VLOOKUP, etc.)
- `sheets_append` - Append rows to sheets
- `sheets_get_sheet_id` - Get sheet ID by name
- `sheets_delete_rows` - Delete rows
- `sheets_insert_rows` - Insert blank rows
- `sheets_clear_range` - Clear cell contents
- `sheets_find_replace` - Find and replace text
- `sheets_duplicate_sheet` - Duplicate sheets
- `sheets_delete_duplicates` - Remove duplicate rows
- `sheets_trim_whitespace` - Clean cell whitespace
- `sheets_merge_cells` - Merge cell ranges
- `sheets_copy_paste` - Copy and paste ranges

### Formatting
- `sheets_format_cells` - Apply formatting (bold, italic, colors)
- `sheets_add_borders` - Add cell borders

### Charts
- `sheets_add_chart` - Create charts (column, bar, line, pie, scatter)

### Data Validation
- `sheets_add_dropdown` - Add dropdown lists
- `sheets_conditional_format` - Apply conditional formatting
- `sheets_sort_range` - Sort data ranges

## Quick Start

### 1. Install

```bash
cd google-sheets
./scripts/install.sh

# Or manually
pip install -e .
```

### 2. Configure Google OAuth

Create credentials at [Google Cloud Console](https://console.cloud.google.com/):

1. Enable Google Sheets API
2. Configure OAuth consent screen
3. Create OAuth Client ID (Desktop app)
4. Download credentials as `gcp-oauth.keys.json`

```bash
mkdir -p ~/.config/mcp-gdrive
mv gcp-oauth.keys.json ~/.config/mcp-gdrive/
```

Full setup guide: [docs/setup/GOOGLE_OAUTH_SETUP.md](docs/setup/GOOGLE_OAUTH_SETUP.md)

### 3. Start the Server

```bash
# STDIO mode (for IDE integration)
./scripts/start.sh

# HTTP mode (for web access)
./scripts/start.sh http
```

## Deployment Options

### STDIO Transport (IDE Integration)

Best for: Claude Desktop, Cursor, Claude Code

```bash
python src/server.py
```

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/path/to/google-sheets",
        "python", "src/server.py"
      ],
      "env": {
        "GDRIVE_CREDS_DIR": "~/.config/mcp-gdrive"
      }
    }
  }
}
```

**Cursor** (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "uv",
      "args": [
        "run",
        "--project", "/path/to/google-sheets",
        "python", "src/server.py"
      ],
      "env": {
        "GDRIVE_CREDS_DIR": "~/.config/mcp-gdrive"
      }
    }
  }
}
```

**Claude Code**:

```bash
fastmcp install claude-code src/server.py
# or
claude mcp add google-sheets -- uv run --project /path/to/google-sheets python src/server.py
```

### HTTP Transport (Web/API)

Best for: Multiple clients, remote access, API integration

```bash
# Development
python src/server_http.py http

# Production
uvicorn src.server_http:app --host 0.0.0.0 --port 8000 --workers 4
```

**Endpoints:**
- `POST /mcp/` - MCP protocol endpoint
- `GET /health` - Health check
- `GET /ready` - Readiness check

**Health Check:**

```bash
curl http://localhost:8000/health
```

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

## Environment Variables

```bash
# Google OAuth (required)
GDRIVE_CREDS_DIR=~/.config/mcp-gdrive

# HTTP Transport (optional)
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_WORKERS=4

# CORS (optional)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Logging (optional)
LOG_LEVEL=INFO
```

Copy `.env.example` to `.env` and configure.

## Directory Structure

```
google-sheets/
  src/
    server.py          # STDIO server
    server_http.py     # HTTP server with production features
  configs/
    claude_desktop_config.json
    cursor_config.json
    claude_code_config.json
  scripts/
    start.sh           # Start script
    install.sh         # Installation script
    health_check.sh    # Health check script
  docs/
    deployment/
      DEPLOYMENT.md    # Full deployment guide
    setup/
      GOOGLE_OAUTH_SETUP.md  # OAuth setup guide
  tests/
    test_server.py     # Test suite
  .env.example         # Environment template
  fastmcp.json         # FastMCP manifest
  pyproject.toml       # Project configuration
```

## Production Deployment

### CORS Configuration

For browser-based clients:

```bash
CORS_ORIGINS=http://localhost:3000,https://myapp.com
```

### SSL/TLS

Use Nginx as a reverse proxy for HTTPS:

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
    }
}
```

### Docker

```bash
docker build -t google-sheets-mcp .
docker run -p 8000:8000 \
  -v ~/.config/mcp-gdrive:/root/.config/mcp-gdrive \
  google-sheets-mcp
```

### Systemd

See [docs/deployment/DEPLOYMENT.md](docs/deployment/DEPLOYMENT.md) for systemd service configuration.

## Security Considerations

1. **OAuth Credentials**: Keep `gcp-oauth.keys.json` secure and never commit to git
2. **Token Storage**: `sheets-token.json` contains access tokens - protect it
3. **CORS**: Restrict origins to your trusted domains
4. **Production**: Use service accounts for server-to-server communication

## Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=src
```

## Example Usage

After connecting via MCP client:

```python
# Create a spreadsheet
result = await sheets_create(title="Budget 2024", sheet_titles=["Income", "Expenses"])

# Write data with formulas
await sheets_write(
    spreadsheet_id="...",
    range="Income!A1:B5",
    values=[
        ["Month", "Amount"],
        ["January", "5000"],
        ["February", "5500"],
        ["March", "6000"],
        ["Total", "=SUM(B2:B4)"]
    ]
)

# Format header row
await sheets_format_cells(
    spreadsheet_id="...",
    sheet_id=0,
    start_row=0, end_row=1,
    start_col=0, end_col=2,
    bold=True, bg_color="#4285F4", text_color="#FFFFFF"
)

# Add a chart
await sheets_add_chart(
    spreadsheet_id="...",
    sheet_id=0,
    chart_type="COLUMN",
    data_range="Income!A1:B4",
    title="Monthly Income"
)
```

## Documentation

- [Deployment Guide](docs/deployment/DEPLOYMENT.md)
- [Google OAuth Setup](docs/setup/GOOGLE_OAUTH_SETUP.md)
- [Testing Guide](TESTING.md)

## Dependencies

- Python >= 3.10
- fastmcp >= 2.0.0
- google-auth >= 2.29.0
- google-auth-oauthlib >= 1.2.0
- google-api-python-client >= 2.122.0
- python-dotenv >= 1.0.0

## License

MIT
