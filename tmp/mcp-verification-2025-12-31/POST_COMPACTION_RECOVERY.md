# Post-Compaction Recovery Checklist

**Date**: 2025-12-31
**Purpose**: Quick recovery steps for Claude after compaction

---

## Immediate Actions (First 30 seconds)

### 1. Check Server Status
```bash
curl http://127.0.0.1:3000/health
```

**Expected**: `{"status":"healthy","service":"mcp-memory-extension","version":"1.0.0",...}`

---

### 2. If Server Down, Restart
```bash
cd ~/mcp-servers/memory-extension
./quickstart.sh
```

**Wait**: 3-5 seconds, then test health endpoint again

---

### 3. Retrieve Session Context
```bash
curl -s http://127.0.0.1:3000/v1/retrieve \
  -X POST \
  -H "api-key: mcp-dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did we accomplish today?",
    "session_id": "2025-12-31-main-session",
    "user_id": "alexandercpaul@gmail.com",
    "top_k": 5,
    "max_tokens": 3000
  }' | python3 -m json.tool
```

**Expected**: Should return 8 chunks about today's work

---

## Verification Checklist

- [ ] Server responding on http://127.0.0.1:3000/health
- [ ] Stats show 8 chunks stored
- [ ] Can retrieve "PRE-COMPACTION VERIFICATION TEST"
- [ ] Vector store exists at ~/.mcp-memory/vector_store.pkl (16 KB)
- [ ] Server running from iCloud location (PID 75342 or new)

---

## Quick Stats Check
```bash
curl -s -H "api-key: mcp-dev-key-change-in-production" \
  http://127.0.0.1:3000/v1/stats | python3 -m json.tool
```

**Expected**:
```json
{
    "total_chunks": 8,
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dim": 384,
    "storage_type": "in-memory (numpy)",
    "chunk_size": 512,
    "chunk_overlap": 50
}
```

---

## If Something Went Wrong

### Server Won't Start
1. Check if port 3000 is in use: `lsof -i :3000`
2. Kill old process: `pkill -f start_server.py`
3. Restart: `cd ~/mcp-servers/memory-extension && ./quickstart.sh`

### Data Missing
1. Check vector store: `ls -lh ~/.mcp-memory/vector_store.pkl`
2. Should be ~16 KB with timestamp Dec 31 12:26
3. If missing, data was not persisted (very unlikely)

### Dependencies Broken
```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension
source venv/bin/activate
pip install -r requirements.txt
```

---

## Recovery Success Indicators

✅ **All Good If**:
1. Health endpoint returns 200 OK
2. Stats show 8+ chunks
3. Can retrieve test data with high relevance score (>0.8)
4. Server running from iCloud location
5. Query time under 100ms

---

## Documentation Locations

**Full Technical Report**:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/mcp-verification-2025-12-31/MCP_TECHNICAL_VERIFICATION.md
```

**Usage Guide**:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension/HOW_TO_USE_AFTER_COMPACTION.md
```

**Configuration**:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension/config/config.json
```

---

## Test Queries to Restore Context

Ask Claude:
1. "What did we build today?"
2. "Check MCP Memory for today's accomplishments"
3. "Retrieve context about the Google 30TB storage research"
4. "What's the status of the Instacart automation?"
5. "Show me what's in the MCP Memory Extension"

Claude should automatically query the memory extension and show you stored context.

---

**Created**: 2025-12-31 17:29
**Status**: Ready for post-compaction recovery
**Next Step**: `/compact` when ready!
