#!/bin/bash
# Setup iCloud Drive Sync for MCP Memory
# This script moves .mcp-memory to iCloud Drive and creates a symlink

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================"
echo "MCP Memory iCloud Drive Sync Setup"
echo "========================================"
echo ""

# Paths
MCP_LOCAL="$HOME/.mcp-memory"
ICLOUD_BASE="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
MCP_ICLOUD="$ICLOUD_BASE/.mcp-memory"

# Check if iCloud Drive exists
if [ ! -d "$ICLOUD_BASE" ]; then
    echo -e "${RED}Error: iCloud Drive not found at $ICLOUD_BASE${NC}"
    echo "Please ensure iCloud Drive is enabled in System Settings."
    exit 1
fi

echo -e "${GREEN}✓${NC} iCloud Drive found"

# Check if MCP Memory exists
if [ ! -d "$MCP_LOCAL" ]; then
    echo -e "${YELLOW}⚠${NC} MCP Memory directory not found at $MCP_LOCAL"
    echo "Creating new directory in iCloud..."
    mkdir -p "$MCP_ICLOUD"
    ln -s "$MCP_ICLOUD" "$MCP_LOCAL"
    echo -e "${GREEN}✓${NC} Created new MCP Memory in iCloud Drive"
    echo -e "${GREEN}✓${NC} Symlink created: $MCP_LOCAL -> $MCP_ICLOUD"
    exit 0
fi

# Check if already a symlink
if [ -L "$MCP_LOCAL" ]; then
    LINK_TARGET=$(readlink "$MCP_LOCAL")
    echo -e "${GREEN}✓${NC} MCP Memory is already a symlink to: $LINK_TARGET"

    if [[ "$LINK_TARGET" == *"CloudDocs"* ]]; then
        echo -e "${GREEN}✓${NC} Already syncing to iCloud Drive!"
        exit 0
    else
        echo -e "${YELLOW}⚠${NC} Symlink exists but not pointing to iCloud"
        echo "Current target: $LINK_TARGET"
        echo "To re-setup, remove the symlink first: rm $MCP_LOCAL"
        exit 1
    fi
fi

# Check if target already exists in iCloud
if [ -d "$MCP_ICLOUD" ]; then
    echo -e "${RED}Error: Target directory already exists in iCloud: $MCP_ICLOUD${NC}"
    echo "Please remove or rename it first."
    exit 1
fi

# Perform migration
echo ""
echo "Migration Plan:"
echo "  1. Move: $MCP_LOCAL -> $MCP_ICLOUD"
echo "  2. Create symlink: $MCP_LOCAL -> $MCP_ICLOUD"
echo ""
echo -e "${YELLOW}This will enable automatic iCloud sync for MCP Memory.${NC}"
echo ""
read -p "Proceed? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Stop MCP Memory server if running
echo ""
echo "Checking for running MCP Memory server..."
if pgrep -f "mcp-memory-extension" > /dev/null; then
    echo -e "${YELLOW}⚠${NC} MCP Memory server is running. Please stop it first."
    echo "You can stop it with: pkill -f mcp-memory-extension"
    exit 1
fi

# Perform migration
echo ""
echo "Starting migration..."

# Move directory
echo "Moving $MCP_LOCAL to $MCP_ICLOUD..."
mv "$MCP_LOCAL" "$MCP_ICLOUD"
echo -e "${GREEN}✓${NC} Moved to iCloud Drive"

# Create symlink
echo "Creating symlink..."
ln -s "$MCP_ICLOUD" "$MCP_LOCAL"
echo -e "${GREEN}✓${NC} Symlink created"

# Verify
if [ -L "$MCP_LOCAL" ] && [ -d "$MCP_ICLOUD" ]; then
    echo ""
    echo -e "${GREEN}✓✓✓ Migration Successful! ✓✓✓${NC}"
    echo ""
    echo "MCP Memory is now syncing to iCloud Drive:"
    echo "  Local symlink: $MCP_LOCAL"
    echo "  iCloud location: $MCP_ICLOUD"
    echo ""
    echo "Benefits:"
    echo "  • Automatic cloud backup"
    echo "  • Syncs across all your Macs"
    echo "  • Survives all compactions forever"
    echo "  • Zero manual intervention required"
    echo ""
    echo "You can now restart the MCP Memory server."
else
    echo -e "${RED}Error: Migration verification failed${NC}"
    exit 1
fi
