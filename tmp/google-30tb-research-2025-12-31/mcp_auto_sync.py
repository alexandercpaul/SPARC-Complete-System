#!/usr/bin/env python3
"""
Watch MCP Memory directory and auto-upload changes to Google Drive

Features:
- Real-time file watching
- Automatic upload on change
- Background daemon mode
- Deduplication (no duplicate uploads)

Usage:
    pip install PyDrive2 watchdog
    python mcp_auto_sync.py
"""

import time
import os
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from datetime import datetime

MCP_MEMORY_PATH = os.path.expanduser("~/.mcp-memory/")

class MCPMemoryHandler(FileSystemEventHandler):
    def __init__(self, drive):
        self.drive = drive
        self.file_id_map = {}  # Local cache of file_path -> drive_file_id
        self.last_upload_time = {}  # Debounce multiple rapid changes
        self.debounce_seconds = 2  # Wait 2 seconds before uploading

        # Load existing files from Drive
        self._load_existing_files()

    def _load_existing_files(self):
        """Load existing files from Drive into cache"""
        print("🔍 Loading existing files from Google Drive...")
        try:
            query = "trashed=false"
            file_list = self.drive.ListFile({'q': query}).GetList()

            for file_drive in file_list:
                # Map filename to Drive ID
                filename = file_drive['title']
                self.file_id_map[filename] = file_drive['id']
                print(f"   Found: {filename} (ID: {file_drive['id']})")

            print(f"✅ Loaded {len(self.file_id_map)} file(s) from Drive")
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing files: {e}")

    def _should_upload(self, file_path):
        """Check if enough time has passed since last upload (debounce)"""
        now = time.time()
        last_upload = self.last_upload_time.get(file_path, 0)

        if now - last_upload < self.debounce_seconds:
            return False

        return True

    def on_modified(self, event):
        if event.is_directory:
            return

        # Skip metadata files
        if os.path.basename(event.src_path).startswith('.'):
            return

        print(f"\n📝 File changed: {event.src_path}")

        # Debounce rapid changes
        if not self._should_upload(event.src_path):
            print("   ⏭️  Skipping (debounce)")
            return

        self.upload_file(event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return

        # Skip metadata files
        if os.path.basename(event.src_path).startswith('.'):
            return

        print(f"\n🆕 New file: {event.src_path}")
        self.upload_file(event.src_path)

    def upload_file(self, file_path):
        """Upload or update file on Google Drive"""

        filename = os.path.basename(file_path)

        try:
            # Check if file already exists on Drive
            file_id = self.file_id_map.get(filename)

            if file_id:
                # Update existing file
                print(f"   📝 Updating existing file (ID: {file_id})")
                file_drive = self.drive.CreateFile({'id': file_id})
            else:
                # Create new file
                print(f"   🆕 Creating new file on Drive")
                file_drive = self.drive.CreateFile({
                    'title': filename,
                    'parents': [{'id': 'root'}]
                })

            # Upload content
            print(f"   ⏫ Uploading...")
            file_drive.SetContentFile(file_path)
            file_drive.Upload()

            # Cache file ID
            self.file_id_map[filename] = file_drive['id']

            # Update last upload time
            self.last_upload_time[file_path] = time.time()

            # Get file size
            file_size = os.path.getsize(file_path)

            print(f"   ✅ Uploaded {filename}")
            print(f"      ID: {file_drive['id']}")
            print(f"      Size: {file_size} bytes")
            print(f"      Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"   ❌ Upload failed: {e}")

def main():
    print("=" * 70)
    print("MCP Memory Auto-Sync Daemon")
    print("=" * 70)

    # Check if MCP memory directory exists
    if not os.path.exists(MCP_MEMORY_PATH):
        print(f"❌ Error: {MCP_MEMORY_PATH} does not exist")
        print("   Creating directory...")
        os.makedirs(MCP_MEMORY_PATH)

    # Authenticate with PyDrive2
    print("\n🔐 Authenticating with Google Drive...")
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")

    if gauth.credentials is None:
        print("   First time setup - browser will open")
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        print("   Refreshing expired credentials")
        gauth.Refresh()
    else:
        gauth.Authorize()

    gauth.SaveCredentialsFile("mycreds.txt")
    drive = GoogleDrive(gauth)

    print("✅ Authenticated successfully")

    # Set up file watcher
    print(f"\n👀 Watching directory: {MCP_MEMORY_PATH}")
    print("   Press Ctrl+C to stop\n")

    event_handler = MCPMemoryHandler(drive)
    observer = Observer()
    observer.schedule(event_handler, MCP_MEMORY_PATH, recursive=True)
    observer.start()

    print("-" * 70)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping auto-sync daemon...")
        observer.stop()

    observer.join()
    print("✅ Stopped")

if __name__ == "__main__":
    main()
