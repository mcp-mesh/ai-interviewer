#!/bin/bash
# Script to check telemetry data in Redis
# Run this after services are deployed and running

echo "🔍 Checking telemetry data in Redis..."
echo "====================================="

# Check Redis connection
echo "1. Testing Redis connection..."
docker exec ai-interviewer-redis redis-cli ping

# Check for trace keys
echo ""
echo "2. Looking for trace keys in Redis..."
docker exec ai-interviewer-redis redis-cli --scan --pattern "*trace*" | head -10

# Check for execution trace keys
echo ""
echo "3. Looking for execution trace keys..."
docker exec ai-interviewer-redis redis-cli --scan --pattern "*execution*" | head -10

# Check for telemetry keys
echo ""
echo "4. Looking for telemetry keys..."
docker exec ai-interviewer-redis redis-cli --scan --pattern "*telemetry*" | head -10

# Show all keys with pattern matching
echo ""
echo "5. All MCP Mesh related keys..."
docker exec ai-interviewer-redis redis-cli --scan --pattern "*mcp*" | head -20

# Show recent trace entries (if any exist)
echo ""
echo "6. Sample trace data (if available)..."
TRACE_KEY=$(docker exec ai-interviewer-redis redis-cli --scan --pattern "*trace*" | head -1)
if [ -n "$TRACE_KEY" ]; then
    echo "Found trace key: $TRACE_KEY"
    docker exec ai-interviewer-redis redis-cli get "$TRACE_KEY" | head -5
else
    echo "No trace keys found yet. Make sure services are processing requests."
fi

echo ""
echo "✅ Telemetry check complete!"
echo ""
echo "📋 To generate telemetry data:"
echo "  1. Make API calls to http://localhost/api/..."
echo "  2. Use the interview system to trigger MCP agent calls"  
echo "  3. Run this script again to see telemetry data"
echo ""
echo "📊 Telemetry is enabled for:"
echo "  - fastapi service (API routes with @mesh.route)"
echo "  - pdf-extractor agent (MCP tools with @mesh.tool)"
echo "  - llm-agent (MCP tools with @mesh.tool)"
echo "  - openai-llm-agent (MCP tools with @mesh.tool)"
echo "  - interview-agent (MCP tools with @mesh.tool)"
echo "  - registry service (coordination telemetry)"