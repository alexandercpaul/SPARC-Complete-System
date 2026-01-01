# MCP Memory Extension - Usage Examples

## Example 1: Store Conversation History

```python
import requests

API_KEY = "mcp-dev-key-change-in-production"
BASE_URL = "http://127.0.0.1:3000"

# Store a conversation turn
response = requests.post(
    f"{BASE_URL}/v1/ingest",
    headers={"api-key": API_KEY, "Content-Type": "application/json"},
    json={
        "content": """
User: How do I implement a REST API in Python?

Claude: Here's a complete example using FastAPI:

1. Install FastAPI: pip install fastapi uvicorn
2. Create app.py:
   ```python
   from fastapi import FastAPI

   app = FastAPI()

   @app.get("/")
   def read_root():
       return {"message": "Hello World"}
   ```
3. Run: uvicorn app:app --reload

This creates a simple API server with auto-generated docs at /docs.
        """,
        "source_type": "conversation",
        "source_name": "python-api-discussion",
        "session_id": "2025-12-31-coding-session",
        "user_id": "alexandercpaul@gmail.com",
        "metadata": {
            "topic": "python",
            "subtopic": "fastapi",
            "importance": "high"
        }
    }
)

print(f"Stored {response.json()['chunks_stored']} chunks")
```

## Example 2: Retrieve Relevant Context

```python
# Later in the session, ask a related question
response = requests.post(
    f"{BASE_URL}/v1/retrieve",
    headers={"api-key": API_KEY, "Content-Type": "application/json"},
    json={
        "query": "How do I add authentication to my API?",
        "session_id": "2025-12-31-coding-session",
        "user_id": "alexandercpaul@gmail.com",
        "top_k": 3,
        "max_tokens": 2000
    }
)

# The system will retrieve the FastAPI conversation
# as it's semantically related to the new query
for chunk in response.json()['chunks']:
    print(f"Relevance: {chunk['relevance_score']:.3f}")
    print(f"Source: {chunk['source_name']}")
    print(f"Content: {chunk['text'][:200]}...\n")
```

## Example 3: Index Code Files

```python
from pathlib import Path

def index_codebase(directory, session_id):
    """Index all Python files in a directory"""
    for py_file in Path(directory).rglob("*.py"):
        with open(py_file) as f:
            content = f.read()

        requests.post(
            f"{BASE_URL}/v1/ingest",
            headers={"api-key": API_KEY},
            json={
                "content": content,
                "source_type": "file",
                "source_name": str(py_file.name),
                "session_id": session_id,
                "user_id": "alexandercpaul@gmail.com",
                "metadata": {
                    "file_type": "python",
                    "full_path": str(py_file),
                    "size": len(content)
                }
            }
        )
        print(f"Indexed: {py_file.name}")

# Index your project
index_codebase("~/projects/my-api", "project-index")
```

## Example 4: Smart Code Search

```python
# Find code examples related to database connections
response = requests.post(
    f"{BASE_URL}/v1/retrieve",
    headers={"api-key": API_KEY},
    json={
        "query": "database connection pooling example",
        "session_id": "project-index",
        "user_id": "alexandercpaul@gmail.com",
        "top_k": 5,
        "filter_metadata": {
            "file_type": "python"
        }
    }
)

# Get formatted context for Claude
from context_optimizer import ContextOptimizer
optimizer = ContextOptimizer()
formatted = optimizer.format_for_prompt(response.json()['chunks'])
print(formatted)
```

## Example 5: Session-Based Memory

```python
# Store context across multiple interactions
session_id = "debugging-session-001"

# First interaction
requests.post(f"{BASE_URL}/v1/ingest", headers={"api-key": API_KEY}, json={
    "content": "Error: TypeError: 'NoneType' object is not subscriptable in line 42",
    "source_type": "error",
    "source_name": "app.py",
    "session_id": session_id,
    "user_id": "alexandercpaul@gmail.com"
})

# Later, retrieve all debugging context
response = requests.post(f"{BASE_URL}/v1/retrieve", headers={"api-key": API_KEY}, json={
    "query": "what errors have we seen?",
    "session_id": session_id,
    "user_id": "alexandercpaul@gmail.com",
    "filter_metadata": {"source_type": "error"}
})
```

## Example 6: Multi-Session Knowledge

