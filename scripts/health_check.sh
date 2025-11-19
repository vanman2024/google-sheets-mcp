#!/bin/bash
# Google Sheets MCP Server - Health Check Script

HOST="${MCP_HOST:-localhost}"
PORT="${MCP_PORT:-8000}"

echo "Checking health of Google Sheets MCP Server..."
echo "URL: http://$HOST:$PORT/health"
echo ""

RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "http://$HOST:$PORT/health")
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d':' -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

echo "Response:"
echo "$BODY" | python -m json.tool 2>/dev/null || echo "$BODY"
echo ""

if [ "$HTTP_CODE" == "200" ]; then
    echo "Status: HEALTHY"
    exit 0
else
    echo "Status: UNHEALTHY (HTTP $HTTP_CODE)"
    exit 1
fi
