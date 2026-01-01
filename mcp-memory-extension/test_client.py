#!/usr/bin/env python3
"""
Test client for MCP Memory Extension
Demonstrates ingestion and retrieval
"""
import requests
import json
from datetime import datetime

# Server configuration
BASE_URL = "http://127.0.0.1:3000"
API_KEY = "mcp-dev-key-change-in-production"

headers = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_ingest():
    """Test ingestion"""
    print("📝 Testing ingestion...")

    # Test data
    test_content = """
    This is a test document about MCP Memory Extension.

    The MCP Memory Extension provides semantic memory for Claude Code.
    It uses ChromaDB for vector storage and supports conversation history,
    code context, and custom content types.

    Key features:
    - Semantic search using vector embeddings
    - Automatic chunking and deduplication
    - Session and user isolation
    - Token budget optimization
    """

    data = {
        "content": test_content,
        "source_type": "documentation",
        "source_name": "test_doc.md",
        "session_id": "test-session-001",
        "user_id": "test-user",
        "metadata": {
            "category": "system",
            "importance": "high"
        }
    }

    response = requests.post(
        f"{BASE_URL}/v1/ingest",
        headers=headers,
        json=data
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

def test_retrieve():
    """Test retrieval"""
    print("🔎 Testing retrieval...")

    data = {
        "query": "What features does MCP Memory Extension have?",
        "session_id": "test-session-001",
        "user_id": "test-user",
        "top_k": 3,
        "max_tokens": 1000
    }

    response = requests.post(
        f"{BASE_URL}/v1/retrieve",
        headers=headers,
        json=data
    )

    print(f"Status: {response.status_code}")
    result = response.json()

    print(f"Found {len(result['chunks'])} chunks:")
    print(f"Total tokens: {result['total_tokens']}")
    print(f"Query time: {result['query_time_ms']}ms\n")

    for i, chunk in enumerate(result['chunks'], 1):
        print(f"--- Chunk {i} (relevance: {chunk['relevance_score']:.3f}) ---")
        print(chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'])
        print()

def test_stats():
    """Test statistics"""
    print("📊 Testing statistics...")

    response = requests.get(
        f"{BASE_URL}/v1/stats",
        headers=headers
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║          MCP Memory Extension Test Client                  ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)

    try:
        test_health()
        test_ingest()
        test_retrieve()
        test_stats()

        print("✅ All tests completed successfully!")

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server. Is it running?")
        print("   Start server with: python start_server.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