```python
# Store general knowledge that applies across sessions
requests.post(f"{BASE_URL}/v1/ingest", headers={"api-key": API_KEY}, json={
    "content": """
    Project Conventions:
    - Use FastAPI for all REST APIs
    - PostgreSQL for databases
    - JWT for authentication
    - pytest for testing
    - Black for code formatting
    """,
    "source_type": "documentation",
    "source_name": "project-conventions.md",
    "session_id": "global-knowledge",
    "user_id": "alexandercpaul@gmail.com",
    "metadata": {"category": "conventions"}
})

# Retrieve from any session
def get_conventions():
    response = requests.post(f"{BASE_URL}/v1/retrieve", headers={"api-key": API_KEY}, json={
        "query": "what are our project conventions?",
        "session_id": "global-knowledge",
        "user_id": "alexandercpaul@gmail.com"
    })
    return response.json()['chunks'][0]['text']
```

## Example 7: Automatic Workspace Indexing

```python
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WorkspaceIndexer(FileSystemEventHandler):
    def __init__(self, session_id):
        self.session_id = session_id

    def on_modified(self, event):
        if event.src_path.endswith(('.py', '.md', '.js', '.ts')):
            with open(event.src_path) as f:
                content = f.read()

            requests.post(f"{BASE_URL}/v1/ingest", headers={"api-key": API_KEY}, json={
                "content": content,
                "source_type": "file",
                "source_name": event.src_path,
                "session_id": self.session_id,
                "user_id": "alexandercpaul@gmail.com",
                "metadata": {"auto_indexed": True}
            })
            print(f"Auto-indexed: {event.src_path}")

# Watch workspace
observer = Observer()
observer.schedule(WorkspaceIndexer("workspace-auto"), path="./src", recursive=True)
observer.start()
```

## Example 8: Context-Aware Prompting

```python
def ask_claude_with_context(question, session_id):
    """Get relevant context and format for Claude"""

    # Retrieve context
    context_response = requests.post(f"{BASE_URL}/v1/retrieve", headers={"api-key": API_KEY}, json={
        "query": question,
        "session_id": session_id,
        "user_id": "alexandercpaul@gmail.com",
        "top_k": 5,
        "max_tokens": 3000
    })

    chunks = context_response.json()['chunks']

    # Build prompt with context
    context_text = "\n\n".join([
        f"[{chunk['source_name']}]\n{chunk['text']}"
        for chunk in chunks
    ])

    prompt = f"""
Here's relevant context from our previous work:

{context_text}

---

Based on this context, {question}
    """

    return prompt

# Use it
prompt = ask_claude_with_context(
    "how should I structure my authentication module?",
    "2025-12-31-coding-session"
)
print(prompt)
```

## Example 9: Memory Statistics

```python
# Get system statistics
response = requests.get(
    f"{BASE_URL}/v1/stats",
    headers={"api-key": API_KEY}
)

stats = response.json()['stats']
print(f"Total chunks: {stats['total_chunks']}")
print(f"Embedding model: {stats['embedding_model']}")
print(f"Embedding dimension: {stats['embedding_dim']}")
```

## Example 10: Clear Old Sessions

```python
# Clear specific session
requests.post(f"{BASE_URL}/v1/clear", headers={"api-key": API_KEY}, json={
    "session_id": "old-session-001",
    "user_id": "alexandercpaul@gmail.com"
})

# Clear all user data
requests.post(f"{BASE_URL}/v1/clear", headers={"api-key": API_KEY}, json={
    "user_id": "alexandercpaul@gmail.com"
})
```

## Integration Pattern: Claude Code Session

```python
class ClaudeCodeSession:
    def __init__(self, session_id):
        self.session_id = session_id
        self.api_key = "mcp-dev-key-change-in-production"
        self.base_url = "http://127.0.0.1:3000"

    def remember(self, content, source_name, metadata=None):
        """Store something in memory"""
        requests.post(f"{self.base_url}/v1/ingest",
            headers={"api-key": self.api_key},
            json={
                "content": content,
                "source_type": "conversation",
                "source_name": source_name,
                "session_id": self.session_id,
                "user_id": "alexandercpaul@gmail.com",
                "metadata": metadata or {}
            }
        )

    def recall(self, query, top_k=5):
        """Retrieve relevant memories"""
        response = requests.post(f"{self.base_url}/v1/retrieve",
            headers={"api-key": self.api_key},
            json={
                "query": query,
                "session_id": self.session_id,
                "user_id": "alexandercpaul@gmail.com",
                "top_k": top_k
            }
        )
        return response.json()['chunks']

# Usage
session = ClaudeCodeSession("2025-12-31-deployment")
session.remember("Successfully deployed MCP Memory Extension", "deployment-log")
memories = session.recall("what did we deploy today?")
```
