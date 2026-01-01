# Quick Start: MCP Memory → 30TB Google Drive

**Goal**: Back up your MCP Memory to Google Drive in under 5 minutes.

---

## Option 1: Simple Backup with rclone (Recommended)

**Time**: 5 minutes

### Step 1: Install rclone

```bash
brew install rclone
```

### Step 2: Configure Google Drive

```bash
rclone config
```

**Follow prompts**:
- Choose: `n` (new remote)
- Name: `gdrive`
- Storage: `drive` (Google Drive)
- OAuth: `Auto config` (browser will open)
- Login with: `alexandercpaul@gmail.com`
- Advanced: `No`
- Keep all other defaults

### Step 3: Backup MCP Memory

```bash
rclone sync ~/.mcp-memory/ gdrive:mcp-memory/
```

### Step 4: Verify

Go to [drive.google.com](https://drive.google.com) and check for `mcp-memory/` folder.

**Done!** Your MCP Memory is now backed up to 30TB Drive.

---

## Option 2: Automated Backup (Cron Job)

**Time**: 2 minutes (after Option 1)

### Add to Crontab

```bash
crontab -e
```

**Add this line** (runs every 15 minutes):

```bash
*/15 * * * * /opt/homebrew/bin/rclone sync ~/.mcp-memory/ gdrive:mcp-memory/ >> ~/.mcp-backup.log 2>&1
```

**Done!** Automatic backups every 15 minutes.

---

## Option 3: Python Auto-Sync (Real-time)

**Time**: 10 minutes

### Install Dependencies

```bash
pip install PyDrive2 watchdog
```

### Run Auto-Sync Daemon

```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/google-30tb-research-2025-12-31/

python mcp_auto_sync.py
```

**First run**: Browser will open for Google OAuth authentication.

**What it does**:
- Watches `~/.mcp-memory/` directory
- Auto-uploads changes to Google Drive
- Runs continuously in background

**To run in background**:

```bash
nohup python mcp_auto_sync.py > ~/mcp-auto-sync.log 2>&1 &
```

**Done!** Real-time sync enabled.

---

## Troubleshooting

### Issue: "command not found: rclone"

**Fix**:
```bash
brew install rclone
```

### Issue: "remote 'gdrive' not configured"

**Fix**:
```bash
rclone config
```

### Issue: OAuth error in Python scripts

**Fix**: Delete old credentials and re-authenticate
```bash
rm mycreds.txt
python mcp_backup_pydrive2.py
```

---

## What You Get

- **30TB** of Google Drive storage (included with AI Ultra subscription)
- **Zero marginal cost** (already paying subscription)
- **Automatic backups** (with cron or auto-sync)
- **Multi-device access** (sync across computers)
- **Disaster recovery** (cloud backup)

**Current usage**: 8KB / 30TB = 0.00000027%

You have effectively **unlimited storage** for MCP Memory!

---

## Next Steps

1. Set up one of the backup options above
2. Test by modifying `~/.mcp-memory/vector_store.pkl`
3. Verify backup on Google Drive
4. Read full guide: `GOOGLE_30TB_INTEGRATION_GUIDE.md`

---

**Need help?** See full documentation in `GOOGLE_30TB_INTEGRATION_GUIDE.md`
