# Google 30TB Storage Integration Guide for MCP Memory Persistence

**Created**: 2025-12-31
**User**: alexandercpaul@gmail.com
**Subscription**: Google AI Ultra ($250/month)
**Goal**: Unlimited MCP Memory persistence on 30TB Google Drive storage

---

## Executive Summary

Your Google AI Ultra subscription includes **30TB of Google Drive storage** (not Google Cloud Storage). This is standard Google Drive that works with Gmail, Drive, and Photos. You can leverage this massive storage allocation for unlimited MCP Memory persistence at zero marginal cost.

**Key Findings**:
- ✅ Storage Type: **Google Drive** (not GCS)
- ✅ Size: **30TB** across Drive, Gmail, Photos
- ✅ Current MCP Memory: **8KB** (`~/.mcp-memory/vector_store.pkl`)
- ✅ OAuth Credentials: Already exist at `~/.gemini/oauth_creds.json`
- ✅ Scopes Available: `cloud-platform`, `userinfo.email`, `openid`, `userinfo.profile`
- ✅ Best Python Library: **PyDrive2** (simplifies Google Drive API)
- ✅ Backup Tool: **rclone** (rsync-like sync with Google Drive)

---

## Table of Contents

1. [What Storage Do You Have?](#1-what-storage-do-you-have)
2. [Access Methods](#2-access-methods)
3. [Storage Capabilities](#3-storage-capabilities)
4. [Integration with MCP Memory](#4-integration-with-mcp-memory)
5. [Authentication](#5-authentication)
6. [Implementation Guide](#6-implementation-guide)
7. [Performance Benchmarks](#7-performance-benchmarks)
8. [Cost Considerations](#8-cost-considerations)
9. [Code Examples](#9-code-examples)
10. [Recommended Architecture](#10-recommended-architecture)

---

## 1. What Storage Do You Have?

### Google AI Ultra Storage Breakdown

Your **$249.99/month Google AI Ultra** subscription includes:

- **30TB of Google Drive storage** (shared across):
  - Google Drive (files, folders, documents)
  - Gmail (email storage)
  - Google Photos (photos, videos)
- Access to Gemini 3 Pro
- Advanced AI features

**Important**: This is NOT Google Cloud Storage (GCS). It's Google Drive - the same service as regular Google Drive, just with 30TB instead of 15GB.

**Source**: [Google AI Plans with Cloud Storage](https://one.google.com/about/google-ai-plans/)

---

## 2. Access Methods

### Option 1: PyDrive2 (Recommended for Python)

**Why PyDrive2?**
- Simplifies OAuth2.0 into just a few lines
- Built on top of `google-api-python-client`
- Handles pagination, content fetching automatically
- Object-oriented interface
- Active development (maintained fork of PyDrive)

**Installation**:
```bash
pip install PyDrive2
```

**Best For**:
- Python scripts and automation
- Programmatic file upload/download
- Direct API access
- Custom MCP Memory sync logic

**Sources**:
- [PyDrive2 GitHub](https://github.com/iterative/PyDrive2)
- [PyDrive2 Documentation](https://docs.iterative.ai/PyDrive2/)

### Option 2: rclone (Recommended for Backups)

**Why rclone?**
- "rsync for cloud storage"
- Mount Google Drive as filesystem
- Efficient sync with change detection
- Incremental backups
- Cross-platform (macOS, Linux, Windows)

**Installation**:
```bash
brew install rclone  # macOS
```

**Best For**:
- Automated backups
- Mounting Drive as local filesystem
- Command-line sync operations
- CI/CD pipelines

**Sources**:
- [rclone Google Drive](https://rclone.org/drive/)
- [rclone GitHub](https://github.com/rclone/rclone)

### Option 3: Official google-api-python-client

**Why Official SDK?**
- Low-level control
- Works with all Google APIs
- Most flexible
- Official support

**Installation**:
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

**Best For**:
- Advanced use cases
- Multi-API integration
- Fine-grained control

**Source**: [Python quickstart | Google Drive](https://developers.google.com/workspace/drive/api/quickstart/python)

### Option 4: Google Drive Desktop App

**Why Desktop App?**
- Zero configuration
- Automatic sync
- Native macOS integration

**Best For**:
- Manual file management
- Quick testing
- Non-technical users

---

## 3. Storage Capabilities

### File Storage

✅ **Can Store**:
- Arbitrary binary files (`.pkl`, `.db`, `.sqlite`)
- Vector databases (ChromaDB, LanceDB, SQLite)
- Large files up to **5TB per file**
- Any file type

❌ **Limitations**:
- **750GB per day upload limit** per user
- **5TB max file size**
- Files > 750GB can't be copied (must download then re-upload)
- After hitting 750GB/day limit, wait 24 hours

**Source**: [Storage and upload limits](https://support.google.com/a/answer/172541?hl=en)

### API Rate Limits

**Request Limits**:
- **20,000 calls per 100 seconds** (per project, per user)
- ~200 requests/second project-wide
- ~40 requests/second per user

**Error Handling**:
- `403: User rate limit exceeded` → Use exponential backoff
- `429: Too many requests` → Backend rate limit, retry with backoff

**Source**: [Usage limits | Google Drive](https://developers.google.com/workspace/drive/api/guides/limits)

### File Size & Quantity Limits

- **Max 500 million items** per account (files + folders + shortcuts)
- **Max 500,000 items per folder**
- **Max 5TB per file**
- Deleted files don't count toward limits

---

## 4. Integration with MCP Memory

### Current MCP Memory Setup

**Location**: `~/.mcp-memory/`

**Contents**:
```bash
$ ls -lah ~/.mcp-memory/
total 16
drwxr-xr-x   3 alexandercpaul  staff    96B Dec 31 12:02 .
drwxr-x---+ 51 alexandercpaul  staff   1.6K Dec 31 12:15 ..
-rw-r--r--   1 alexandercpaul  staff   4.1K Dec 31 12:15 vector_store.pkl

$ du -sh ~/.mcp-memory/vector_store.pkl
8.0K	/Users/alexandercpaul/.mcp-memory/vector_store.pkl
```

### Integration Strategies

#### Strategy 1: Real-Time Sync (Recommended)

**Pattern**: Local primary + Cloud backup

**How it works**:
1. MCP Memory writes to `~/.mcp-memory/vector_store.pkl`
2. File watcher detects changes
3. Auto-upload to Google Drive (async)
4. Keep local copy for fast reads

**Latency**: 5ms local reads, async cloud writes

**Pros**:
- Zero latency for reads
- Automatic cloud backup
- No code changes to MCP Memory

**Cons**:
- Requires file watcher
- Potential sync delays

#### Strategy 2: Periodic Backup

**Pattern**: Scheduled sync

**How it works**:
1. Cron job runs every N minutes/hours
2. rclone syncs `~/.mcp-memory/` to Drive
3. Only changed files uploaded

**Latency**: N/A (backup only)

**Pros**:
- Simple setup
- Efficient (only changed files)
- No daemon required

**Cons**:
- Not real-time
- Potential data loss between backups

#### Strategy 3: Cloud Primary Storage

**Pattern**: Mount Drive as filesystem

**How it works**:
1. rclone mount Drive as `~/GoogleDrive/`
2. Symlink `~/.mcp-memory` → `~/GoogleDrive/mcp-memory/`
3. MCP Memory reads/writes directly to Drive

**Latency**: 250ms - 10s per read (see [Performance](#7-performance-benchmarks))

**Pros**:
- Always in sync
- Automatic multi-device access
- No sync logic needed

**Cons**:
- High read latency (250ms - 10s)
- Not suitable for real-time vector search
- Network dependency

#### Strategy 4: Hybrid (Best of Both Worlds)

**Pattern**: Local cache + Cloud sync + Change detection

**How it works**:
1. Local SQLite/ChromaDB for fast reads
2. Google Drive Changes API detects remote updates
3. Incremental sync when changes detected
4. Write-through cache to Drive

**Latency**: 5ms reads, async writes

**Pros**:
- Fast local performance
- Multi-device sync
- Efficient bandwidth usage
- Change detection (not full scans)

**Cons**:
- Most complex implementation
- Requires conflict resolution

**Source**: [DRIVEUP: Incremental Backup](https://github.com/eblet/driveup)

---

## 5. Authentication

### Your Existing OAuth Credentials

**Location**: `~/.gemini/oauth_creds.json`

**Current Scopes**:
```json
{
  "scope": "https://www.googleapis.com/auth/cloud-platform https://www.googleapis.com/auth/userinfo.email openid https://www.googleapis.com/auth/userinfo.profile"
}
```

### Required Scopes for Google Drive

**Option A: Full Drive Access** (Easier, less secure)
```
https://www.googleapis.com/auth/drive
```
- Access to all Drive files
- Requires user consent
- Considered "restricted scope" by Google

**Option B: Per-File Access** (Recommended, more secure)
```
https://www.googleapis.com/auth/drive.file
```
- Only access files created by your app
- Users explicitly grant access
- More secure, encouraged by Google

**Your Current Status**:
- ❌ No Drive-specific scopes yet
- ✅ Have `cloud-platform` (broad scope, may include Drive)
- 🔧 Need to add `drive.file` or `drive` scope

**Source**: [Choose Google Drive API scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)

### Adding Drive Scopes

You'll need to:
1. Update OAuth scopes to include Drive
2. Re-authorize (delete `token.pickle` if using official SDK)
3. User consent to new permissions

See [Code Examples](#9-code-examples) for implementation.

---

## 6. Implementation Guide

### Quick Start: 3 Steps to Cloud Backup

#### Step 1: Install rclone

```bash
brew install rclone
```

#### Step 2: Configure Google Drive

```bash
rclone config

# Choose: n (new remote)
# Name: gdrive
# Storage: drive (Google Drive)
# OAuth: Auto config (browser will open)
# Advanced: No
# Keep defaults
```

#### Step 3: Sync MCP Memory

```bash
# One-time sync
rclone sync ~/.mcp-memory/ gdrive:mcp-memory/

# Automated backup (add to crontab)
# Runs every 15 minutes
*/15 * * * * /opt/homebrew/bin/rclone sync ~/.mcp-memory/ gdrive:mcp-memory/
```

**Done!** Your MCP Memory is now backed up to 30TB Drive.

### Advanced: Python Integration

See [Code Examples](#9-code-examples) for:
- PyDrive2 upload/download
- Incremental sync with Changes API
- File watcher with auto-upload
- Conflict resolution

---

## 7. Performance Benchmarks

### rclone Mount Performance

**Real-world measurements from rclone users**:

| Operation | Speed | Latency | Notes |
|-----------|-------|---------|-------|
| Small file read (1-20MB) | 6-8 MB/s | 250ms | First 200 chars |
| Large file read | 60-80 MB/s | N/A | Sustained |
| Upload (small files) | <10 MB/s | N/A | Many small files |
| Upload (large files) | 50-80 MB/s | N/A | With `--drive-chunk-size 2G` |
| Mount access (PDF) | N/A | 5-10s | Time to appear after click |
| rclone copy vs mount | **333x faster** | N/A | 100 MB/s vs 300 KB/s |

**Key Insight**: `rclone copy` is **333x faster** than `rclone mount` for reads.

**Recommendation**:
- Use **mount** for convenience (filesystem access)
- Use **copy/sync** for performance (scripted backups)

**Source**: [rclone forum discussions](https://forum.rclone.org/t/poor-read-speed-from-google-drive/28847)

### PyDrive2 Performance

**Expected Performance**:
- API call overhead: ~100-200ms per request
- Upload speed: Limited by Google Drive API quotas
- Download speed: Limited by network bandwidth
- Pagination: Automatic, efficient

**Optimization Tips**:
- Use resumable uploads for files >5MB
- Implement chunked uploads for large files
- Use batch requests for multiple operations
- Cache metadata locally

---

## 8. Cost Considerations

### Direct Costs

**Google AI Ultra Subscription**: $249.99/month

**What's included**:
- 30TB Google Drive storage
- Gemini 3 Pro access
- No additional API costs for Drive access
- Unlimited API calls (within rate limits)

**Marginal cost for MCP Memory storage**: **$0.00**

You're already paying the subscription, storage is included!

### API Quotas (Not Costs)

**Free tier quotas**:
- 20,000 API calls per 100 seconds
- 750GB uploads per day

**Can you increase quotas?**
- ❌ API call rate limits cannot be increased
- ❌ 750GB daily upload limit cannot be increased

**Workaround**: Exponential backoff + retry logic

### Comparison to Competitors

| Service | Storage | Price/month | Notes |
|---------|---------|-------------|-------|
| **Google AI Ultra** | **30TB** | **$249.99** | Includes AI + storage |
| Dropbox Plus | 2TB | $11.99 | Cloud storage only |
| iCloud+ | 2TB | $9.99 | Apple ecosystem |
| OneDrive | 1TB | $6.99 | Microsoft 365 |
| Google One (standalone) | 2TB | $9.99 | No AI |
| S3 Standard (AWS) | 30TB | ~$690/month | Just storage! |

**Your value**: 30TB storage is effectively free with AI subscription.

---

## 9. Code Examples

### Example 1: PyDrive2 Basic Upload/Download

```python
#!/usr/bin/env python3
"""
Basic MCP Memory backup to Google Drive using PyDrive2
"""

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os

# Authenticate
gauth = GoogleAuth()

# Try to load saved credentials
gauth.LoadCredentialsFile("mycreds.txt")

if gauth.credentials is None:
    # Authenticate if credentials don't exist
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh credentials if expired
    gauth.Refresh()
else:
    # Initialize the saved credentials
    gauth.Authorize()

# Save credentials for next run
gauth.SaveCredentialsFile("mycreds.txt")

drive = GoogleDrive(gauth)

def upload_mcp_memory():
    """Upload vector_store.pkl to Google Drive"""

    mcp_memory_path = os.path.expanduser("~/.mcp-memory/vector_store.pkl")

    # Create file on Drive
    file_drive = drive.CreateFile({
        'title': 'vector_store.pkl',
        'parents': [{'id': 'root'}]  # Upload to root, or specify folder ID
    })

    # Set content
    file_drive.SetContentFile(mcp_memory_path)

    # Upload
    file_drive.Upload()

    print(f"✅ Uploaded {mcp_memory_path} to Google Drive")
    print(f"   File ID: {file_drive['id']}")
    return file_drive['id']

def download_mcp_memory(file_id):
    """Download vector_store.pkl from Google Drive"""

    file_drive = drive.CreateFile({'id': file_id})

    download_path = os.path.expanduser("~/.mcp-memory/vector_store.pkl")

    file_drive.GetContentFile(download_path)

    print(f"✅ Downloaded to {download_path}")

if __name__ == "__main__":
    # Upload
    file_id = upload_mcp_memory()

    # Download (example)
    # download_mcp_memory(file_id)
```

**Save as**: `mcp_backup_pydrive2.py`

**Run**:
```bash
pip install PyDrive2
python mcp_backup_pydrive2.py
```

---

### Example 2: Resumable Upload for Large Files

```python
#!/usr/bin/env python3
"""
Resumable upload with progress tracking for large MCP Memory files
"""

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    """Authenticate and return Drive service"""

    creds = None
    token_path = 'token.pickle'

    # Load existing credentials
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # You'll need to implement OAuth flow here
            # See: https://developers.google.com/drive/api/quickstart/python
            raise Exception("Need to implement OAuth flow")

        # Save credentials
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def upload_with_progress(file_path, drive_folder_id=None):
    """Upload file with resumable upload and progress tracking"""

    service = get_drive_service()

    file_metadata = {
        'name': os.path.basename(file_path)
    }

    if drive_folder_id:
        file_metadata['parents'] = [drive_folder_id]

    # Create resumable upload with 5MB chunks
    media = MediaFileUpload(
        file_path,
        mimetype='application/octet-stream',
        resumable=True,
        chunksize=5 * 1024 * 1024  # 5MB chunks
    )

    request = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    )

    # Upload with progress tracking
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"⏫ Uploaded {int(status.progress() * 100)}%")

    print(f"✅ Upload complete! File ID: {response.get('id')}")
    return response.get('id')

if __name__ == "__main__":
    mcp_memory_path = os.path.expanduser("~/.mcp-memory/vector_store.pkl")
    upload_with_progress(mcp_memory_path)
```

**Save as**: `mcp_resumable_upload.py`

---

### Example 3: Incremental Sync with Changes API

```python
#!/usr/bin/env python3
"""
Incremental sync using Google Drive Changes API
Only syncs files that changed since last check
"""

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pickle
import os
import json

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PATH = 'drive_changes_token.json'

def get_service():
    """Get authenticated Drive service"""
    # (Same as previous example)
    pass

def get_start_page_token(service):
    """Get the current start page token for tracking changes"""
    response = service.changes().getStartPageToken().execute()
    return response.get('startPageToken')

def save_token(token):
    """Save page token to disk"""
    with open(TOKEN_PATH, 'w') as f:
        json.dump({'pageToken': token}, f)

def load_token():
    """Load page token from disk"""
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, 'r') as f:
            return json.load(f).get('pageToken')
    return None

def sync_changes(service, mcp_folder_id):
    """Sync only changed files since last check"""

    # Load saved token or get new one
    page_token = load_token()
    if not page_token:
        page_token = get_start_page_token(service)
        print("🆕 First run - getting initial token")

    print(f"🔍 Checking for changes since token: {page_token}")

    changes = []
    while page_token is not None:
        response = service.changes().list(
            pageToken=page_token,
            spaces='drive',
            fields='nextPageToken, newStartPageToken, changes(fileId, file(name, mimeType, modifiedTime))'
        ).execute()

        changes.extend(response.get('changes', []))

        if 'newStartPageToken' in response:
            # Last page, save token for next run
            page_token = response.get('newStartPageToken')
            save_token(page_token)
            break

        page_token = response.get('nextPageToken')

    print(f"📊 Found {len(changes)} changes")

    for change in changes:
        file_info = change.get('file')
        if file_info:
            print(f"  📄 {file_info['name']} - {file_info['modifiedTime']}")

    return changes

if __name__ == "__main__":
    service = get_service()
    changes = sync_changes(service, mcp_folder_id='root')
```

**Save as**: `mcp_incremental_sync.py`

**Key Feature**: Uses Google Drive Changes API to detect only modified files, avoiding full directory scans.

**Source**: [DRIVEUP implementation](https://github.com/eblet/driveup)

---

### Example 4: File Watcher with Auto-Upload

```python
#!/usr/bin/env python3
"""
Watch MCP Memory directory and auto-upload changes to Google Drive
"""

import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

MCP_MEMORY_PATH = os.path.expanduser("~/.mcp-memory/")

class MCPMemoryHandler(FileSystemEventHandler):
    def __init__(self, drive):
        self.drive = drive
        self.file_id_map = {}  # Local cache of file_path -> drive_file_id

    def on_modified(self, event):
        if event.is_directory:
            return

        print(f"📝 File changed: {event.src_path}")
        self.upload_file(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return

        print(f"🆕 New file: {event.src_path}")
        self.upload_file(event.src_path)

    def upload_file(self, file_path):
        """Upload or update file on Google Drive"""

        filename = os.path.basename(file_path)

        # Check if file already exists on Drive
        file_id = self.file_id_map.get(file_path)

        if file_id:
            # Update existing file
            file_drive = self.drive.CreateFile({'id': file_id})
        else:
            # Create new file
            file_drive = self.drive.CreateFile({
                'title': filename,
                'parents': [{'id': 'root'}]
            })

        # Upload content
        file_drive.SetContentFile(file_path)
        file_drive.Upload()

        # Cache file ID
        self.file_id_map[file_path] = file_drive['id']

        print(f"✅ Uploaded {filename} (ID: {file_drive['id']})")

def main():
    # Authenticate with PyDrive2
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")

    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("mycreds.txt")
    drive = GoogleDrive(gauth)

    # Set up file watcher
    event_handler = MCPMemoryHandler(drive)
    observer = Observer()
    observer.schedule(event_handler, MCP_MEMORY_PATH, recursive=True)
    observer.start()

    print(f"👀 Watching {MCP_MEMORY_PATH} for changes...")
    print("   Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()

if __name__ == "__main__":
    main()
```

**Save as**: `mcp_auto_sync.py`

**Install dependencies**:
```bash
pip install PyDrive2 watchdog
```

**Run**:
```bash
python mcp_auto_sync.py
```

**How it works**:
1. Watches `~/.mcp-memory/` directory
2. Detects file changes automatically
3. Uploads changed files to Google Drive
4. Runs continuously in background

---

### Example 5: rclone Automation Script

```bash
#!/bin/bash
# Automated MCP Memory backup using rclone
# Save as: ~/bin/mcp-backup.sh

set -euo pipefail

# Configuration
MCP_MEMORY_LOCAL="$HOME/.mcp-memory/"
GDRIVE_REMOTE="gdrive:mcp-memory/"
LOG_FILE="$HOME/.mcp-backup.log"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Check if rclone is configured
if ! rclone listremotes | grep -q "^gdrive:"; then
    log "❌ ERROR: Google Drive remote 'gdrive' not configured"
    log "   Run: rclone config"
    exit 1
fi

# Sync to Google Drive
log "🔄 Starting MCP Memory backup..."

if rclone sync "$MCP_MEMORY_LOCAL" "$GDRIVE_REMOTE" \
    --progress \
    --log-level INFO \
    --log-file "$LOG_FILE" \
    --transfers 4 \
    --checkers 8 \
    --drive-chunk-size 64M; then

    log "✅ Backup completed successfully"

    # Show stats
    SIZE=$(du -sh "$MCP_MEMORY_LOCAL" | cut -f1)
    log "   Local size: $SIZE"

else
    log "❌ Backup failed with exit code $?"
    exit 1
fi
```

**Setup**:
```bash
# Make executable
chmod +x ~/bin/mcp-backup.sh

# Test run
~/bin/mcp-backup.sh

# Add to crontab for automated backups
crontab -e

# Add this line (runs every 15 minutes):
*/15 * * * * $HOME/bin/mcp-backup.sh
```

---

### Example 6: Full Integration with Conflict Resolution

```python
#!/usr/bin/env python3
"""
Complete MCP Memory <-> Google Drive integration
Features:
- Bidirectional sync
- Conflict resolution (last write wins)
- Metadata tracking
- Incremental sync
"""

import os
import json
import hashlib
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

MCP_MEMORY_PATH = os.path.expanduser("~/.mcp-memory/")
METADATA_FILE = os.path.join(MCP_MEMORY_PATH, ".sync_metadata.json")

class MCPDriveSync:
    def __init__(self):
        self.drive = self._authenticate()
        self.metadata = self._load_metadata()

    def _authenticate(self):
        """Authenticate with Google Drive"""
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile("mycreds.txt")

        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()

        gauth.SaveCredentialsFile("mycreds.txt")
        return GoogleDrive(gauth)

    def _load_metadata(self):
        """Load sync metadata (file hashes, timestamps)"""
        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """Save sync metadata"""
        with open(METADATA_FILE, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _file_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_remote_files(self):
        """List all files in Drive MCP folder"""
        query = "title='vector_store.pkl' and trashed=false"
        file_list = self.drive.ListFile({'q': query}).GetList()
        return {f['title']: f for f in file_list}

    def sync_to_drive(self):
        """Upload local changes to Google Drive"""

        for filename in os.listdir(MCP_MEMORY_PATH):
            if filename.startswith('.'):
                continue  # Skip hidden files

            local_path = os.path.join(MCP_MEMORY_PATH, filename)

            if not os.path.isfile(local_path):
                continue

            # Calculate current hash
            current_hash = self._file_hash(local_path)

            # Check if changed since last sync
            last_hash = self.metadata.get(filename, {}).get('hash')

            if current_hash == last_hash:
                print(f"⏭️  {filename} - No changes")
                continue

            # File changed - upload
            print(f"⏫ {filename} - Uploading...")

            remote_files = self._get_remote_files()

            if filename in remote_files:
                # Update existing
                file_drive = remote_files[filename]
            else:
                # Create new
                file_drive = self.drive.CreateFile({
                    'title': filename,
                    'parents': [{'id': 'root'}]
                })

            file_drive.SetContentFile(local_path)
            file_drive.Upload()

            # Update metadata
            self.metadata[filename] = {
                'hash': current_hash,
                'drive_id': file_drive['id'],
                'last_sync': datetime.now().isoformat()
            }

            print(f"   ✅ Uploaded (ID: {file_drive['id']})")

        self._save_metadata()
        print("\n✅ Sync to Drive complete")

    def sync_from_drive(self):
        """Download remote changes from Google Drive"""

        remote_files = self._get_remote_files()

        for filename, file_drive in remote_files.items():
            local_path = os.path.join(MCP_MEMORY_PATH, filename)

            # Get remote modification time
            remote_modified = file_drive['modifiedDate']

            # Get local modification time
            if os.path.exists(local_path):
                local_modified = datetime.fromtimestamp(
                    os.path.getmtime(local_path)
                ).isoformat()
            else:
                local_modified = None

            # Conflict resolution: last write wins
            if local_modified and local_modified > remote_modified:
                print(f"⏭️  {filename} - Local is newer, skipping")
                continue

            # Download from Drive
            print(f"⏬ {filename} - Downloading...")
            file_drive.GetContentFile(local_path)

            # Update metadata
            self.metadata[filename] = {
                'hash': self._file_hash(local_path),
                'drive_id': file_drive['id'],
                'last_sync': datetime.now().isoformat()
            }

            print(f"   ✅ Downloaded")

        self._save_metadata()
        print("\n✅ Sync from Drive complete")

    def bidirectional_sync(self):
        """Sync both ways"""
        print("=" * 60)
        print("MCP Memory <-> Google Drive Bidirectional Sync")
        print("=" * 60)

        # Download first (remote changes)
        print("\n📥 PHASE 1: Download from Drive")
        print("-" * 60)
        self.sync_from_drive()

        # Upload second (local changes)
        print("\n📤 PHASE 2: Upload to Drive")
        print("-" * 60)
        self.sync_to_drive()

        print("\n" + "=" * 60)
        print("✅ Full sync complete!")
        print("=" * 60)

if __name__ == "__main__":
    syncer = MCPDriveSync()
    syncer.bidirectional_sync()
```

**Save as**: `mcp_full_sync.py`

**Features**:
- ✅ Bidirectional sync
- ✅ Change detection (SHA256 hashing)
- ✅ Conflict resolution (last write wins)
- ✅ Metadata tracking
- ✅ Incremental sync (only changed files)

**Run**:
```bash
python mcp_full_sync.py
```

---

## 10. Recommended Architecture

### Architecture: Hybrid Local + Cloud

**Components**:

1. **Local Primary Storage**
   - Location: `~/.mcp-memory/`
   - Fast reads (5ms)
   - MCP Memory Extension writes here

2. **File Watcher Daemon**
   - Script: `mcp_auto_sync.py` (Example 4)
   - Runs in background
   - Detects file changes
   - Triggers async upload

3. **Google Drive Cloud Backup**
   - 30TB storage
   - Automatic backup
   - Multi-device access
   - Disaster recovery

4. **Periodic Full Sync** (Safety Net)
   - Cron job: Every 15 minutes
   - Script: `mcp-backup.sh` (Example 5)
   - Ensures consistency
   - Catches any missed changes

**Data Flow**:

```
┌─────────────────────────────────────────────────────┐
│                  MCP Memory Extension                │
│              (writes to local storage)               │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │   ~/.mcp-memory/            │
        │   vector_store.pkl (8KB)    │  ◄─── Fast reads (5ms)
        │   [Local Primary Storage]   │
        └─────────────┬───────────────┘
                      │
                      │ (File change detected)
                      │
                      ▼
        ┌─────────────────────────────┐
        │   File Watcher Daemon       │
        │   (mcp_auto_sync.py)        │
        │   [Background Process]      │
        └─────────────┬───────────────┘
                      │
                      │ (Async upload)
                      │
                      ▼
        ┌─────────────────────────────┐
        │   Google Drive API          │
        │   (PyDrive2)                │
        └─────────────┬───────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │   Google Drive              │
        │   30TB Storage              │
        │   [Cloud Backup]            │
        └─────────────────────────────┘
                      ▲
                      │
                      │ (Periodic sync - safety net)
                      │
        ┌─────────────┴───────────────┐
        │   Cron Job (15min)          │
        │   rclone sync               │
        └─────────────────────────────┘
```

**Benefits**:
- ✅ Fast local reads (5ms)
- ✅ Automatic cloud backup
- ✅ Minimal latency impact
- ✅ Disaster recovery
- ✅ Multi-device sync capability
- ✅ Zero marginal cost
- ✅ 30TB capacity (unlimited for practical purposes)

**Setup Steps**:

```bash
# 1. Install dependencies
pip install PyDrive2 watchdog
brew install rclone

# 2. Configure rclone
rclone config
# Name: gdrive
# Storage: drive

# 3. Set up file watcher daemon (runs in background)
python mcp_auto_sync.py &

# 4. Set up periodic sync (cron)
crontab -e
# Add: */15 * * * * $HOME/bin/mcp-backup.sh

# 5. Test
echo "test" > ~/.mcp-memory/test.txt
# Watch auto-upload happen
# Check Google Drive
```

---

## Quick Reference Commands

### rclone Commands

```bash
# Configure Google Drive
rclone config

# List remotes
rclone listremotes

# List files on Drive
rclone ls gdrive:

# One-time sync
rclone sync ~/.mcp-memory/ gdrive:mcp-memory/

# Mount Drive as filesystem
rclone mount gdrive: ~/GoogleDrive --daemon

# Check sync status
rclone check ~/.mcp-memory/ gdrive:mcp-memory/

# Copy specific file
rclone copy ~/.mcp-memory/vector_store.pkl gdrive:mcp-memory/
```

### PyDrive2 Quick Start

```python
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)

# Upload
file_drive = drive.CreateFile({'title': 'test.txt'})
file_drive.SetContentFile('test.txt')
file_drive.Upload()

# Download
file_drive.GetContentFile('downloaded.txt')
```

---

## Troubleshooting

### Issue: OAuth Scopes Missing

**Symptom**: `403: Insufficient Permission`

**Fix**:
```bash
# Delete old token
rm token.pickle
rm mycreds.txt

# Re-authenticate with correct scopes
# Will trigger browser OAuth flow
```

### Issue: Rate Limit Exceeded

**Symptom**: `403: User rate limit exceeded`

**Fix**: Add exponential backoff
```python
import time
import random

def upload_with_retry(file_path, max_retries=5):
    for attempt in range(max_retries):
        try:
            upload_file(file_path)
            return
        except Exception as e:
            if "rate limit" in str(e).lower():
                wait_time = (2 ** attempt) + random.random()
                print(f"⏳ Rate limited, waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                raise
```

### Issue: Slow rclone Mount

**Symptom**: 5-10 second latency for file access

**Fix**: Use `rclone copy` instead of mount for performance-critical operations

```bash
# Instead of mounting
# rclone mount gdrive: ~/GoogleDrive

# Use copy/sync
rclone sync ~/.mcp-memory/ gdrive:mcp-memory/
```

### Issue: Daily Upload Limit (750GB)

**Symptom**: Cannot upload after hitting 750GB in 24 hours

**Fix**:
1. Wait 24 hours for reset
2. Implement upload tracking
3. Prioritize critical files

```python
def check_daily_quota():
    """Track daily uploads to avoid hitting 750GB limit"""
    # Implement counter with 24-hour reset
    pass
```

---

## Next Steps

### Immediate Actions

1. **Set up rclone** (5 minutes)
   ```bash
   brew install rclone
   rclone config
   ```

2. **Test backup** (2 minutes)
   ```bash
   rclone sync ~/.mcp-memory/ gdrive:mcp-memory/
   ```

3. **Verify on Drive** (1 minute)
   - Go to [drive.google.com](https://drive.google.com)
   - Check for `mcp-memory/` folder
   - Verify `vector_store.pkl` is there

### Long-term Setup

4. **Implement auto-sync** (30 minutes)
   - Copy `mcp_auto_sync.py` (Example 4)
   - Install dependencies
   - Run as daemon

5. **Add cron backup** (5 minutes)
   - Copy `mcp-backup.sh` (Example 5)
   - Add to crontab
   - Test execution

6. **Monitor and optimize** (ongoing)
   - Check logs: `~/.mcp-backup.log`
   - Monitor Drive usage
   - Optimize sync frequency if needed

---

## Conclusion

You have **30TB of Google Drive storage** included with your Google AI Ultra subscription. This is more than enough for unlimited MCP Memory persistence at zero marginal cost.

**Best approach**:
1. Use **rclone** for simple automated backups (15-minute cron)
2. Optionally add **PyDrive2** file watcher for real-time sync
3. Keep local storage as primary for performance
4. Use Drive as cloud backup and multi-device sync

**Storage utilization**:
- Current MCP Memory: **8KB**
- Available storage: **30TB** (30,000,000,000 KB)
- **Usage**: 0.00000027%
- **Capacity**: Effectively unlimited

You can store **3.75 billion** copies of your current vector store before running out of space!

---

## Sources

### Documentation
- [Google AI Plans with Cloud Storage](https://one.google.com/about/google-ai-plans/)
- [What Gemini features you get with Google AI Pro and AI Ultra](https://9to5google.com/2025/12/24/google-ai-pro-ultra-features/)
- [Google Drive API Usage Limits](https://developers.google.com/workspace/drive/api/guides/limits)
- [Storage and Upload Limits](https://support.google.com/a/answer/172541?hl=en)
- [Choose Google Drive API Scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth)
- [Python Quickstart | Google Drive](https://developers.google.com/workspace/drive/api/quickstart/python)

### Tools & Libraries
- [PyDrive2 GitHub](https://github.com/iterative/PyDrive2)
- [PyDrive2 Documentation](https://docs.iterative.ai/PyDrive2/)
- [rclone Google Drive](https://rclone.org/drive/)
- [rclone GitHub](https://github.com/rclone/rclone)
- [google-api-python-client](https://thepythoncode.com/article/using-google-drive--api-in-python)

### MCP Memory Systems
- [MCP Memory Service](https://github.com/doobidoo/mcp-memory-service)
- [Memory-MCP](https://glama.ai/mcp/servers/@wb200/memory-mcp)
- [Memora](https://github.com/agentic-mcp-tools/memora)
- [MCP Memory LibSQL](https://github.com/joleyline/mcp-memory-libsql)
- [DRIVEUP: Incremental Backup](https://github.com/eblet/driveup)

### Performance & Benchmarks
- [rclone forum: Poor read speed from Google Drive](https://forum.rclone.org/t/poor-read-speed-from-google-drive/28847)
- [rclone forum: Increase performance and speed](https://forum.rclone.org/t/increase-performance-and-speed-on-google-drive-personal-drive/29998)
- [ChromaDB GitHub](https://github.com/chroma-core/chroma)
- [ChromaDB Backups](https://cookbook.chromadb.dev/strategies/backup/)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-31
**Author**: Claude Code (Sonnet 4.5)
**For**: alexandercpaul@gmail.com
