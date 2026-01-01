#!/bin/bash
# Quick installation script for MCP Memory → Google Drive integration
# Run: ./install.sh

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}MCP Memory → Google Drive Setup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install rclone
install_rclone() {
    echo -e "${YELLOW}📦 Installing rclone...${NC}"

    if command_exists brew; then
        brew install rclone
        echo -e "${GREEN}✅ rclone installed${NC}"
    else
        echo -e "${RED}❌ Homebrew not found${NC}"
        echo "   Install Homebrew first: https://brew.sh"
        exit 1
    fi
}

# Function to install Python dependencies
install_python_deps() {
    echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"

    if command_exists pip3; then
        pip3 install PyDrive2 watchdog
        echo -e "${GREEN}✅ Python dependencies installed${NC}"
    elif command_exists pip; then
        pip install PyDrive2 watchdog
        echo -e "${GREEN}✅ Python dependencies installed${NC}"
    else
        echo -e "${RED}❌ pip not found${NC}"
        echo "   Install Python first: https://www.python.org/downloads/"
        exit 1
    fi
}

# Function to configure rclone
configure_rclone() {
    echo ""
    echo -e "${BLUE}🔧 Configuring rclone for Google Drive${NC}"
    echo ""
    echo "Follow these steps:"
    echo "  1. Choose: n (new remote)"
    echo "  2. Name: gdrive"
    echo "  3. Storage: drive (Google Drive)"
    echo "  4. OAuth: Auto config (browser will open)"
    echo "  5. Login with: alexandercpaul@gmail.com"
    echo "  6. Advanced: No"
    echo "  7. Keep all other defaults"
    echo ""

    read -p "Press Enter to start rclone config..."

    rclone config

    echo ""
    if rclone listremotes | grep -q "^gdrive:"; then
        echo -e "${GREEN}✅ rclone configured successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  'gdrive' remote not found${NC}"
        echo "   You can configure it later with: rclone config"
    fi
}

# Function to test backup
test_backup() {
    echo ""
    echo -e "${BLUE}🧪 Testing backup...${NC}"

    # Create test directory if needed
    if [ ! -d "$HOME/.mcp-memory" ]; then
        mkdir -p "$HOME/.mcp-memory"
        echo "test" > "$HOME/.mcp-memory/test.txt"
    fi

    # Test sync
    if rclone sync "$HOME/.mcp-memory/" gdrive:mcp-memory/ --dry-run; then
        echo -e "${GREEN}✅ Backup test successful (dry-run)${NC}"

        read -p "Run actual backup now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rclone sync "$HOME/.mcp-memory/" gdrive:mcp-memory/
            echo -e "${GREEN}✅ Backup completed${NC}"
            echo "   Check: https://drive.google.com"
        fi
    else
        echo -e "${RED}❌ Backup test failed${NC}"
    fi
}

# Function to setup cron job
setup_cron() {
    echo ""
    echo -e "${BLUE}⏰ Setup automated backups?${NC}"
    echo "   This will run backups every 15 minutes"
    echo ""

    read -p "Setup cron job? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        RCLONE_PATH=$(which rclone)
        CRON_COMMAND="*/15 * * * * $RCLONE_PATH sync ~/.mcp-memory/ gdrive:mcp-memory/ >> ~/.mcp-backup.log 2>&1"

        # Check if cron job already exists
        if crontab -l 2>/dev/null | grep -q "mcp-memory"; then
            echo -e "${YELLOW}⚠️  Cron job already exists${NC}"
        else
            # Add to crontab
            (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
            echo -e "${GREEN}✅ Cron job added${NC}"
            echo "   Backups will run every 15 minutes"
            echo "   Log: ~/.mcp-backup.log"
        fi
    fi
}

# Function to show summary
show_summary() {
    echo ""
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}Installation Complete!${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""
    echo -e "${GREEN}What's next?${NC}"
    echo ""
    echo "  1. Manual backup:"
    echo "     rclone sync ~/.mcp-memory/ gdrive:mcp-memory/"
    echo ""
    echo "  2. Run auto-sync daemon (real-time):"
    echo "     python mcp_auto_sync.py"
    echo ""
    echo "  3. Check backup on Google Drive:"
    echo "     https://drive.google.com"
    echo ""
    echo "  4. View logs:"
    echo "     tail -f ~/.mcp-backup.log"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "  - Quick start: QUICK_START.md"
    echo "  - Full guide: GOOGLE_30TB_INTEGRATION_GUIDE.md"
    echo ""
}

# Main installation flow
main() {
    # Check prerequisites
    echo "🔍 Checking prerequisites..."
    echo ""

    # Check rclone
    if command_exists rclone; then
        echo -e "${GREEN}✅ rclone already installed${NC}"
    else
        echo -e "${YELLOW}⚠️  rclone not found${NC}"
        install_rclone
    fi

    # Check Python
    if command_exists python3 || command_exists python; then
        echo -e "${GREEN}✅ Python already installed${NC}"

        # Check Python packages
        echo ""
        read -p "Install Python dependencies (PyDrive2, watchdog)? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_python_deps
        fi
    else
        echo -e "${YELLOW}⚠️  Python not found (optional for Python scripts)${NC}"
    fi

    # Configure rclone
    echo ""
    if rclone listremotes 2>/dev/null | grep -q "^gdrive:"; then
        echo -e "${GREEN}✅ rclone 'gdrive' remote already configured${NC}"
    else
        echo -e "${YELLOW}⚠️  rclone not configured for Google Drive${NC}"
        configure_rclone
    fi

    # Test backup
    if rclone listremotes 2>/dev/null | grep -q "^gdrive:"; then
        test_backup
    fi

    # Setup cron
    if command_exists crontab; then
        setup_cron
    fi

    # Show summary
    show_summary
}

# Run main
main
