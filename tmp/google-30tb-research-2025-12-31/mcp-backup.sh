#!/bin/bash
# Automated MCP Memory backup using rclone
# Save as: ~/bin/mcp-backup.sh or run directly

set -euo pipefail

# Configuration
MCP_MEMORY_LOCAL="$HOME/.mcp-memory/"
GDRIVE_REMOTE="gdrive:mcp-memory/"
LOG_FILE="$HOME/.mcp-backup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Check if rclone is installed
if ! command -v rclone &> /dev/null; then
    log "${RED}❌ ERROR: rclone is not installed${NC}"
    log "   Install with: brew install rclone"
    exit 1
fi

# Check if rclone is configured
if ! rclone listremotes | grep -q "^gdrive:"; then
    log "${RED}❌ ERROR: Google Drive remote 'gdrive' not configured${NC}"
    log "   Run: rclone config"
    log "   Then select:"
    log "     - New remote"
    log "     - Name: gdrive"
    log "     - Storage: drive"
    exit 1
fi

# Check if MCP memory directory exists
if [ ! -d "$MCP_MEMORY_LOCAL" ]; then
    log "${YELLOW}⚠️  Warning: $MCP_MEMORY_LOCAL does not exist${NC}"
    log "   Creating directory..."
    mkdir -p "$MCP_MEMORY_LOCAL"
fi

# Display banner
echo ""
log "${BLUE}======================================${NC}"
log "${BLUE}MCP Memory → Google Drive Backup${NC}"
log "${BLUE}======================================${NC}"
echo ""

# Check local size
if [ -d "$MCP_MEMORY_LOCAL" ]; then
    SIZE=$(du -sh "$MCP_MEMORY_LOCAL" | cut -f1)
    log "📁 Local directory: $MCP_MEMORY_LOCAL"
    log "📊 Local size: $SIZE"
else
    log "${YELLOW}⚠️  Local directory is empty${NC}"
fi

# Sync to Google Drive
log ""
log "${BLUE}🔄 Starting sync to Google Drive...${NC}"
log ""

# rclone sync with options:
# --progress: Show progress during transfer
# --log-level INFO: Detailed logging
# --log-file: Append to log file
# --transfers 4: Use 4 parallel transfers
# --checkers 8: Use 8 parallel checkers
# --drive-chunk-size 64M: 64MB chunks for better performance
# --fast-list: Use recursive list if possible (faster for large dirs)
# --stats 10s: Update stats every 10 seconds

if rclone sync "$MCP_MEMORY_LOCAL" "$GDRIVE_REMOTE" \
    --progress \
    --log-level INFO \
    --log-file "$LOG_FILE" \
    --transfers 4 \
    --checkers 8 \
    --drive-chunk-size 64M \
    --fast-list \
    --stats 10s; then

    log ""
    log "${GREEN}======================================${NC}"
    log "${GREEN}✅ Backup completed successfully${NC}"
    log "${GREEN}======================================${NC}"

    # Show final stats
    log ""
    log "📊 Final Statistics:"
    log "   Local size: $SIZE"
    log "   Remote: $GDRIVE_REMOTE"
    log "   Log file: $LOG_FILE"

else
    EXIT_CODE=$?
    log ""
    log "${RED}======================================${NC}"
    log "${RED}❌ Backup failed with exit code $EXIT_CODE${NC}"
    log "${RED}======================================${NC}"
    log ""
    log "📋 Check log file for details: $LOG_FILE"
    exit $EXIT_CODE
fi

# Verify backup (optional)
echo ""
read -p "🔍 Verify backup integrity? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log ""
    log "${BLUE}🔍 Verifying backup...${NC}"

    if rclone check "$MCP_MEMORY_LOCAL" "$GDRIVE_REMOTE" --one-way; then
        log "${GREEN}✅ Verification successful - all files match${NC}"
    else
        log "${RED}❌ Verification failed - files may differ${NC}"
        log "   Run: rclone check $MCP_MEMORY_LOCAL $GDRIVE_REMOTE"
    fi
fi

echo ""
log "✨ Done!"
