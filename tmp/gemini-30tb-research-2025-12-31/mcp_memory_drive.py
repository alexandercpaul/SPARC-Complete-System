#!/usr/bin/env python3
"""
MCP Memory Extension with Google Drive 30TB Storage Integration

Complete implementation for unlimited MCP Memory persistence using
Google AI Ultra subscription's 30TB Google Drive storage.

Author: Claude Code
Created: 2025-12-31
User: alexandercpaul@gmail.com

Usage:
    python mcp_memory_drive.py [command]

Commands:
    demo        - Run demonstration of all features
    backup      - Manually trigger backup to Google Drive
    restore     - Restore from latest backup
    list        - List all backups on Google Drive
    search      - Search memories
    monitor     - Start continuous monitoring and sync
"""

import os
import sys
import json
import time
import pickle
import shutil
import tempfile
import tarfile
import hashlib
import io
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Google Drive API
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: Missing Google API packages. Install with:")
    print("  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    sys.exit(1)

# ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("ERROR: Missing ChromaDB. Install with:")
    print("  pip install chromadb")
    sys.exit(1)

# Sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: Missing sentence-transformers. Install with:")
    print("  pip install sentence-transformers")
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/cloud-platform'
]

OAUTH_CREDS_PATH = os.path.expanduser('~/.gemini/oauth_creds.json')
TOKEN_PATH = os.path.expanduser('~/.gemini/drive_token.pickle')
CHROMA_DB_PATH = os.path.expanduser('~/.mcp_memory/chroma')
DRIVE_FOLDER_NAME = 'MCP_Memory_Backups'
BACKUP_STATE_FILE = os.path.expanduser('~/.mcp_memory/backup_state.json')

# Ensure directories exist
Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
Path(os.path.dirname(BACKUP_STATE_FILE)).mkdir(parents=True, exist_ok=True)


# ============================================================================
# GOOGLE DRIVE AUTHENTICATION
# ============================================================================

def get_drive_credentials() -> Credentials:
    """
    Get or refresh Google Drive API credentials

    Returns:
        Authenticated credentials object
    """
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_PATH):
        print(f"Loading existing credentials from {TOKEN_PATH}")
        with open(TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)

    # Refresh or authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("Starting OAuth2 authentication flow...")
            if not os.path.exists(OAUTH_CREDS_PATH):
                print(f"ERROR: OAuth credentials not found at {OAUTH_CREDS_PATH}")
                print("Please ensure you have valid OAuth2 credentials")
                sys.exit(1)

            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CREDS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for next run
        print(f"Saving credentials to {TOKEN_PATH}")
        with open(TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)

    return creds


def create_drive_service(creds: Credentials):
    """
    Create Google Drive API service

    Args:
        creds: Authenticated credentials

    Returns:
        Drive API service object
    """
    return build('drive', 'v3', credentials=creds)


# ============================================================================
# GOOGLE DRIVE OPERATIONS
# ============================================================================

def get_or_create_drive_folder(drive_service, folder_name: str) -> str:
    """
    Get or create folder on Google Drive

    Args:
        drive_service: Drive API service
        folder_name: Name of folder to create

    Returns:
        Folder ID
    """
    # Search for existing folder
    query = (
        f"name='{folder_name}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )

    results = drive_service.files().list(
        q=query,
        fields='files(id, name)'
    ).execute()

    folders = results.get('files', [])

    if folders:
        print(f"Found existing folder: {folder_name} (ID: {folders[0]['id']})")
        return folders[0]['id']

    # Create new folder
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }

    folder = drive_service.files().create(
        body=folder_metadata,
        fields='id'
    ).execute()

    print(f"Created new folder: {folder_name} (ID: {folder['id']})")
    return folder['id']


