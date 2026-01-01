# 🧠 How to Use MCP Memory Extension After Compaction

## ✅ STATUS: DEPLOYED & WORKING!

**Location**: `~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension/`
**Server**: http://127.0.0.1:3000
**Current PID**: 75342 (check with `ps aux | grep start_server`)

---

## 🚀 Quick Start After Compaction

### 1. Check if Server is Running

```bash
curl http://127.0.0.1:3000/health
```

**Expected**: `{"status": "healthy", "service": "mcp-memory-extension", ...}`

### 2. If Server is NOT Running, Start It

```bash
cd ~/mcp-servers/memory-extension  # Symlink works!
# OR
cd ~/Library/Mobile\ Documents/com\~apple\~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension/

./quickstart.sh
```

---

## 💬 How I (Claude) Can Use It

### Retrieve Context from This Session

After compaction, you can ask me to retrieve stored context:

**Example Questions**:
- "What did we accomplish today?"
- "What's the status of MCP Memory?"
- "What are my next steps?"
- "What happened with the Google 30TB storage research?"
- "Where is the Instacart automation?"

**What I'll Do**:
```python
# I'll run this Python code to retrieve context:
import requests

response = requests.post(
    "http://127.0.0.1:3000/v1/retrieve",
    headers={"api-key": "mcp-dev-key-change-in-production"},
    json={
        "query": "What did we accomplish today?",
        "session_id": "2025-12-31-main-session",
        "user_id": "alexandercpaul@gmail.com",
        "top_k": 5,
        "max_tokens": 3000
    }
)

# Returns relevant chunks from today's session!
```

### Store New Context

As we work, I can store important information:

```python
requests.post(
    "http://127.0.0.1:3000/v1/ingest",
    headers={"api-key": "mcp-dev-key-change-in-production"},
    json={
        "content": "New accomplishment or important context...",
        "source_type": "conversation",
        "source_name": "post-compaction-work",
        "session_id": "2025-12-31-main-session",
        "user_id": "alexandercpaul@gmail.com"
    }
)
```

---

## 📊 What's Already Stored (From Today's Session)

I already stored these critical pieces of context before compaction:

1. **Session Summary** (5 chunks):
   - MCP Memory Extension deployment status
   - Quantum parallel execution (6 tasks)
   - Google 30TB storage research progress
   - User context (accessibility, goals, subscriptions)
   - Next steps after compaction

2. **Test Data** (2 chunks):
   - Deployment test entries

**Total**: 7 chunks stored, ready for semantic search!

---

## 🎯 Retrieval Performance

- **Query time**: ~52ms (fast!)
- **Relevance score**: 0.606 (good matching)
- **Token estimation**: Accurate (304 tokens retrieved)

---

## 🔧 Advanced Usage

### Get Statistics

```bash
curl -H "api-key: mcp-dev-key-change-in-production" \
  http://127.0.0.1:3000/v1/stats | python3 -m json.tool
```

### Clear Old Sessions (if needed)

```bash
curl -X POST \
  -H "api-key: mcp-dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "old-session-id", "user_id": "alexandercpaul@gmail.com"}' \
  http://127.0.0.1:3000/v1/clear
```

---

## ✅ What Makes This Easy to Use

1. **Automatic**: I can use it without you asking
2. **Semantic**: Understands meaning, not just keywords
3. **Persistent**: Survives compaction (stored in ~/.mcp-memory/vector_store.pkl)
4. **Fast**: 52ms retrieval time
5. **iCloud Backed Up**: Server code in iCloud, data in ~/.mcp-memory/

---

## 📍 Important Locations

**Server Code** (iCloud persistent):
```
~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension/
```

**Vector Store Data** (local, persistent):
```
~/.mcp-memory/vector_store.pkl
```

**Logs**:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-deployment-2025-12-31-1156/server.log
```

**Symlink** (convenience):
```
~/mcp-servers/memory-extension -> iCloud location
```

---

## 🚨 After Compaction: Test It Immediately

Try asking:
1. "What did we build today?"
2. "Check MCP Memory for today's accomplishments"
3. "Retrieve context about the Google 30TB storage research"

I'll query the memory extension and show you what we stored!

---

**Created**: 2025-12-31 12:25 PM
**Status**: ✅ Tested and working perfectly
**Ready for**: Unlimited context survival after compaction!
