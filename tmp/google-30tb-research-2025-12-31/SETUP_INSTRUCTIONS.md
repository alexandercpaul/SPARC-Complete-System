# Google Drive Integration Setup - Interactive Steps Required

## Status: Python Dependencies Installed ✓

The automated agent has completed the non-interactive setup steps:

1. ✅ Verified rclone is installed (`/opt/homebrew/bin/rclone`)
2. ✅ Verified MCP memory directory exists (`~/.mcp-memory/`)
3. ✅ Installed Python dependencies (PyDrive2, watchdog) in virtual environment

## Next Steps: Manual OAuth Configuration Required

Since Google Drive authentication requires interactive browser OAuth, you need to complete these steps:

### Step 1: Configure rclone with Google Drive

Run this command in your terminal:

```bash
rclone config
```

Follow these prompts:

1. **Choose**: `n` (new remote)
2. **Name**: `gdrive`
3. **Storage type**: `drive` (Google Drive)
4. **Client ID**: Press Enter (use defaults)
5. **Client Secret**: Press Enter (use defaults)
6. **Scope**: `1` (Full access to all files)
7. **Root folder ID**: Press Enter (leave blank)
8. **Service Account File**: Press Enter (leave blank)
9. **Edit advanced config**: `n` (No)
10. **Use auto config**: `y` (Yes - browser will open)
11. **Browser authentication**:
    - Browser will open automatically
    - Login with: `alexandercpaul@gmail.com`
    - Grant permissions to rclone
12. **Configure as team drive**: `n` (No)
13. **Confirm**: `y` (Yes, this is OK)
14. **Exit**: `q` (Quit config)

### Step 2: Test the Configuration

After configuring rclone, test that it works:

```bash
# Test connection
rclone lsd gdrive:

# Test sync (dry-run)
rclone sync ~/.mcp-memory/ gdrive:mcp-memory/ --dry-run
```

### Step 3: Run Integration Tests

Navigate to the project directory and run tests:

```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/google-30tb-research-2025-12-31/

# Activate virtual environment
source venv/bin/activate

# Run integration tests
python test_integration.py
```

### Step 4: Choose Your Sync Strategy

After tests pass, choose one of these options:

#### Option A: Manual Backup (Simplest)
```bash
rclone sync ~/.mcp-memory/ gdrive:mcp-memory/
```

#### Option B: Automated Backup with Cron (Recommended)
```bash
# Edit crontab
crontab -e

# Add this line (backups every 15 minutes):
*/15 * * * * /opt/homebrew/bin/rclone sync ~/.mcp-memory/ gdrive:mcp-memory/ >> ~/.mcp-backup.log 2>&1
```

#### Option C: Real-time Sync with Python Watcher
```bash
# Run in the project directory
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/google-30tb-research-2025-12-31/
source venv/bin/activate
python mcp_auto_sync.py

# Or run in background:
nohup python mcp_auto_sync.py > ~/mcp-auto-sync.log 2>&1 &
```

## Quick Reference Commands

### Check rclone is configured:
```bash
rclone listremotes
# Should show: gdrive:
```

### Check Google Drive contents:
```bash
rclone ls gdrive:mcp-memory/
```

### Manual backup:
```bash
rclone sync ~/.mcp-memory/ gdrive:mcp-memory/
```

### Check backup logs:
```bash
tail -f ~/.mcp-backup.log
```

### Verify on web:
https://drive.google.com

## Troubleshooting

### Issue: "Config file not found"
**Solution**: You need to run `rclone config` first (see Step 1 above)

### Issue: "gdrive remote not found"
**Solution**: The remote name must be exactly `gdrive` - check with `rclone listremotes`

### Issue: "OAuth authentication failed"
**Solution**:
1. Delete existing config: `rclone config delete gdrive`
2. Run `rclone config` again
3. Make sure you're logged into the correct Google account in your browser

### Issue: "Permission denied"
**Solution**: Make sure you granted all permissions when authenticating

## Support Files

All scripts and documentation are in:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/google-30tb-research-2025-12-31/
```

### Available files:
- `EXECUTIVE_SUMMARY.md` - Overview of the solution
- `INDEX.md` - Navigation guide
- `QUICK_START.md` - 5-minute setup guide
- `GOOGLE_30TB_INTEGRATION_GUIDE.md` - Complete 1,445-line guide
- `install.sh` - Automated setup script
- `test_integration.py` - Integration test suite
- `mcp-backup.sh` - Backup script for cron
- `mcp_auto_sync.py` - Real-time file watcher

## Success Criteria

You'll know it's working when:

1. ✅ `rclone listremotes` shows `gdrive:`
2. ✅ `rclone ls gdrive:` shows files
3. ✅ `python test_integration.py` passes all 6 tests
4. ✅ Files appear at https://drive.google.com in `mcp-memory/` folder
5. ✅ `vector_store.pkl` automatically syncs to Google Drive

## Estimated Time

- Step 1 (OAuth config): 3-5 minutes
- Step 2 (Test): 1 minute
- Step 3 (Integration tests): 2 minutes
- Step 4 (Choose sync): 2 minutes

**Total: ~10 minutes**

## What You'll Get

- ✅ Unlimited 30TB storage for MCP Memory
- ✅ Automatic cloud backups
- ✅ Zero marginal cost ($0.00 - already included in subscription)
- ✅ Multi-device sync capability
- ✅ Disaster recovery

---

**Last Updated**: 2025-12-31
**Status**: Waiting for OAuth configuration
**Next Action**: Run `rclone config` (see Step 1 above)