def upload_file_to_drive(
    drive_service,
    local_path: str,
    drive_folder_id: str,
    file_name: Optional[str] = None
) -> Dict:
    """
    Upload file to Google Drive with resumable upload

    Args:
        drive_service: Drive API service
        local_path: Path to local file
        drive_folder_id: Parent folder ID on Drive
        file_name: Optional custom file name

    Returns:
        File metadata dictionary
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"File not found: {local_path}")

    file_name = file_name or os.path.basename(local_path)

    # Determine MIME type
    if local_path.endswith('.tar.gz'):
        mime_type = 'application/gzip'
    elif local_path.endswith('.sqlite3'):
        mime_type = 'application/x-sqlite3'
    else:
        mime_type = 'application/octet-stream'

    file_metadata = {
        'name': file_name,
        'parents': [drive_folder_id]
    }

    # Use resumable upload for reliability
    media = MediaFileUpload(
        local_path,
        mimetype=mime_type,
        resumable=True,
        chunksize=256 * 1024 * 1024  # 256 MB chunks
    )

    print(f"Uploading {file_name} to Google Drive...")

    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, size, createdTime, webViewLink'
    ).execute()

    print(f"Upload complete: {file.get('name')}")
    print(f"  ID: {file.get('id')}")
    print(f"  Size: {int(file.get('size')) / 1024 / 1024:.2f} MB")
    print(f"  Link: {file.get('webViewLink')}")

    return file


def download_file_from_drive(
    drive_service,
    file_id: str,
    local_path: str
) -> None:
    """
    Download file from Google Drive

    Args:
        drive_service: Drive API service
        file_id: Google Drive file ID
        local_path: Where to save file locally
    """
    print(f"Downloading file ID {file_id}...")

    request = drive_service.files().get_media(fileId=file_id)

    with io.FileIO(local_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"  Download progress: {progress}%", end='\r')

    print(f"\nDownload complete: {local_path}")


def list_drive_files(
    drive_service,
    folder_id: str,
    name_contains: Optional[str] = None
) -> List[Dict]:
    """
    List files in Google Drive folder

    Args:
        drive_service: Drive API service
        folder_id: Folder ID to search
        name_contains: Optional name filter

    Returns:
        List of file metadata dictionaries
    """
    query = f"'{folder_id}' in parents and trashed=false"

    if name_contains:
        query += f" and name contains '{name_contains}'"

    results = drive_service.files().list(
        q=query,
        orderBy='createdTime desc',
        fields='files(id, name, size, createdTime, modifiedTime, webViewLink)'
    ).execute()

    return results.get('files', [])


def delete_drive_file(drive_service, file_id: str) -> None:
    """
    Delete file from Google Drive

    Args:
        drive_service: Drive API service
        file_id: File ID to delete
    """
    drive_service.files().delete(fileId=file_id).execute()
    print(f"Deleted file ID: {file_id}")


# ============================================================================
# CHROMADB OPERATIONS
# ============================================================================

class ChromaDBManager:
    """Manage ChromaDB with automatic Google Drive backup"""

    def __init__(
        self,
        persist_directory: str,
        drive_service,
        drive_folder_id: str,
        embedding_model: str = 'all-MiniLM-L6-v2'
    ):
        """
        Initialize ChromaDB manager

        Args:
            persist_directory: Local ChromaDB storage path
            drive_service: Google Drive API service
            drive_folder_id: Drive folder for backups
            embedding_model: Sentence transformer model name
        """
        self.persist_directory = persist_directory
        self.drive_service = drive_service
        self.drive_folder_id = drive_folder_id

        # Initialize ChromaDB client
        print(f"Initializing ChromaDB at {persist_directory}")
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedder = SentenceTransformer(embedding_model)

        # Get or create default collection
        self.collection = self.client.get_or_create_collection(
            name="mcp_memories",
            metadata={"description": "MCP Memory Extension with Drive backup"}
        )

        # Load backup state
        self.backup_state = self._load_backup_state()

        print("ChromaDB initialized successfully!")

    def _load_backup_state(self) -> Dict:
        """Load backup state from disk"""
        if os.path.exists(BACKUP_STATE_FILE):
            with open(BACKUP_STATE_FILE, 'r') as f:
                return json.load(f)
        return {'last_backup': None, 'last_backup_file_id': None}

    def _save_backup_state(self) -> None:
        """Save backup state to disk"""
        with open(BACKUP_STATE_FILE, 'w') as f:
            json.dump(self.backup_state, f, indent=2)

    def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory with automatic embedding

        Args:
            content: Memory content
            metadata: Optional metadata dictionary

        Returns:
            Memory ID
        """
        import uuid

        # Generate embedding
        embedding = self.embedder.encode(content).tolist()

        # Generate unique ID
        memory_id = str(uuid.uuid4())

        # Add to collection
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
        n_results: int = 5,
        metadata_filter: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Search memories using semantic similarity

        Args:
            query: Search query
            n_results: Number of results to return
            metadata_filter: Optional metadata filter

        Returns:
            List of memory dictionaries with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()

        # Build query parameters
        query_params = {
            'query_embeddings': [query_embedding],
            'n_results': n_results
        }

        if metadata_filter:
            query_params['where'] = metadata_filter

        # Query ChromaDB
        results = self.collection.query(**query_params)

        # Format results
        memories = []
        for i in range(len(results['documents'][0])):
            memories.append({
                'id': results['ids'][0][i],
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity': 1 - results['distances'][0][i],
                'distance': results['distances'][0][i]
            })

        return memories

    def get_memory_count(self) -> int:
        """Get total number of stored memories"""
        result = self.collection.count()
        return result

    def backup_to_drive(self, force: bool = False) -> Optional[str]:
        """
        Backup ChromaDB to Google Drive

        Args:
            force: Force backup even if recently backed up

        Returns:
            File ID of backup on Drive, or None if skipped
        """
        # Check if backup needed (don't backup more than once per hour)
        if not force and self.backup_state.get('last_backup'):
            last_backup_time = datetime.fromisoformat(
                self.backup_state['last_backup']
            )
            hours_since_backup = (
                datetime.now() - last_backup_time
            ).total_seconds() / 3600

            if hours_since_backup < 1:
                print(f"Skipping backup (last backup {hours_since_backup:.1f}h ago)")
                return None

        print("Creating ChromaDB backup...")

        # Create temporary archive
        with tempfile.NamedTemporaryFile(
            suffix='.tar.gz', delete=False
        ) as tmp:
            archive_path = tmp.name

        # Archive ChromaDB directory
        base_name = archive_path.replace('.tar.gz', '')
        shutil.make_archive(base_name, 'gztar', self.persist_directory)

        # Generate backup file name with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file_name = f'chromadb_backup_{timestamp}.tar.gz'

        try:
            # Upload to Google Drive
            file = upload_file_to_drive(
                self.drive_service,
                archive_path,
                self.drive_folder_id,
                backup_file_name
            )

            # Update backup state
            self.backup_state['last_backup'] = datetime.now().isoformat()
            self.backup_state['last_backup_file_id'] = file['id']
            self._save_backup_state()

            return file['id']

        finally:
            # Cleanup temporary file
            if os.path.exists(archive_path):
                os.remove(archive_path)

    def restore_from_drive(self, file_id: Optional[str] = None) -> None:
        """
        Restore ChromaDB from Google Drive backup

        Args:
            file_id: Specific file ID to restore, or latest if None
        """
        # Get latest backup if not specified
        if not file_id:
            backups = list_drive_files(
                self.drive_service,
                self.drive_folder_id,
                name_contains='chromadb_backup'
            )

            if not backups:
                raise ValueError("No backups found on Google Drive")

            file_id = backups[0]['id']
            print(f"Restoring from latest backup: {backups[0]['name']}")
        else:
            print(f"Restoring from file ID: {file_id}")

        # Create backup of current data before restoring
        current_backup_path = f"{self.persist_directory}_before_restore_{int(time.time())}"
        if os.path.exists(self.persist_directory):
            print(f"Backing up current data to: {current_backup_path}")
            shutil.copytree(self.persist_directory, current_backup_path)

        try:
            # Download backup
            with tempfile.NamedTemporaryFile(
                suffix='.tar.gz', delete=False
            ) as tmp:
                archive_path = tmp.name

            download_file_from_drive(
                self.drive_service,
                file_id,
                archive_path
            )

            # Remove current ChromaDB directory
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)

            # Extract backup
            print("Extracting backup...")
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(path=self.persist_directory)

            # Cleanup
            os.remove(archive_path)

            # Reinitialize ChromaDB client
            print("Reinitializing ChromaDB...")
            self.client = chromadb.PersistentClient(
                path=self.persist_directory
            )
            self.collection = self.client.get_or_create_collection(
                name="mcp_memories"
            )

            print("Restore complete!")

        except Exception as e:
            print(f"ERROR during restore: {e}")
            # Restore original data
            if os.path.exists(current_backup_path):
                print("Restoring original data...")
                if os.path.exists(self.persist_directory):
                    shutil.rmtree(self.persist_directory)
                shutil.copytree(current_backup_path, self.persist_directory)
            raise

    def list_backups(self) -> List[Dict]:
        """
        List all backups on Google Drive

        Returns:
            List of backup file metadata
        """
        backups = list_drive_files(
            self.drive_service,
            self.drive_folder_id,
            name_contains='chromadb_backup'
        )
        return backups

    def cleanup_old_backups(self, keep_count: int = 10) -> None:
        """
        Delete old backups, keeping only the most recent ones

        Args:
            keep_count: Number of recent backups to keep
        """
        backups = self.list_backups()

        if len(backups) <= keep_count:
            print(f"Only {len(backups)} backups found, nothing to clean up")
            return

        # Delete old backups
        for backup in backups[keep_count:]:
            print(f"Deleting old backup: {backup['name']}")
            delete_drive_file(self.drive_service, backup['id'])

        print(f"Cleanup complete. Kept {keep_count} most recent backups.")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class MCPMemoryDriveApp:
    """Main application for MCP Memory with Google Drive storage"""

    def __init__(self):
        """Initialize application"""
        print("=" * 70)
        print("MCP Memory Extension with 30TB Google Drive Storage")
        print("=" * 70)
        print()

        # Authenticate with Google Drive
        print("Step 1: Authenticating with Google Drive...")
        self.creds = get_drive_credentials()
        self.drive_service = create_drive_service(self.creds)
        print("  Authentication successful!")
        print()

        # Setup Drive folder
        print("Step 2: Setting up Google Drive folder...")
        self.drive_folder_id = get_or_create_drive_folder(
            self.drive_service,
            DRIVE_FOLDER_NAME
        )
        print()

        # Initialize ChromaDB
        print("Step 3: Initializing ChromaDB with Drive sync...")
        self.chroma_manager = ChromaDBManager(
            CHROMA_DB_PATH,
            self.drive_service,
            self.drive_folder_id
        )
        print()

        print("Initialization complete!")
        print(f"Local storage: {CHROMA_DB_PATH}")
        print(f"Drive folder ID: {self.drive_folder_id}")
        print(f"Current memories: {self.chroma_manager.get_memory_count()}")
        print()

    def demo(self):
        """Run demonstration of all features"""
        print("\n" + "=" * 70)
        print("DEMONSTRATION MODE")
        print("=" * 70)

        # Store some example memories
        print("\n--- Storing Example Memories ---")
        memories = [
            {
                "content": "Claude Code supports MCP (Model Context Protocol) for extending functionality",
                "metadata": {"category": "documentation", "importance": "high"}
            },
            {
                "content": "Google Drive API has a 750 GB daily upload limit per user account",
                "metadata": {"category": "api_limits", "source": "google_docs"}
            },
            {
                "content": "ChromaDB uses SQLite for persistent vector storage with efficient indexing",
                "metadata": {"category": "technical", "technology": "chromadb"}
            },
            {
                "content": "Sentence transformers can generate embeddings for semantic search",
                "metadata": {"category": "ml", "technology": "sentence-transformers"}
            },
            {
                "content": "The 30TB storage from Google AI Ultra enables unlimited MCP memory persistence",
                "metadata": {"category": "storage", "importance": "high"}
            }
        ]

        for mem in memories:
            memory_id = self.chroma_manager.store_memory(
                mem["content"],
                mem["metadata"]
            )
            print(f"  Stored: {mem['content'][:50]}...")

        print(f"\nTotal memories: {self.chroma_manager.get_memory_count()}")

        # Search memories
        print("\n--- Searching Memories ---")
        queries = [
            "How does Claude Code work with MCP?",
            "Storage limitations and quotas",
            "Vector database technology"
        ]

        for query in queries:
            print(f"\nQuery: {query}")
            results = self.chroma_manager.search_memories(query, n_results=2)

            for i, mem in enumerate(results, 1):
                print(f"  {i}. [Similarity: {mem['similarity']:.3f}]")
                print(f"     {mem['content'][:80]}...")
                print(f"     Metadata: {mem['metadata']}")

        # Backup to Drive
        print("\n--- Backing Up to Google Drive ---")
        file_id = self.chroma_manager.backup_to_drive(force=True)

        # List backups
        print("\n--- Available Backups on Google Drive ---")
        backups = self.chroma_manager.list_backups()

        for backup in backups:
            size_mb = int(backup.get('size', 0)) / 1024 / 1024
            print(f"\n  {backup['name']}")
            print(f"    Created: {backup.get('createdTime', 'unknown')}")
            print(f"    Size: {size_mb:.2f} MB")
            print(f"    ID: {backup['id']}")
            print(f"    Link: {backup.get('webViewLink', 'N/A')}")

        print("\n" + "=" * 70)
        print("DEMONSTRATION COMPLETE")
        print("=" * 70)

    def backup(self):
        """Manually trigger backup"""
        print("\n--- Manual Backup ---")
        file_id = self.chroma_manager.backup_to_drive(force=True)
        if file_id:
            print(f"\nBackup successful! File ID: {file_id}")
        else:
            print("\nBackup skipped (recent backup exists)")

    def restore(self):
        """Restore from latest backup"""
        print("\n--- Restore from Backup ---")
        backups = self.chroma_manager.list_backups()

        if not backups:
            print("No backups found on Google Drive")
            return

        print("\nAvailable backups:")
        for i, backup in enumerate(backups[:5], 1):
            size_mb = int(backup.get('size', 0)) / 1024 / 1024
            print(f"  {i}. {backup['name']} ({size_mb:.2f} MB)")

        choice = input("\nRestore from latest? (y/n): ")
        if choice.lower() == 'y':
            self.chroma_manager.restore_from_drive()
            print(f"\nRestored successfully!")
            print(f"Current memories: {self.chroma_manager.get_memory_count()}")

    def list_backups(self):
        """List all backups"""
        print("\n--- Backups on Google Drive ---")
        backups = self.chroma_manager.list_backups()

        if not backups:
            print("No backups found")
            return

        total_size = 0
        for i, backup in enumerate(backups, 1):
            size_mb = int(backup.get('size', 0)) / 1024 / 1024
            total_size += size_mb

            print(f"\n{i}. {backup['name']}")
            print(f"   Created: {backup.get('createdTime', 'unknown')}")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"   Link: {backup.get('webViewLink', 'N/A')}")

        print(f"\nTotal backups: {len(backups)}")
        print(f"Total size: {total_size:.2f} MB")

    def search(self):
        """Interactive search"""
        print("\n--- Search Memories ---")
        query = input("Enter search query: ")

        if not query:
            print("No query provided")
            return

        results = self.chroma_manager.search_memories(query, n_results=5)

        if not results:
            print("No results found")
            return

        print(f"\nFound {len(results)} results:")
        for i, mem in enumerate(results, 1):
            print(f"\n{i}. [Similarity: {mem['similarity']:.3f}]")
            print(f"   {mem['content']}")
            print(f"   Metadata: {mem['metadata']}")

    def monitor(self):
        """Start continuous monitoring and sync"""
        print("\n--- Monitoring Mode ---")
        print("Press Ctrl+C to stop")

        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for changes...")

                # Trigger backup if needed
                file_id = self.chroma_manager.backup_to_drive(force=False)

                if file_id:
                    print(f"  Backup created: {file_id}")
                else:
                    print("  No backup needed")

                # Wait 1 hour
                print("  Waiting 1 hour until next check...")
                time.sleep(3600)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def print_usage():
    """Print usage information"""
    print(__doc__)
    print("\nInstallation:")
    print("  pip install google-auth google-auth-oauthlib google-api-python-client")
    print("  pip install chromadb sentence-transformers")
    print()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        command = 'demo'
    else:
        command = sys.argv[1]

    if command == 'help' or command == '--help' or command == '-h':
        print_usage()
        return

    try:
        app = MCPMemoryDriveApp()

        if command == 'demo':
            app.demo()
        elif command == 'backup':
            app.backup()
        elif command == 'restore':
            app.restore()
        elif command == 'list':
            app.list_backups()
        elif command == 'search':
            app.search()
        elif command == 'monitor':
            app.monitor()
        else:
            print(f"Unknown command: {command}")
            print_usage()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
