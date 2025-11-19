#!/bin/bash
# Google Sheets MCP Server - Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Installing Google Sheets MCP Server..."
echo "Project: $PROJECT_DIR"

# Check for uv
if command -v uv &> /dev/null; then
    echo "Using uv for installation..."
    cd "$PROJECT_DIR" && uv pip install -e .
else
    echo "Using pip for installation..."
    cd "$PROJECT_DIR" && pip install -e .
fi

echo ""
echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Set up Google Cloud credentials (see docs/setup/GOOGLE_OAUTH_SETUP.md)"
echo "2. Configure your credentials directory:"
echo "   export GDRIVE_CREDS_DIR=~/.config/mcp-gdrive"
echo "3. Start the server:"
echo "   ./scripts/start.sh          # STDIO mode"
echo "   ./scripts/start.sh http     # HTTP mode"
