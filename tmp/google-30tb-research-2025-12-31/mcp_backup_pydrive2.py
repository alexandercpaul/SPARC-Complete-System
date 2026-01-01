#!/usr/bin/env python3
"""
Basic MCP Memory backup to Google Drive using PyDrive2

Usage:
    pip install PyDrive2
    python mcp_backup_pydrive2.py
"""

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
import sys

# Authenticate
gauth = GoogleAuth()

# Try to load saved credentials
gauth.LoadCredentialsFile("mycreds.txt")

if gauth.credentials is None:
    # Authenticate if credentials don't exist
    print("🔐 First time setup - authenticating with Google Drive...")
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    # Refresh credentials if expired
    print("🔄 Refreshing expired credentials...")
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

    if not os.path.exists(mcp_memory_path):
        print(f"❌ Error: {mcp_memory_path} not found")
        sys.exit(1)

    # Check if file already exists on Drive
    query = "title='vector_store.pkl' and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()

    if file_list:
        # Update existing file
        file_drive = file_list[0]
        print(f"📝 Updating existing file (ID: {file_drive['id']})")
    else:
        # Create new file
        file_drive = drive.CreateFile({
            'title': 'vector_store.pkl',
            'parents': [{'id': 'root'}]  # Upload to root, or specify folder ID
        })
        print("🆕 Creating new file on Google Drive")

    # Set content
    file_drive.SetContentFile(mcp_memory_path)

    # Upload
    print("⏫ Uploading...")
    file_drive.Upload()

    # Get file size
    file_size = os.path.getsize(mcp_memory_path)

    print(f"✅ Uploaded {mcp_memory_path} to Google Drive")
    print(f"   File ID: {file_drive['id']}")
    print(f"   Size: {file_size} bytes")
    return file_drive['id']

def download_mcp_memory(file_id):
    """Download vector_store.pkl from Google Drive"""

    file_drive = drive.CreateFile({'id': file_id})

    download_path = os.path.expanduser("~/.mcp-memory/vector_store_downloaded.pkl")

    print(f"⏬ Downloading file ID: {file_id}")
    file_drive.GetContentFile(download_path)

    print(f"✅ Downloaded to {download_path}")

def list_drive_files():
    """List all MCP memory files on Google Drive"""

    query = "title contains 'vector_store' and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()

    print(f"\n📁 Found {len(file_list)} file(s) on Google Drive:")
    for file_drive in file_list:
        print(f"   - {file_drive['title']} (ID: {file_drive['id']})")
        print(f"     Modified: {file_drive['modifiedDate']}")

if __name__ == "__main__":
    print("=" * 60)
    print("MCP Memory → Google Drive Backup (PyDrive2)")
    print("=" * 60)

    # List existing files
    list_drive_files()

    # Upload
    print("\n" + "-" * 60)
    file_id = upload_mcp_memory()

    print("\n" + "=" * 60)
    print("✅ Backup complete!")
    print("=" * 60)

    # Optionally download (for testing)
    # download_mcp_memory(file_id)
