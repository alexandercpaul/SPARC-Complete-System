#!/usr/bin/env python3
"""
MCP Memory Extension Server Launcher
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from server import start_server

def load_config():
    """Load configuration"""
    config_path = Path(__file__).parent / "config" / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}

if __name__ == "__main__":
    config = load_config()
    server_config = config.get("server", {})

    host = server_config.get("host", "127.0.0.1")
    port = server_config.get("port", 3000)

    print(f"""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           MCP Memory Extension Server v1.0.0               ║
║                                                            ║
║  Semantic memory and context management for Claude Code   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝

🚀 Starting server on http://{host}:{port}

📚 API Endpoints:
   - POST /v1/ingest      - Ingest context into memory
   - POST /v1/retrieve    - Retrieve relevant context
   - POST /v1/clear       - Clear memory
   - GET  /v1/stats       - Get statistics
   - GET  /health         - Health check

🔑 API Key: {server_config.get('api_key', 'mcp-dev-key-change-in-production')}

💾 Data Directory: ~/.mcp-memory/

Press Ctrl+C to stop the server
    """)

    start_server(host=host, port=port)
