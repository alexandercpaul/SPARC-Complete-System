# MCP Memory Extension - Location Information

## ✅ PERSISTENT iCloud Location

**Primary Location** (persistent, backed up):
```
~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension/
```

**Symlink** (for convenience):
```
~/mcp-servers/memory-extension -> (points to iCloud location above)
```

## Why This Location?

**Before**: `~/mcp-servers/memory-extension/` (NOT backed up, could be lost!)
**After**: iCloud location (persistent, survives restarts, backed up automatically)

This ensures:
- ✅ Survives system restarts
- ✅ Backed up to iCloud
- ✅ Part of organized SPARC workspace
- ✅ Accessible after compaction
- ✅ Theory of Constraints applied (persistent storage)

## Quick Access

You can still use the short path thanks to the symlink:
```bash
cd ~/mcp-servers/memory-extension  # Works! (symlink)
cd ~/Library/Mobile\ Documents/com\~apple\~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension/  # Actual location
```

## Server Commands

```bash
# Start server (from either location)
cd ~/mcp-servers/memory-extension
./quickstart.sh

# Or from iCloud location
cd ~/Library/Mobile\ Documents/com\~apple\~CloudDocs/Developer/SPARC_Complete_System/mcp-memory-extension/
./quickstart.sh
```

**Updated**: 2025-12-31 12:20 PM
**Moved for**: Persistent iCloud backup and survival
