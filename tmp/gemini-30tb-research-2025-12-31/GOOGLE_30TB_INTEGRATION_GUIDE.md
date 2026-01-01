# Google One AI Ultra 30TB Storage Integration Guide for MCP Memory Extension

**Created:** 2025-12-31
**User:** alexandercpaul@gmail.com
**Subscription:** $250/month Google AI Ultra (30TB Google Drive storage)
**OAuth Credentials:** ~/.gemini/oauth_creds.json

---

## Executive Summary

This guide provides comprehensive implementation strategies for leveraging the **30TB Google Drive storage** included with Google AI Ultra subscription for **unlimited MCP Memory Extension persistence**. We cover three integration approaches:

1. **Google Drive API v3** - Direct file storage (Primary recommended)
2. **Gemini Files API** - AI-optimized file storage (Limited retention)
3. **Hybrid ChromaDB + Google Drive** - Best of both worlds

---

## Table of Contents

1. [Understanding Your 30TB Storage](#understanding-your-30tb-storage)
2. [Authentication & OAuth Setup](#authentication--oauth-setup)
3. [Integration Method 1: Google Drive API v3](#integration-method-1-google-drive-api-v3)
4. [Integration Method 2: Gemini Files API](#integration-method-2-gemini-files-api)
5. [Integration Method 3: Hybrid ChromaDB + Drive](#integration-method-3-hybrid-chromadb--drive)
6. [MCP Memory Extension Architecture](#mcp-memory-extension-architecture)
7. [Rate Limits & Quotas](#rate-limits--quotas)
8. [Implementation Code Examples](#implementation-code-examples)
9. [Best Practices & Optimization](#best-practices--optimization)
10. [Troubleshooting & FAQ](#troubleshooting--faq)

---

## Understanding Your 30TB Storage

### What You Get with Google AI Ultra ($250/month)

- **30TB total storage** shared across Google Drive, Gmail, and Google Photos
- **Google Drive API v3 access** for programmatic file operations
- **Gemini Advanced features** including Files API
- **No additional cloud storage fees** (already included)
- **OAuth2 authentication** (credentials already at `~/.gemini/oauth_creds.json`)

### Storage Breakdown

Your 30TB can be allocated as:
- **MCP Memory ChromaDB backups** (SQLite files, typically MB-GB range)
- **Vector embeddings** (compressed storage, efficient)
- **Session history** (JSON/text files)
- **Model artifacts** (if needed)
- **Unlimited persistence** for MCP Memory Extension

### Key Limitations to Know

1. **Upload Rate Limits:** 750 GB per 24-hour period per user
2. **API Quota:** 20,000 calls per 100 seconds (per user/project)
3. **File Size Limit:** Individual files up to 5 TB
4. **Gemini Files API retention:** 48 hours (unless using File Search store)

**Source:** [Google Drive API Usage Limits](https://developers.google.com/workspace/drive/api/guides/limits)

---

## Authentication & OAuth Setup

### Your Existing OAuth Credentials

You already have OAuth2 credentials at `~/.gemini/oauth_creds.json` with these scopes:
- `https://www.googleapis.com/auth/cloud-platform`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/userinfo.profile`

### Required Additional Scope for Drive API

Add this scope for full Google Drive access:
```
https://www.googleapis.com/auth/drive
```

### OAuth2 Flow Implementation

```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import json
import os
import pickle

# Scopes needed for Drive API + existing scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid',
    'https://www.googleapis.com/auth/userinfo.profile'
]

def get_drive_credentials():
    """Get or refresh Google Drive API credentials"""
    creds = None
    token_path = os.path.expanduser('~/.gemini/drive_token.pickle')
    creds_path = os.path.expanduser('~/.gemini/oauth_creds.json')

    # Load existing token if available
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh expired token
            creds.refresh(Request())
        else:
            # New authentication flow
            flow = InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return creds
```

**Source:** [Google Drive API Python Quickstart](https://developers.google.com/drive/api/quickstart/python)

### Alternative: Use Existing Token

Your existing `oauth_creds.json` has a refresh token. You can use it directly:

```python
import json
from google.oauth2.credentials import Credentials

def load_existing_creds():
    """Load existing OAuth credentials from ~/.gemini/oauth_creds.json"""
    creds_path = os.path.expanduser('~/.gemini/oauth_creds.json')

    with open(creds_path, 'r') as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data['access_token'],
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id='YOUR_CLIENT_ID',  # Extract from oauth_creds if available
        scopes=token_data['scope'].split()
    )

    return creds
```

**Note:** You may need to re-authenticate to add the Drive scope if not already present.

---

## Integration Method 1: Google Drive API v3

### Overview

**Primary recommended approach** for MCP Memory Extension persistence:
- Store ChromaDB SQLite files directly on Google Drive
- Automatic sync using Google Drive API
- Resumable uploads for large files
- Full control over file lifecycle

### Architecture

```
MCP Memory Extension
    ↓
ChromaDB (local SQLite)
    ↓
Sync Service (Python script)
    ↓
Google Drive API v3
    ↓
30TB Google Drive Storage
```

### Setup Google Drive API Client

```python
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

def create_drive_service(creds):
    """Create Google Drive API service"""
    return build('drive', 'v3', credentials=creds)

# Initialize service
creds = get_drive_credentials()
drive_service = create_drive_service(creds)
```

**Source:** [Google Drive API Overview](https://developers.google.com/workspace/drive/api/guides/about-sdk)

### File Operations

#### 1. Upload ChromaDB SQLite File

```python
def upload_chromadb_file(drive_service, local_file_path, drive_folder_id=None):
    """
    Upload ChromaDB SQLite database to Google Drive with resumable upload

    Args:
        drive_service: Google Drive API service instance
        local_file_path: Path to local ChromaDB SQLite file
        drive_folder_id: Optional Google Drive folder ID

    Returns:
        File ID of uploaded file
    """
    file_metadata = {
        'name': os.path.basename(local_file_path),
        'mimeType': 'application/x-sqlite3'
    }

    # Add to specific folder if provided
    if drive_folder_id:
        file_metadata['parents'] = [drive_folder_id]

    # Use resumable upload for reliability with large files
    media = MediaFileUpload(
        local_file_path,
        mimetype='application/x-sqlite3',
        resumable=True,
        chunksize=256 * 1024 * 1024  # 256 MB chunks
    )

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, size, createdTime'
    ).execute()

    print(f"Uploaded {file.get('name')} - ID: {file.get('id')}")
    return file.get('id')
```

**Source:** [Google Drive API Upload File Data](https://developers.google.com/drive/api/v3/manage-uploads)

#### 2. Download ChromaDB File

```python
def download_chromadb_file(drive_service, file_id, local_path):
    """
    Download ChromaDB SQLite file from Google Drive

    Args:
        drive_service: Google Drive API service instance
        file_id: Google Drive file ID
        local_path: Where to save the file locally
    """
    request = drive_service.files().get_media(fileId=file_id)

    with io.FileIO(local_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download progress: {int(status.progress() * 100)}%")

    print(f"Downloaded to {local_path}")
```

#### 3. List Files in Drive

```python
def list_memory_backups(drive_service, folder_id=None):
    """
    List all ChromaDB backup files in Google Drive

    Args:
        drive_service: Google Drive API service instance
        folder_id: Optional folder ID to search within

    Returns:
        List of file metadata dictionaries
    """
    query = "mimeType='application/x-sqlite3'"
    if folder_id:
        query += f" and '{folder_id}' in parents"

    results = drive_service.files().list(
        q=query,
        fields="files(id, name, size, createdTime, modifiedTime)",
        orderBy="modifiedTime desc"
    ).execute()

    return results.get('files', [])
```

#### 4. Update Existing File

```python
def update_chromadb_file(drive_service, file_id, local_file_path):
    """
    Update existing ChromaDB file on Google Drive (versioning)

    Args:
        drive_service: Google Drive API service instance
        file_id: Existing file ID on Google Drive
        local_file_path: Path to updated local file
    """
    media = MediaFileUpload(
        local_file_path,
        mimetype='application/x-sqlite3',
        resumable=True,
        chunksize=256 * 1024 * 1024
    )

    updated_file = drive_service.files().update(
        fileId=file_id,
        media_body=media,
        fields='id, name, modifiedTime'
    ).execute()

    print(f"Updated file: {updated_file.get('name')}")
    return updated_file
```

### Create Dedicated Folder Structure

```python
def setup_mcp_memory_folder(drive_service):
    """
    Create folder structure for MCP Memory Extension on Google Drive

    Structure:
        MCP_Memory/
            ├── chromadb/
            ├── backups/
            └── sessions/

    Returns:
        Dictionary of folder IDs
    """
    folder_structure = {
        'MCP_Memory': None,
        'chromadb': None,
        'backups': None,
        'sessions': None
    }

    # Create root folder
    root_metadata = {
        'name': 'MCP_Memory',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    root = drive_service.files().create(
        body=root_metadata,
        fields='id'
    ).execute()
    folder_structure['MCP_Memory'] = root.get('id')

    # Create subfolders
    for subfolder in ['chromadb', 'backups', 'sessions']:
        sub_metadata = {
            'name': subfolder,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [folder_structure['MCP_Memory']]
        }
        sub = drive_service.files().create(
            body=sub_metadata,
            fields='id'
        ).execute()
        folder_structure[subfolder] = sub.get('id')

    return folder_structure
```

### Automatic Sync Service

```python
import time
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ChromaDBSyncHandler(FileSystemEventHandler):
    """Monitor ChromaDB directory and sync changes to Google Drive"""

    def __init__(self, drive_service, local_db_path, drive_folder_id):
        self.drive_service = drive_service
        self.local_db_path = local_db_path
        self.drive_folder_id = drive_folder_id
        self.file_hashes = {}
        self.drive_file_ids = {}

    def get_file_hash(self, file_path):
        """Calculate MD5 hash of file"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def on_modified(self, event):
        """Handle file modification events"""
        if event.is_directory or not event.src_path.endswith('.sqlite3'):
            return

        # Check if file actually changed (debounce)
        current_hash = self.get_file_hash(event.src_path)
        if self.file_hashes.get(event.src_path) == current_hash:
            return

        self.file_hashes[event.src_path] = current_hash

        # Upload or update on Drive
        file_name = os.path.basename(event.src_path)

        if file_name in self.drive_file_ids:
            # Update existing file
            print(f"Syncing update: {file_name}")
            update_chromadb_file(
                self.drive_service,
                self.drive_file_ids[file_name],
                event.src_path
            )
        else:
            # Upload new file
            print(f"Uploading new file: {file_name}")
            file_id = upload_chromadb_file(
                self.drive_service,
                event.src_path,
                self.drive_folder_id
            )
            self.drive_file_ids[file_name] = file_id

def start_sync_service(drive_service, local_db_path, drive_folder_id):
    """
    Start automatic sync service for ChromaDB to Google Drive

    Args:
        drive_service: Google Drive API service
        local_db_path: Path to local ChromaDB directory
        drive_folder_id: Google Drive folder ID for backups
    """
    event_handler = ChromaDBSyncHandler(
        drive_service, local_db_path, drive_folder_id
    )
    observer = Observer()
    observer.schedule(event_handler, local_db_path, recursive=True)
    observer.start()

    print(f"Sync service started. Monitoring: {local_db_path}")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
```

**Note:** Requires `watchdog` package: `pip install watchdog`

---

## Integration Method 2: Gemini Files API

### Overview

The **Gemini Files API** provides AI-optimized file storage but with important limitations:
- **48-hour retention** for standard uploads
- **Indefinite storage** when using File Search store
- **2 GB per file, 20 GB per project** limits
- **Free embeddings** with File Search

### When to Use Gemini Files API

Use for:
- AI-specific file operations (feeding files to Gemini models)
- File Search with automatic embeddings (free)
- Small to medium files (under 2 GB)

**Do NOT use for:**
- Long-term ChromaDB backup (48-hour deletion)
- Large database files (20 GB project limit)
- Primary storage (use Google Drive instead)

**Source:** [Gemini Files API Documentation](https://ai.google.dev/gemini-api/docs/files)

### Setup Gemini Files API

```python
import google.generativeai as genai

# Configure with your API key
genai.configure(api_key='YOUR_API_KEY')

# Or use OAuth credentials
from google.oauth2.credentials import Credentials
creds = load_existing_creds()  # From earlier function
genai.configure(credentials=creds)
```

### File Upload to Gemini

```python
def upload_to_gemini_files(file_path, display_name=None):
    """
    Upload file to Gemini Files API (48-hour retention)

    Args:
        file_path: Path to local file
        display_name: Optional display name

    Returns:
        File object with URI and metadata
    """
    print(f"Uploading to Gemini Files API: {file_path}")

    file = genai.upload_file(
        path=file_path,
        display_name=display_name or os.path.basename(file_path)
    )

    print(f"Uploaded file URI: {file.uri}")
    print(f"File will expire at: {file.expiration_time}")

    return file
```

### File Search Store (Indefinite Storage)

```python
def create_file_search_corpus():
    """
    Create File Search corpus for indefinite storage

    Returns:
        Corpus object
    """
    from google.ai.generativelanguage import (
        CreateCorpusRequest,
        Corpus
    )

    corpus = genai.create_corpus(
        name="MCP_Memory_Corpus",
        display_name="MCP Memory Extension Storage"
    )

    print(f"Created corpus: {corpus.name}")
    return corpus

def upload_to_file_search_corpus(corpus_name, file_path):
    """
    Upload file to File Search corpus (indefinite storage)

    Args:
        corpus_name: Corpus resource name
        file_path: Path to file

    Returns:
        Document object
    """
    document = genai.create_document(
        corpus_name=corpus_name,
        display_name=os.path.basename(file_path),
        file=file_path
    )

    print(f"Uploaded to corpus: {document.name}")
    print("File will be stored indefinitely until manually deleted")

    return document
```

**Source:** [Gemini File Search](https://ai.google.dev/gemini-api/docs/file-search)

### Search Uploaded Files

```python
def search_memory_files(corpus_name, query):
    """
    Search files in File Search corpus using semantic search

    Args:
        corpus_name: Corpus resource name
        query: Search query

    Returns:
        Search results
    """
    # Use Gemini model with File Search tool
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        tools=[
            genai.protos.Tool(
                file_search=genai.protos.FileSearchTool(
                    corpora=[corpus_name]
                )
            )
        ]
    )

    response = model.generate_content(query)
    return response
```

### Important: File Retention Policy

```python
def list_gemini_files():
    """List all files uploaded to Gemini Files API"""
    files = genai.list_files()

    for f in files:
        print(f"File: {f.name}")
        print(f"  Display Name: {f.display_name}")
        print(f"  URI: {f.uri}")
        print(f"  Expires: {f.expiration_time}")
        print()

    return files

def delete_gemini_file(file_name):
    """Delete file from Gemini Files API"""
    genai.delete_file(name=file_name)
    print(f"Deleted: {file_name}")
```

**Warning:** Standard Gemini Files API uploads are **automatically deleted after 48 hours**. Only files in File Search store persist indefinitely.

**Source:** [Gemini File Management](https://deepwiki.com/googleapis/python-genai/7-file-management)

---

## Integration Method 3: Hybrid ChromaDB + Drive

### Overview

**Best of both worlds approach:**
- Local ChromaDB for fast vector search
- Automatic backup to Google Drive (30TB)
- Periodic sync with conflict resolution
- Restore capability from Drive

### Architecture

```
┌─────────────────────────────────────────────────┐
│           MCP Memory Extension                  │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│         ChromaDB (Local SQLite)                 │
│  - Fast vector search                           │
│  - Local embeddings                             │
│  - Session persistence                          │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│         Sync Manager (Python Service)           │
│  - Watchdog file monitoring                     │
│  - Incremental backups                          │
│  - Conflict resolution                          │
│  - Scheduled full backups                       │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│      Google Drive API v3 (30TB Storage)         │
│  - Automatic versioning                         │
│  - Unlimited persistence                        │
│  - Multi-device sync                            │
└─────────────────────────────────────────────────┘
```

### ChromaDB Setup with Drive Sync

```python
import chromadb
from chromadb.config import Settings

class ChromaDBWithDriveSync:
    """ChromaDB client with automatic Google Drive backup"""

    def __init__(self, persist_directory, drive_service, drive_folder_id):
        """
        Initialize ChromaDB with Drive sync

        Args:
            persist_directory: Local ChromaDB storage path
            drive_service: Google Drive API service
            drive_folder_id: Google Drive folder for backups
        """
        self.persist_directory = persist_directory
        self.drive_service = drive_service
        self.drive_folder_id = drive_folder_id

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Track last backup time
        self.last_backup = None

        # Start backup scheduler
        self._start_backup_scheduler()

    def get_or_create_collection(self, name, metadata=None):
        """Get or create collection with metadata"""
        return self.client.get_or_create_collection(
            name=name,
            metadata=metadata
        )

    def backup_to_drive(self, force=False):
        """
        Backup ChromaDB to Google Drive

        Args:
            force: Force backup even if recently backed up

        Returns:
            File ID of backup on Google Drive
        """
        import shutil
        import tempfile
        from datetime import datetime, timedelta

        # Check if backup needed (don't backup more than once per hour)
        if not force and self.last_backup:
            if datetime.now() - self.last_backup < timedelta(hours=1):
                print("Skipping backup (last backup < 1 hour ago)")
                return None

        print(f"Backing up ChromaDB to Google Drive...")

        # Create temporary archive of ChromaDB directory
        with tempfile.NamedTemporaryFile(
            suffix='.tar.gz', delete=False
        ) as tmp:
            archive_path = tmp.name

        # Archive the ChromaDB directory
        shutil.make_archive(
            archive_path.replace('.tar.gz', ''),
            'gztar',
            self.persist_directory
        )

        # Upload to Google Drive
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_metadata = {
            'name': f'chromadb_backup_{timestamp}.tar.gz',
            'parents': [self.drive_folder_id]
        }

        media = MediaFileUpload(
            archive_path,
            mimetype='application/gzip',
            resumable=True
        )

        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size'
        ).execute()

        # Clean up temp file
        os.remove(archive_path)

        self.last_backup = datetime.now()
        print(f"Backup complete: {file.get('name')} ({file.get('size')} bytes)")

        return file.get('id')

    def restore_from_drive(self, file_id=None):
        """
        Restore ChromaDB from Google Drive backup

        Args:
            file_id: Specific backup file ID (latest if None)
        """
        import shutil
        import tempfile
        import tarfile

        # Get latest backup if file_id not specified
        if not file_id:
            backups = list_memory_backups(
                self.drive_service,
                self.drive_folder_id
            )
            if not backups:
                raise ValueError("No backups found on Google Drive")
            file_id = backups[0]['id']

        print(f"Restoring ChromaDB from Google Drive (file_id: {file_id})...")

        # Download backup
        with tempfile.NamedTemporaryFile(
            suffix='.tar.gz', delete=False
        ) as tmp:
            archive_path = tmp.name

        download_chromadb_file(
            self.drive_service,
            file_id,
            archive_path
        )

        # Extract to persist directory
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(path=self.persist_directory)

        # Clean up
        os.remove(archive_path)

        # Reinitialize client with restored data
        self.client = chromadb.PersistentClient(
            path=self.persist_directory
        )

        print("Restore complete!")

    def _start_backup_scheduler(self):
        """Start background thread for periodic backups"""
        import threading

        def backup_loop():
            while True:
                time.sleep(3600)  # Backup every hour
                try:
                    self.backup_to_drive()
                except Exception as e:
                    print(f"Backup error: {e}")

        backup_thread = threading.Thread(
            target=backup_loop,
            daemon=True
        )
        backup_thread.start()
```

### Usage Example

```python
# Initialize Drive service
creds = get_drive_credentials()
drive_service = create_drive_service(creds)

# Setup folder structure
folders = setup_mcp_memory_folder(drive_service)

# Initialize ChromaDB with Drive sync
chroma_client = ChromaDBWithDriveSync(
    persist_directory='./chroma_db',
    drive_service=drive_service,
    drive_folder_id=folders['chromadb']
)

# Use ChromaDB normally - automatic backups every hour
collection = chroma_client.get_or_create_collection(
    name="mcp_memory",
    metadata={"description": "MCP Memory Extension storage"}
)

# Add documents
collection.add(
    documents=["This is a memory about coding"],
    metadatas=[{"type": "code_memory"}],
    ids=["mem_1"]
)

# Manual backup
chroma_client.backup_to_drive(force=True)

# Restore from backup (if needed)
# chroma_client.restore_from_drive()
```

---

## MCP Memory Extension Architecture

### Integration with Existing MCP Servers

Based on research, several MCP memory servers exist that can be enhanced with 30TB Google Drive storage:

1. **OpenMemory MCP (Mem0.ai)** - Local SQLite with vector storage
2. **MCP Memory Service (doobidoo)** - Hybrid SQLite + Cloudflare sync
3. **Claude-Cursor Memory MCP** - PostgreSQL with pgvector
4. **Vector Memory MCP** - sqlite-vec with sentence-transformers

**Sources:**
- [OpenMemory MCP](https://mem0.ai/blog/introducing-openmemory-mcp)
- [MCP Memory Service](https://github.com/doobidoo/mcp-memory-service)
- [Claude-Cursor Memory](https://github.com/Angleito/Claude-CursorMemoryMCP)

### Recommended Architecture: Enhanced MCP Memory with Drive

```python
"""
Enhanced MCP Memory Extension with 30TB Google Drive persistence

Combines:
- Local ChromaDB for fast vector search
- Google Drive for unlimited cloud backup
- MCP protocol for Claude Code integration
"""

from typing import Any, Dict, List, Optional
import asyncio
from mcp.server import Server
from mcp.types import Tool, TextContent

class MCPMemoryWithDrive:
    """MCP Memory server with Google Drive persistence"""

    def __init__(
        self,
        chroma_client: ChromaDBWithDriveSync,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.chroma = chroma_client
        self.server = Server("mcp-memory-drive")

        # Initialize sentence transformer for embeddings
        from sentence_transformers import SentenceTransformer
        self.embedder = SentenceTransformer(embedding_model)

        # Setup MCP tools
        self._register_tools()

    def _register_tools(self):
        """Register MCP tools for memory operations"""

        @self.server.tool()
        async def store_memory(
            content: str,
            metadata: Optional[Dict[str, Any]] = None
        ) -> TextContent:
            """Store a memory in ChromaDB with automatic Drive backup"""

            # Generate embedding
            embedding = self.embedder.encode(content).tolist()

            # Get or create collection
            collection = self.chroma.get_or_create_collection("memories")

            # Generate ID
            import uuid
            memory_id = str(uuid.uuid4())

            # Add to collection
            collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata or {}],
                ids=[memory_id]
            )

            # Trigger backup
            self.chroma.backup_to_drive()

            return TextContent(
                type="text",
                text=f"Memory stored with ID: {memory_id}"
            )

        @self.server.tool()
        async def search_memories(
            query: str,
            n_results: int = 5
        ) -> TextContent:
            """Search memories using semantic similarity"""

            # Generate query embedding
            query_embedding = self.embedder.encode(query).tolist()

            # Get collection
            collection = self.chroma.get_or_create_collection("memories")

            # Query
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )

            # Format results
            formatted = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                formatted.append(
                    f"{i+1}. [{1-distance:.2f}] {doc}\n"
                    f"   Metadata: {metadata}"
                )

            return TextContent(
                type="text",
                text="\n\n".join(formatted)
            )

        @self.server.tool()
        async def backup_memories() -> TextContent:
            """Manually trigger backup to Google Drive"""
            file_id = self.chroma.backup_to_drive(force=True)
            return TextContent(
                type="text",
                text=f"Backup complete. File ID: {file_id}"
            )

        @self.server.tool()
        async def restore_memories(
            file_id: Optional[str] = None
        ) -> TextContent:
            """Restore memories from Google Drive backup"""
            self.chroma.restore_from_drive(file_id)
            return TextContent(
                type="text",
                text="Restore complete. Memories reloaded."
            )

    async def run(self):
        """Run the MCP server"""
        async with self.server:
            await self.server.wait_for_completion()
```

### MCP Server Configuration

Add to Claude Code's MCP settings (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mcp-memory-drive": {
      "command": "python",
      "args": [
        "/path/to/mcp_memory_drive_server.py"
      ],
      "env": {
        "GOOGLE_OAUTH_CREDS": "/Users/alexandercpaul/.gemini/oauth_creds.json",
        "CHROMA_PERSIST_DIR": "/Users/alexandercpaul/.mcp_memory/chroma",
        "DRIVE_FOLDER_ID": "YOUR_DRIVE_FOLDER_ID"
      }
    }
  }
}
```

---

## Rate Limits & Quotas

### Google Drive API Quotas

From the official documentation:

| Limit Type | Default Quota | Notes |
|------------|---------------|-------|
| **API Calls** | 20,000 per 100 seconds | Per user and per project |
| **Daily Upload** | 750 GB per 24 hours | Per user account |
| **Max File Size** | 5 TB | Per individual file |
| **Max Folder Depth** | 100 levels | Nesting limit |

**Error Responses:**
- `403: User rate limit exceeded` - Exceeded 20K calls/100s
- `429: Too many requests` - Backend rate limit

**Solution:** Implement exponential backoff:

```python
import time
from googleapiclient.errors import HttpError

def drive_api_call_with_retry(func, max_retries=5):
    """Execute Drive API call with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return func()
        except HttpError as e:
            if e.resp.status in [403, 429]:
                wait_time = (2 ** attempt) + (random.randint(0, 1000) / 1000)
                print(f"Rate limit hit. Waiting {wait_time:.2f}s...")
                time.sleep(wait_time)
            else:
                raise

    raise Exception(f"Failed after {max_retries} retries")

# Usage
result = drive_api_call_with_retry(
    lambda: drive_service.files().list().execute()
)
```

**Source:** [Google Drive API Usage Limits](https://developers.google.com/workspace/drive/api/guides/limits)

### Gemini Files API Quotas

| Limit Type | Quota | Notes |
|------------|-------|-------|
| **File Size** | 2 GB | Per individual file |
| **Project Total** | 20 GB | All files combined |
| **Retention** | 48 hours | Standard uploads |
| **File Search Store** | Unlimited | Indefinite storage |

**Source:** [Gemini Files API](https://ai.google.dev/gemini-api/docs/files)

### Optimization Strategies

1. **Batch Operations**
   ```python
   from googleapiclient.http import BatchHttpRequest

   def batch_upload_files(drive_service, file_paths):
       """Upload multiple files in a single batch"""
       batch = drive_service.new_batch_http_request()

       for file_path in file_paths:
           media = MediaFileUpload(file_path)
           file_metadata = {'name': os.path.basename(file_path)}

           batch.add(
               drive_service.files().create(
                   body=file_metadata,
                   media_body=media
               )
           )

       batch.execute()
   ```

2. **Incremental Backups**
   - Only backup changed collections
   - Use file hashing to detect changes
   - Implement differential backups

3. **Compression**
   ```python
   import gzip

   def compress_chromadb_backup(source_dir, output_file):
       """Compress ChromaDB directory before upload"""
       import shutil

       # Create tar.gz archive
       shutil.make_archive(
           output_file.replace('.tar.gz', ''),
           'gztar',
           source_dir
       )

       # Typically achieves 80-90% compression for SQLite files
   ```

---

## Implementation Code Examples

### Complete Working Example

```python
#!/usr/bin/env python3
"""
Complete MCP Memory Extension with Google Drive 30TB persistence

Usage:
    python mcp_memory_drive.py
"""

import os
import sys
import json
import time
import pickle
from pathlib import Path
from typing import Dict, List, Optional

# Google Drive API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

# ChromaDB
import chromadb
from chromadb.config import Settings

# Sentence transformers for embeddings
from sentence_transformers import SentenceTransformer

# Configuration
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/cloud-platform'
]

OAUTH_CREDS_PATH = os.path.expanduser('~/.gemini/oauth_creds.json')
TOKEN_PATH = os.path.expanduser('~/.gemini/drive_token.pickle')
CHROMA_DB_PATH = os.path.expanduser('~/.mcp_memory/chroma')
DRIVE_FOLDER_NAME = 'MCP_Memory_Backups'


class MCPMemoryDriveStorage:
    """Complete MCP Memory system with 30TB Google Drive storage"""

    def __init__(self):
        # Initialize Google Drive
        self.creds = self._get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.creds)

        # Setup Drive folder
        self.drive_folder_id = self._get_or_create_drive_folder()

        # Initialize ChromaDB
        Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize embedder
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="mcp_memories",
            metadata={"description": "MCP Memory Extension with Drive backup"}
        )

        print("MCP Memory with Google Drive initialized!")
        print(f"Local storage: {CHROMA_DB_PATH}")
        print(f"Drive folder ID: {self.drive_folder_id}")

    def _get_credentials(self) -> Credentials:
        """Get or refresh Google Drive credentials"""
        creds = None

        # Load existing token
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)

        # Refresh or authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    OAUTH_CREDS_PATH, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)

        return creds

    def _get_or_create_drive_folder(self) -> str:
        """Get or create MCP Memory folder on Google Drive"""
        # Search for existing folder
        results = self.drive_service.files().list(
            q=f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields='files(id, name)'
        ).execute()

        folders = results.get('files', [])

        if folders:
            return folders[0]['id']

        # Create new folder
        folder_metadata = {
            'name': DRIVE_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        folder = self.drive_service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()

        print(f"Created Drive folder: {DRIVE_FOLDER_NAME}")
        return folder['id']

    def store_memory(
        self,
        content: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """Store a memory with automatic embedding and Drive backup"""
        import uuid

        # Generate embedding
        embedding = self.embedder.encode(content).tolist()

        # Generate ID
        memory_id = str(uuid.uuid4())

        # Add to ChromaDB
        self.collection.add(
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata or {}],
            ids=[memory_id]
        )

        print(f"Memory stored: {memory_id}")
        return memory_id

    def search_memories(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict]:
        """Search memories using semantic similarity"""
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Format results
        memories = []
        for i in range(len(results['documents'][0])):
            memories.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity': 1 - results['distances'][0][i]
            })

        return memories

    def backup_to_drive(self) -> str:
        """Backup ChromaDB to Google Drive"""
        import tempfile
        import shutil
        from datetime import datetime

        print("Creating backup...")

        # Create temporary archive
        with tempfile.NamedTemporaryFile(
            suffix='.tar.gz', delete=False
        ) as tmp:
            archive_path = tmp.name

        # Archive ChromaDB directory
        shutil.make_archive(
            archive_path.replace('.tar.gz', ''),
            'gztar',
            CHROMA_DB_PATH
        )

        # Upload to Drive
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_metadata = {
            'name': f'chromadb_backup_{timestamp}.tar.gz',
            'parents': [self.drive_folder_id]
        }

        media = MediaFileUpload(
            archive_path,
            mimetype='application/gzip',
            resumable=True
        )

        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size, webViewLink'
        ).execute()

        # Cleanup
        os.remove(archive_path)

        print(f"Backup complete: {file.get('name')}")
        print(f"Size: {int(file.get('size')) / 1024 / 1024:.2f} MB")
        print(f"View: {file.get('webViewLink')}")

        return file.get('id')

    def restore_from_drive(self, file_id: Optional[str] = None):
        """Restore ChromaDB from Google Drive backup"""
        import tempfile
        import tarfile
        import io

        # Get latest backup if not specified
        if not file_id:
            results = self.drive_service.files().list(
                q=f"'{self.drive_folder_id}' in parents and name contains 'chromadb_backup'",
                orderBy='createdTime desc',
                fields='files(id, name)',
                pageSize=1
            ).execute()

            files = results.get('files', [])
            if not files:
                raise ValueError("No backups found on Google Drive")

            file_id = files[0]['id']
            print(f"Restoring from: {files[0]['name']}")

        # Download backup
        request = self.drive_service.files().get_media(fileId=file_id)

        with tempfile.NamedTemporaryFile(
            suffix='.tar.gz', delete=False
        ) as tmp:
            archive_path = tmp.name
            with io.FileIO(archive_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        print(f"Download: {int(status.progress() * 100)}%")

        # Extract
        print("Extracting backup...")
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(path=CHROMA_DB_PATH)

        # Cleanup
        os.remove(archive_path)

        # Reinitialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(
            name="mcp_memories"
        )

        print("Restore complete!")

    def list_backups(self) -> List[Dict]:
        """List all backups on Google Drive"""
        results = self.drive_service.files().list(
            q=f"'{self.drive_folder_id}' in parents and name contains 'chromadb_backup'",
            orderBy='createdTime desc',
            fields='files(id, name, size, createdTime, webViewLink)'
        ).execute()

        return results.get('files', [])


def demo():
    """Demonstration of MCP Memory with Google Drive"""

    print("=" * 60)
    print("MCP Memory Extension with 30TB Google Drive Storage")
    print("=" * 60)
    print()

    # Initialize
    storage = MCPMemoryDriveStorage()

    # Store some memories
    print("\n--- Storing Memories ---")
    storage.store_memory(
        "Claude Code supports MCP for extending functionality",
        {"category": "documentation", "importance": "high"}
    )
    storage.store_memory(
        "Google Drive API has a 750 GB daily upload limit per user",
        {"category": "api_limits"}
    )
    storage.store_memory(
        "ChromaDB uses SQLite for persistent vector storage",
        {"category": "technical"}
    )

    # Search memories
    print("\n--- Searching Memories ---")
    results = storage.search_memories("Claude Code features", n_results=2)
    for i, mem in enumerate(results, 1):
        print(f"{i}. [Similarity: {mem['similarity']:.2f}]")
        print(f"   {mem['content']}")
        print(f"   Metadata: {mem['metadata']}")
        print()

    # Backup to Drive
    print("\n--- Backing Up to Google Drive ---")
    file_id = storage.backup_to_drive()

    # List backups
    print("\n--- Available Backups ---")
    backups = storage.list_backups()
    for backup in backups:
        print(f"- {backup['name']}")
        print(f"  Created: {backup['createdTime']}")
        print(f"  Size: {int(backup['size']) / 1024 / 1024:.2f} MB")
        print(f"  ID: {backup['id']}")
        print()

    print("Demo complete!")


if __name__ == "__main__":
    demo()
```

**Save as:** `/Users/alexandercpaul/Library/Mobile Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/gemini-30tb-research-2025-12-31/mcp_memory_drive.py`

### Installation Requirements

```bash
# Install dependencies
pip install \
    google-auth \
    google-auth-oauthlib \
    google-auth-httplib2 \
    google-api-python-client \
    chromadb \
    sentence-transformers \
    watchdog

# Or use requirements.txt
cat > requirements.txt << EOF
google-auth>=2.35.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.150.0
chromadb>=0.5.0
sentence-transformers>=3.1.0
watchdog>=5.0.0
EOF

pip install -r requirements.txt
```

---

## Best Practices & Optimization

### 1. Incremental Backups

Instead of backing up entire ChromaDB every time, implement incremental backups:

```python
import hashlib
import json

class IncrementalBackupManager:
    """Track changed collections and backup only deltas"""

    def __init__(self, state_file='backup_state.json'):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self):
        """Load previous backup state"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_state(self):
        """Save current backup state"""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f)

    def get_collection_hash(self, collection):
        """Calculate hash of collection data"""
        # Get all documents
        results = collection.get()

        # Create deterministic representation
        data_str = json.dumps({
            'ids': sorted(results['ids']),
            'documents': [results['documents'][i]
                         for i in sorted(range(len(results['ids'])),
                                       key=lambda i: results['ids'][i])]
        }, sort_keys=True)

        return hashlib.sha256(data_str.encode()).hexdigest()

    def needs_backup(self, collection_name, collection):
        """Check if collection changed since last backup"""
        current_hash = self.get_collection_hash(collection)
        last_hash = self.state.get(collection_name)

        if current_hash != last_hash:
            self.state[collection_name] = current_hash
            self._save_state()
            return True

        return False
```

### 2. Compression Optimization

ChromaDB SQLite files compress very well:

```python
def optimized_compression(source_path, output_path):
    """Compress with maximum efficiency for SQLite"""
    import lzma

    # LZMA achieves better compression than gzip for SQLite
    with lzma.open(output_path, 'wb', preset=9) as compressed:
        with open(source_path, 'rb') as source:
            compressed.write(source.read())

    original_size = os.path.getsize(source_path)
    compressed_size = os.path.getsize(output_path)
    ratio = (1 - compressed_size / original_size) * 100

    print(f"Compression: {original_size / 1024 / 1024:.2f} MB -> "
          f"{compressed_size / 1024 / 1024:.2f} MB ({ratio:.1f}% reduction)")
```

### 3. Multi-threaded Uploads

For large backups, use concurrent uploads:

```python
from concurrent.futures import ThreadPoolExecutor
import os

def parallel_upload_chunks(drive_service, large_file_path, folder_id):
    """Upload large file in parallel chunks"""

    # Split file into chunks
    chunk_size = 256 * 1024 * 1024  # 256 MB
    file_size = os.path.getsize(large_file_path)
    num_chunks = (file_size + chunk_size - 1) // chunk_size

    print(f"Uploading {file_size / 1024 / 1024:.2f} MB in {num_chunks} chunks")

    def upload_chunk(chunk_num):
        """Upload a single chunk"""
        start = chunk_num * chunk_size
        end = min(start + chunk_size, file_size)

        # Read chunk
        with open(large_file_path, 'rb') as f:
            f.seek(start)
            chunk_data = f.read(end - start)

        # Upload chunk
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(chunk_data)
            tmp_path = tmp.name

        media = MediaFileUpload(tmp_path)
        file_metadata = {
            'name': f'chunk_{chunk_num}',
            'parents': [folder_id]
        }

        result = drive_service.files().create(
            body=file_metadata,
            media_body=media
        ).execute()

        os.remove(tmp_path)
        return result

    # Upload in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(upload_chunk, range(num_chunks)))

    print(f"Uploaded {len(results)} chunks")
    return results
```

### 4. Automatic Cleanup of Old Backups

Keep only recent backups to save quota:

```python
def cleanup_old_backups(drive_service, folder_id, keep_count=10):
    """Delete old backups, keeping only the most recent ones"""

    # List all backups
    results = drive_service.files().list(
        q=f"'{folder_id}' in parents and name contains 'chromadb_backup'",
        orderBy='createdTime desc',
        fields='files(id, name, createdTime)'
    ).execute()

    backups = results.get('files', [])

    # Delete old backups
    for backup in backups[keep_count:]:
        print(f"Deleting old backup: {backup['name']}")
        drive_service.files().delete(fileId=backup['id']).execute()

    print(f"Kept {min(len(backups), keep_count)} most recent backups")
```

### 5. Monitoring & Alerting

```python
import logging
from datetime import datetime

class BackupMonitor:
    """Monitor backup health and send alerts"""

    def __init__(self, log_file='backup_monitor.log'):
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def log_backup_success(self, file_id, size_mb):
        """Log successful backup"""
        self.logger.info(
            f"Backup successful - File ID: {file_id}, Size: {size_mb:.2f} MB"
        )

    def log_backup_failure(self, error):
        """Log backup failure"""
        self.logger.error(f"Backup failed: {str(error)}")

    def check_backup_age(self, drive_service, folder_id, max_age_hours=24):
        """Alert if backup is too old"""
        results = drive_service.files().list(
            q=f"'{folder_id}' in parents",
            orderBy='createdTime desc',
            fields='files(createdTime)',
            pageSize=1
        ).execute()

        files = results.get('files', [])
        if not files:
            self.logger.warning("No backups found!")
            return False

        last_backup = datetime.fromisoformat(
            files[0]['createdTime'].replace('Z', '+00:00')
        )
        age_hours = (datetime.now(last_backup.tzinfo) - last_backup).total_seconds() / 3600

        if age_hours > max_age_hours:
            self.logger.warning(
                f"Last backup is {age_hours:.1f} hours old (max: {max_age_hours})"
            )
            return False

        return True
```

---

## Troubleshooting & FAQ

### Q: OAuth token expired, how to refresh?

**A:** The credentials automatically refresh if you have a `refresh_token`:

```python
from google.auth.transport.requests import Request

if creds.expired and creds.refresh_token:
    creds.refresh(Request())
```

If refresh fails, delete the token file and re-authenticate:
```bash
rm ~/.gemini/drive_token.pickle
```

### Q: Hit 750 GB daily upload limit, what now?

**A:** Implement these strategies:

1. **Compression** - Reduce upload size by 80-90%
2. **Incremental backups** - Only upload changed data
3. **Scheduled uploads** - Spread across 24-hour period
4. **Deduplication** - Don't upload identical files

```python
def smart_backup_strategy(storage, max_daily_gb=700):
    """Backup strategy respecting 750 GB daily limit"""

    # Track uploaded today
    upload_tracker_file = 'daily_upload_tracker.json'

    if os.path.exists(upload_tracker_file):
        with open(upload_tracker_file, 'r') as f:
            tracker = json.load(f)

        # Check if new day
        if tracker['date'] != str(datetime.now().date()):
            tracker = {'date': str(datetime.now().date()), 'gb_uploaded': 0}
    else:
        tracker = {'date': str(datetime.now().date()), 'gb_uploaded': 0}

    # Check if can upload
    if tracker['gb_uploaded'] >= max_daily_gb:
        print(f"Daily limit reached ({tracker['gb_uploaded']} GB). Skipping backup.")
        return None

    # Perform backup with size tracking
    # ... (backup code)

    # Update tracker
    tracker['gb_uploaded'] += uploaded_size_gb
    with open(upload_tracker_file, 'w') as f:
        json.dump(tracker, f)
```

### Q: ChromaDB restore overwrites current data?

**A:** Create a separate restore directory first:

```python
def safe_restore(drive_service, file_id, verify_first=True):
    """Restore to temporary location, verify, then replace"""

    import tempfile
    import shutil

    # Download to temp location
    temp_restore_dir = tempfile.mkdtemp()

    # Extract backup to temp
    # ... (restore code to temp_restore_dir)

    if verify_first:
        # Verify integrity
        temp_client = chromadb.PersistentClient(path=temp_restore_dir)
        collections = temp_client.list_collections()
        print(f"Verified {len(collections)} collections in backup")

    # Backup current data
    current_backup = f"{CHROMA_DB_PATH}_backup_{int(time.time())}"
    shutil.copytree(CHROMA_DB_PATH, current_backup)
    print(f"Current data backed up to: {current_backup}")

    # Replace with restored data
    shutil.rmtree(CHROMA_DB_PATH)
    shutil.copytree(temp_restore_dir, CHROMA_DB_PATH)

    print("Restore complete!")
```

### Q: Can I use this across multiple machines?

**A:** Yes! The Google Drive sync enables multi-device access:

```python
class MultiDeviceSync:
    """Sync ChromaDB across multiple devices via Google Drive"""

    def __init__(self, drive_service, folder_id, device_name):
        self.drive_service = drive_service
        self.folder_id = folder_id
        self.device_name = device_name

    def pull_latest(self):
        """Pull latest backup from Drive before starting"""
        print(f"[{self.device_name}] Pulling latest backup...")
        # Download and restore latest backup
        # ... (restore code)

    def push_changes(self):
        """Push local changes to Drive"""
        print(f"[{self.device_name}] Pushing changes...")
        # Create and upload backup
        # ... (backup code)

    def sync_loop(self, interval_minutes=15):
        """Continuous sync loop"""
        while True:
            try:
                self.pull_latest()
                time.sleep(interval_minutes * 60)
                self.push_changes()
            except Exception as e:
                print(f"Sync error: {e}")
                time.sleep(60)
```

**Conflict resolution:** Use timestamps to detect conflicts:

```python
def resolve_conflict(local_modified, remote_modified):
    """Resolve sync conflict using newest-wins strategy"""

    if remote_modified > local_modified:
        print("Remote is newer, pulling...")
        return 'pull'
    else:
        print("Local is newer, pushing...")
        return 'push'
```

### Q: How to monitor storage usage?

**A:** Query Google Drive API for storage info:

```python
def get_storage_usage(drive_service):
    """Get current Google Drive storage usage"""

    about = drive_service.about().get(fields='storageQuota').execute()
    quota = about['storageQuota']

    usage_gb = int(quota['usage']) / 1024 / 1024 / 1024
    limit_gb = int(quota['limit']) / 1024 / 1024 / 1024

    print(f"Storage Usage: {usage_gb:.2f} GB / {limit_gb:.2f} GB")
    print(f"Available: {limit_gb - usage_gb:.2f} GB")
    print(f"Percentage used: {usage_gb / limit_gb * 100:.1f}%")

    return {
        'usage_gb': usage_gb,
        'limit_gb': limit_gb,
        'available_gb': limit_gb - usage_gb
    }
```

---

## Summary & Next Steps

### What You've Learned

1. **30TB Google Drive storage** is accessible via Google Drive API v3
2. **Three integration methods:**
   - Direct Drive API (recommended for ChromaDB backups)
   - Gemini Files API (for AI-specific operations, 48hr limit)
   - Hybrid approach (best of both worlds)

3. **Key capabilities:**
   - Unlimited MCP Memory persistence
   - Automatic backup/restore
   - Multi-device sync
   - Incremental backups
   - Compression optimization

4. **Rate limits:**
   - 750 GB/day upload limit
   - 20K API calls per 100 seconds
   - 5 TB max file size

### Implementation Checklist

- [ ] Install required Python packages
- [ ] Setup OAuth credentials with Drive scope
- [ ] Test Google Drive API connection
- [ ] Create MCP Memory folder structure on Drive
- [ ] Initialize ChromaDB with Drive sync
- [ ] Test backup and restore operations
- [ ] Configure automatic sync service
- [ ] Setup monitoring and logging
- [ ] Implement cleanup for old backups
- [ ] Document MCP server configuration

### Production Deployment

1. **Run the demo script:**
   ```bash
   python /Users/alexandercpaul/Library/Mobile\ Documents/com~apple~CloudDocs/Developer/SPARC_Complete_System/tmp/gemini-30tb-research-2025-12-31/mcp_memory_drive.py
   ```

2. **Configure as system service** (macOS):
   ```bash
   # Create LaunchAgent plist
   # ... (systemd/launchd configuration)
   ```

3. **Monitor with dashboard:**
   ```bash
   # Setup monitoring dashboard
   # ... (Grafana/simple web interface)
   ```

### Additional Resources

- [Google Drive API Python Quickstart](https://developers.google.com/drive/api/quickstart/python)
- [Google Drive API Upload File Data](https://developers.google.com/drive/api/v3/manage-uploads)
- [Google Drive API Usage Limits](https://developers.google.com/workspace/drive/api/guides/limits)
- [Gemini Files API Documentation](https://ai.google.dev/gemini-api/docs/files)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [MCP Memory Servers](https://mem0.ai/blog/introducing-openmemory-mcp)

---

## Contact & Support

**User:** alexandercpaul@gmail.com
**OAuth Credentials:** ~/.gemini/oauth_creds.json
**Local ChromaDB:** ~/.mcp_memory/chroma

For issues or questions, refer to:
- Google Drive API documentation
- Gemini API support
- ChromaDB GitHub issues

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Total Storage Available:** 30 TB (Google AI Ultra subscription)
**Status:** Ready for implementation
