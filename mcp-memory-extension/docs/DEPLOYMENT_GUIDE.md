# MCP Memory Extension - Deployment Guide

## Overview

The MCP Memory Extension provides semantic memory and context management for Claude Code, enabling unlimited context through vector-based semantic search.

## What Was Deployed

### Components

1. **FastAPI Server** (`src/server.py`)
   - REST API with endpoints for ingestion, retrieval, and management
   - Runs on http://127.0.0.1:3000

2. **Vector Store** (`src/vector_store.py`)
   - Numpy-based in-memory vector storage with persistence
   - Uses sentence-transformers for embeddings (all-MiniLM-L6-v2)
   - 384-dimensional embeddings with cosine similarity search

3. **Memory Manager** (`src/memory_manager.py`)
   - Automatic text chunking (512 chars with 50 char overlap)
   - Secret redaction for API keys, passwords, tokens
   - Session and user isolation

4. **Context Optimizer** (`src/context_optimizer.py`)
   - Token budget management
   - Relevance-based selection
   - Context formatting for prompts

### Installation Location

```
~/mcp-servers/memory-extension/
├── config/
│   └── config.json              # Configuration
├── docs/
│   └── DEPLOYMENT_GUIDE.md      # This file
├── src/
│   ├── __init__.py
│   ├── server.py                # FastAPI server
│   ├── vector_store.py          # Vector storage
│   ├── memory_manager.py        # Memory management
│   └── context_optimizer.py     # Context optimization
├── venv/                        # Python virtual environment
├── requirements.txt             # Dependencies
├── start_server.py             # Server launcher
└── test_client.py              # Test client
```

### Data Storage

- **Vector Store**: `~/.mcp-memory/vector_store.pkl`
- **Configuration**: `~/mcp-servers/memory-extension/config/config.json`
- **Server Logs**: `~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-deployment-2025-12-31-1156/server.log`

## Server Status

### Check if Running

```bash
ps aux | grep start_server.py
```

### View Logs

```bash
tail -f ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-deployment-2025-12-31-1156/server.log
```

### Stop Server

```bash
kill $(cat ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-deployment-2025-12-31-1156/server.pid)
```

### Restart Server

```bash
cd ~/mcp-servers/memory-extension
source venv/bin/activate
nohup python start_server.py > ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-deployment-2025-12-31-1156/server.log 2>&1 &
echo $! > ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-deployment-2025-12-31-1156/server.pid
```

## API Endpoints

### 1. Health Check

```bash
curl http://127.0.0.1:3000/health
```

### 2. Ingest Context

```bash
curl -X POST http://127.0.0.1:3000/v1/ingest \
  -H "api-key: mcp-dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your content here...",
    "source_type": "conversation",
    "source_name": "chat-2025-12-31",
    "session_id": "session-001",
    "user_id": "alexandercpaul@gmail.com"
  }'
```

### 3. Retrieve Context

```bash
curl -X POST http://127.0.0.1:3000/v1/retrieve \
  -H "api-key: mcp-dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did we discuss?",
    "session_id": "session-001",
    "user_id": "alexandercpaul@gmail.com",
    "top_k": 5,
    "max_tokens": 2000
  }'
```

### 4. Get Statistics

```bash
curl http://127.0.0.1:3000/v1/stats \
  -H "api-key: mcp-dev-key-change-in-production"
```

### 5. Clear Memory

```bash
curl -X POST http://127.0.0.1:3000/v1/clear \
  -H "api-key: mcp-dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session-001",
    "user_id": "alexandercpaul@gmail.com"
  }'
```

## Configuration

Edit `~/mcp-servers/memory-extension/config/config.json`:

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 3000,
    "api_key": "your-secure-api-key-here"
  },
  "memory": {
    "chunk_size": 512,
    "chunk_overlap": 50,
    "max_tokens_default": 4000
  },
  "workspace": {
    "index_path": "~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp",
    "auto_index_sessions": true
  }
}
```

## Integration with Claude Code

### Option 1: Manual API Calls

Use curl or HTTP client to store and retrieve context during coding sessions.

### Option 2: Automation Script

Create a script to automatically index workspace directories:

```python
#!/usr/bin/env python3
import os
import requests
from pathlib import Path

API_KEY = "mcp-dev-key-change-in-production"
BASE_URL = "http://127.0.0.1:3000"

def index_file(file_path, session_id):
    with open(file_path) as f:
        content = f.read()

    requests.post(
        f"{BASE_URL}/v1/ingest",
        headers={"api-key": API_KEY},
        json={
            "content": content,
            "source_type": "file",
            "source_name": str(file_path),
            "session_id": session_id,
            "user_id": "alexandercpaul@gmail.com"
        }
    )

# Index all markdown files in workspace
workspace = Path("~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp").expanduser()
for md_file in workspace.rglob("*.md"):
    index_file(md_file, "workspace-index")
```

### Option 3: Claude Code Integration (Future)

When MCP server protocol support is added, configure in `~/.claude/mcp_servers.json`.

## Performance

- **Ingestion**: ~400ms per document (including embedding generation)
- **Retrieval**: ~22ms for semantic search
- **Storage**: Persistent to disk, fast in-memory search
- **Embedding Model**: 384-dimensional vectors, 68M parameters

## Security Notes

1. **Change API Key**: Update `config/config.json` with a secure key
2. **Local Only**: Server binds to 127.0.0.1 (localhost only)
3. **Secret Redaction**: Automatic redaction of API keys, passwords, tokens in stored content
4. **User Isolation**: Queries filtered by user_id and session_id

## Testing

Run the test client:

```bash
cd ~/mcp-servers/memory-extension
source venv/bin/activate
python test_client.py
```

## Troubleshooting

### Server Won't Start

1. Check if port 3000 is already in use: `lsof -i :3000`
2. View logs for errors
3. Ensure virtual environment is activated

### Import Errors

```bash
cd ~/mcp-servers/memory-extension
source venv/bin/activate
pip install -r requirements.txt
```

### Memory Issues

Clear the vector store:

```bash
rm ~/.mcp-memory/vector_store.pkl
```

## Next Steps

1. **Auto-Index Workspace**: Set up cron job or file watcher to automatically index session files
2. **Claude Code Integration**: Wait for official MCP server protocol support
3. **Advanced Features**: Add re-ranking, hybrid search, automatic summarization
4. **Production Deployment**: Add authentication, monitoring, backups

## Support

- Email: alexandercpaul@gmail.com
- Deployment workspace: `~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-deployment-2025-12-31-1156/`
