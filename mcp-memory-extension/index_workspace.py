#!/usr/bin/env python3
"""
Index SPARC workspace files into MCP Memory Extension
Automatically indexes all session directories and files
"""
import requests
import json
from pathlib import Path
from datetime import datetime

# Configuration
API_KEY = "mcp-dev-key-change-in-production"
BASE_URL = "http://127.0.0.1:3000"
USER_ID = "alexandercpaul@gmail.com"

# Workspace path
WORKSPACE = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp"

def index_file(file_path: Path, session_id: str, source_type: str = "file"):
    """Index a single file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        if not content.strip():
            return False

        response = requests.post(
            f"{BASE_URL}/v1/ingest",
            headers={
                "api-key": API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "content": content,
                "source_type": source_type,
                "source_name": file_path.name,
                "session_id": session_id,
                "user_id": USER_ID,
                "metadata": {
                    "full_path": str(file_path),
                    "file_type": file_path.suffix[1:] if file_path.suffix else "unknown",
                    "indexed_at": datetime.now().isoformat(),
                    "auto_indexed": True
                }
            }
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("chunks_stored", 0)
        else:
            print(f"  ⚠️  Error indexing {file_path.name}: {response.status_code}")
            return False

    except Exception as e:
        print(f"  ❌ Failed to index {file_path.name}: {str(e)}")
        return False

def index_session_directory(session_dir: Path):
    """Index all files in a session directory"""
    print(f"\n📁 Indexing {session_dir.name}...")

    # File patterns to index
    patterns = ["*.md", "*.py", "*.js", "*.ts", "*.json", "*.txt"]

    total_files = 0
    total_chunks = 0

    for pattern in patterns:
        for file_path in session_dir.glob(pattern):
            if file_path.is_file():
                chunks = index_file(file_path, session_dir.name, "file")
                if chunks:
                    total_files += 1
                    total_chunks += chunks
                    print(f"  ✅ {file_path.name} ({chunks} chunks)")

    return total_files, total_chunks

def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                                                            ║")
    print("║        MCP Memory Extension - Workspace Indexer            ║")
    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ Server is not responding. Start it with: ./quickstart.sh")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Start it with: ./quickstart.sh")
        return

    print(f"🔍 Scanning workspace: {WORKSPACE}")
    print()

    if not WORKSPACE.exists():
        print(f"❌ Workspace not found: {WORKSPACE}")
        return

    # Find session directories
    session_patterns = [
        "claude-session-*",
        "gemini-task-*",
        "codex-task-*",
        "ollama-runs-*",
        "mcp-deployment-*"
    ]

    total_sessions = 0
    total_files = 0
    total_chunks = 0

    for pattern in session_patterns:
        for session_dir in WORKSPACE.glob(pattern):
            if session_dir.is_dir():
                files, chunks = index_session_directory(session_dir)
                total_sessions += 1
                total_files += files
                total_chunks += chunks

    print()
    print("=" * 60)
    print(f"✅ Indexing complete!")
    print(f"   Sessions indexed: {total_sessions}")
    print(f"   Files indexed:    {total_files}")
    print(f"   Chunks stored:    {total_chunks}")
    print("=" * 60)
    print()

    # Get current stats
    response = requests.get(
        f"{BASE_URL}/v1/stats",
        headers={"api-key": API_KEY}
    )

    if response.status_code == 200:
        stats = response.json()["stats"]
        print("📊 Memory Statistics:")
        print(f"   Total chunks in memory: {stats['total_chunks']}")
        print(f"   Embedding model: {stats['embedding_model']}")
        print(f"   Embedding dimension: {stats['embedding_dim']}")
        print()

    print("💡 Try querying your indexed data:")
    print("   python test_client.py")
    print()
    print("   Or use the API directly:")
    print(f'   curl -X POST {BASE_URL}/v1/retrieve \\')
    print(f'     -H "api-key: {API_KEY}" \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"query": "What did we work on today?", "session_id": "workspace-auto", "user_id": "{USER_ID}"}}\'')
    print()

if __name__ == "__main__":
    main()
