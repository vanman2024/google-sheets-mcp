#!/bin/bash
# Google Sheets MCP Server - Start Script
# Usage: ./scripts/start.sh [stdio|http]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

# Default to STDIO transport
TRANSPORT="${1:-stdio}"

echo "Starting Google Sheets MCP Server..."
echo "Transport: $TRANSPORT"
echo "Project: $PROJECT_DIR"

case "$TRANSPORT" in
    stdio)
        echo "Starting in STDIO mode..."
        cd "$PROJECT_DIR" && python src/server.py
        ;;
    http)
        HOST="${MCP_HOST:-0.0.0.0}"
        PORT="${MCP_PORT:-8000}"
        echo "Starting HTTP server on $HOST:$PORT..."
        cd "$PROJECT_DIR" && python src/server_http.py http
        ;;
    http-prod)
        HOST="${MCP_HOST:-0.0.0.0}"
        PORT="${MCP_PORT:-8000}"
        WORKERS="${MCP_WORKERS:-4}"
        echo "Starting production HTTP server on $HOST:$PORT with $WORKERS workers..."
        cd "$PROJECT_DIR" && uvicorn src.server_http:app --host "$HOST" --port "$PORT" --workers "$WORKERS"
        ;;
    *)
        echo "Unknown transport: $TRANSPORT"
        echo "Usage: $0 [stdio|http|http-prod]"
        exit 1
        ;;
esac
