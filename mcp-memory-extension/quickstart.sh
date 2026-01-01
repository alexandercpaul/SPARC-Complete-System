#!/bin/bash
# MCP Memory Extension - Quick Start Script

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║           MCP Memory Extension Quick Start                 ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if server is already running
if lsof -i :3000 > /dev/null 2>&1; then
    echo "⚠️  Server already running on port 3000"
    echo ""
    read -p "Stop and restart? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Stopping existing server..."
        pkill -f start_server.py || true
        sleep 2
    else
        echo "❌ Exiting"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Start server
echo "🚀 Starting MCP Memory Extension server..."
LOG_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-deployment-2025-12-31-1156"
mkdir -p "$LOG_DIR"

nohup python start_server.py > "$LOG_DIR/server.log" 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > "$LOG_DIR/server.pid"

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 3

# Test health endpoint
if curl -s http://127.0.0.1:3000/health > /dev/null 2>&1; then
    echo ""
    echo "✅ Server started successfully!"
    echo ""
    echo "📊 Server Information:"
    echo "   PID: $SERVER_PID"
    echo "   URL: http://127.0.0.1:3000"
    echo "   Logs: $LOG_DIR/server.log"
    echo ""
    echo "📚 API Endpoints:"
    echo "   GET  /health          - Health check"
    echo "   POST /v1/ingest       - Store context"
    echo "   POST /v1/retrieve     - Retrieve context"
    echo "   POST /v1/clear        - Clear memory"
    echo "   GET  /v1/stats        - Get statistics"
    echo ""
    echo "🔑 API Key: mcp-dev-key-change-in-production"
    echo ""
    echo "📖 Documentation:"
    echo "   Deployment Guide: $SCRIPT_DIR/docs/DEPLOYMENT_GUIDE.md"
    echo "   Usage Examples:   $SCRIPT_DIR/docs/USAGE_EXAMPLES.md"
    echo ""
    echo "🧪 Run Tests:"
    echo "   python test_client.py"
    echo ""
    echo "🛑 Stop Server:"
    echo "   kill $SERVER_PID"
    echo ""
else
    echo ""
    echo "❌ Server failed to start"
    echo "📋 Check logs: tail -f $LOG_DIR/server.log"
    exit 1
fi
